"""Optional second-stage contextual interpretation. Not a calibrated defect classifier."""
import io
import json
import re
import boto3
import os
from botocore.config import Config
from PIL import Image

MODEL_ID = 'amazon.nova-lite-v1:0'

PROMPT = """You are a cautious visual-triage assistant evaluating a photograph of consumer batteries. This is NOT a safety diagnosis. Interpret the complete image, including terminals, adjacent surfaces, pouch/casing geometry, and normal manufacturing features.

Evaluate separately:
A. Powder-like deposits near terminals or on surrounding surfaces (possibly unrelated dirt).
B. Corrosion-like buildup or discoloration (not normal copper/colored wrapping).
C. Visible tears, punctures, or casing damage (not seams, printing, ordinary creases).
D. Clear abnormal bulging, lifted components, or deformation (not wrinkles alone). Distinguish a visibly bulging pouch from visible powder; do not describe powder that is not there.
E. Image clarity and whether a closer view is needed.

Never conclude that a battery is safe. Do not infer chemistry unless clearly printed. Do not assume yellow insulation, QR codes, labels, reflections, printed letters, battery caps, ordinary wrinkles, or background texture are defects. Never invent debris, residue or other observations. For uncertain evidence, say what is visible and express uncertainty; with no supported evidence use an empty findings array. Do not ask people to touch, rotate, move, charge, puncture, or handle a possibly damaged battery. Follow-up requests may only suggest using existing safely obtained photographs or professional inspection.

Return ONLY one JSON object with keys exactly as shown in this example (substitute real observations). A category MUST be ONE string from the allowed set, NEVER the entire list of alternatives:
{
 "battery_form": "uncertain",
 "findings": [
   {"category": "possible_deformation", "evidence": "The pouch visibly bulges upward relative to its surrounding mounting surface", "location": "center-left", "certainty": "possible"}
 ],
 "normal_features": [],
 "needs_followup": true,
 "followup_photo": "Professional review or an existing safely captured side view, if available",
 "overall": "possible_visual_issue",
 "limitations": "A photograph cannot confirm damage or safety."
}

Allowed battery_form values: pouch, cylindrical, other, uncertain.
Allowed finding category values: residue, corrosion_like, casing_damage, possible_deformation, other.
Allowed certainty values: possible, uncertain. Never use confirmed.
Allowed overall values: possible_visual_issue, no_obvious_visual_issue, insufficient_evidence.
Use category other only for a distinct visible issue outside the defined categories. Every finding needs SPECIFIC visual evidence and location. If the image is blurry or small enough to preclude interpretation, use insufficient_evidence. If no obvious findings, use findings [] and no_obvious_visual_issue (not safe)."""


VALID_CATEGORIES = {'residue', 'corrosion_like', 'casing_damage', 'possible_deformation', 'other'}
VALID_FORMS = {'pouch', 'cylindrical', 'other', 'uncertain'}
VALID_OVERALL = {'possible_visual_issue', 'no_obvious_visual_issue', 'insufficient_evidence'}


def normalize_assessment(data):
    """Validate model-generated JSON without treating unsupported text as a confirmed defect."""
    if not isinstance(data, dict) or not isinstance(data.get('findings'), list):
        raise ValueError('Unexpected model response schema')
    clean = []
    for finding in data['findings'][:12]:
        if not isinstance(finding, dict):
            continue
        category = finding.get('category')
        evidence = finding.get('evidence')
        location = finding.get('location')
        # Never let a pipe-delimited list of possible categories appear as a real classification.
        # Preserve observations under 'other' only when they have independently stated evidence.
        if not isinstance(evidence, str) or len(evidence.strip()) < 10 or not isinstance(location, str) or not location.strip():
            continue
        if category not in VALID_CATEGORIES:
            category = 'other'
        certainty = finding.get('certainty')
        if certainty not in {'possible', 'uncertain'}:
            certainty = 'uncertain'
        clean.append({'category': category, 'evidence': evidence.strip()[:500],
                      'location': location.strip()[:160], 'certainty': certainty})
    data['findings'] = clean
    if data.get('battery_form') not in VALID_FORMS:
        data['battery_form'] = 'uncertain'
    overall = data.get('overall')
    if overall not in VALID_OVERALL:
        overall = 'possible_visual_issue' if clean else 'insufficient_evidence'
    if clean and overall == 'no_obvious_visual_issue':
        overall = 'possible_visual_issue'
    if not clean and overall == 'possible_visual_issue':
        overall = 'insufficient_evidence'
    data['overall'] = overall
    data['needs_followup'] = bool(data.get('needs_followup', False))
    data['followup_photo'] = str(data.get('followup_photo') or '')[:350]
    data['normal_features'] = [str(v)[:180] for v in data.get('normal_features', []) if isinstance(v, str)][:12] if isinstance(data.get('normal_features'), list) else []
    data['limitations'] = str(data.get('limitations') or 'Visual triage cannot determine battery safety.')[:400]
    return data


def analyze_context(image_bytes: bytes, profile=None, region=None, model_id=MODEL_ID):
    region = region or os.getenv(
        "BATTERYGUARD_AWS_REGION", "us-east-2"
    )

    profile = profile or os.getenv(
        "BATTERYGUARD_AWS_PROFILE"
    )
    
    im = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    im.thumbnail((1280, 1280))
    b = io.BytesIO()
    im.save(b, format='JPEG', quality=84)
    session = boto3.Session(profile_name=profile, region_name=region)
    client = session.client('bedrock-runtime', config=Config(connect_timeout=10, read_timeout=100, retries={'max_attempts': 1}))
    response = client.converse(
        modelId=model_id,
        messages=[{'role':'user','content':[
            {'image':{'format':'jpeg','source':{'bytes':b.getvalue()}}},
            {'text':PROMPT}
        ]}],
        inferenceConfig={'maxTokens':850,'temperature':0}
    )
    message = '\n'.join(x.get('text','') for x in response['output']['message']['content'])
    match = re.search(r'\{.*\}', message, re.S)
    if not match:
        raise ValueError('Model did not return structured JSON: ' + message[:400])
    data = json.loads(match.group())
    data = normalize_assessment(data)

    data['model_id'] = model_id
    data['disclaimer'] = 'Unvalidated visual model interpretation, not a safety assessment or a confirmed defect diagnosis.'
    return data
