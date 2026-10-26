"""Lambda handler: input {'image_base64':'...'} -> base64 annotated image + report.
Deploy with a Lambda container image containing OpenCV 5. Do NOT expose publicly.
"""
import base64
from analyzer import analyze_image


def lambda_handler(event, context):
    try:
        payload = event.get('image_base64')
        if not isinstance(payload, str):
            return {'statusCode': 400, 'body': {'error': 'image_base64 string is required'}}
        raw = base64.b64decode(payload, validate=True)
        report, annotated = analyze_image(raw)
        return {'statusCode': 200, 'body': {'report': report, 'annotated_base64': base64.b64encode(annotated).decode('ascii')}}
    except Exception as exc:
        return {'statusCode': 400, 'body': {'error': str(exc)}}
