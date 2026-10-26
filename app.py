import json
import streamlit as st
from analyzer import analyze_image
from aws_client import analyze_in_aws
from bedrock_vision import analyze_context

st.set_page_config(page_title='BatteryGuard Vision', page_icon='🔋', layout='wide')
st.title('🔋 BatteryGuard Vision')
st.caption('Evidence-aware visual triage prototype | OpenCV 5')
st.warning('Not a battery safety certification. Do not touch, charge, open, move, or test a suspicious battery for this demo. Use photos already taken safely.')
mode = st.radio('Processing location', ['AWS Lambda + Bedrock Vision (experimental)', 'AWS Lambda', 'Local OpenCV'], horizontal=True)
if mode.startswith('AWS'):
    st.info('Cloud processing uses AWS Lambda (OpenCV 5). AI-assisted visual analysis uses Amazon Bedrock Nova Lite. AWS permissions and usage charges may apply.')
photo = st.file_uploader('Upload a JPEG or PNG battery photograph', type=['jpg', 'jpeg', 'png'])
if photo:
    try:
        raw = photo.getvalue()
        with st.spinner('Analyzing image...'):
            result, annotated = analyze_in_aws(raw) if mode.startswith('AWS') else analyze_image(raw)
            vision = None
            vision_error = None
            if 'Bedrock' in mode:
                try:
                    vision = analyze_context(raw)
                except Exception as err:
                    vision_error = str(err)
        st.success('Processed by ' + ('AWS Lambda' if mode.startswith('AWS') else 'local OpenCV'))
        c1, c2 = st.columns(2)
        with c1:
            st.image(raw, caption='Original', use_container_width=True)
        with c2:
            st.image(annotated, caption='Color (orange), surface-line (blue) and pale residue (magenta) candidates — not confirmed defects', use_container_width=True)
        st.subheader('Inspection triage')
        if 'Bedrock' in mode:
            st.subheader('Contextual vision assessment — experimental')
            if vision_error:
                st.error('Bedrock vision unavailable: ' + vision_error)
                st.info('The Lambda / OpenCV findings below remain available. Bedrock may require model access and bedrock:InvokeModel permission.')
            elif vision is not None:
                st.warning('Model interpretation is unvalidated. Do not treat as a diagnosis or a safe-to-handle decision.')
                st.write('**Assessment:**', vision.get('overall','uncertain').replace('_',' '))
                if vision.get('findings'):
                    for item in vision['findings']:
                        st.write(f"**{item.get('category', 'observation')}** — {item.get('evidence', '')} (location: {item.get('location', 'unspecified')}; certainty: {item.get('certainty', 'uncertain')})")
                else:
                    st.write('No specific visually supported finding reported by model.')
                st.write('**Next evidence:**', vision.get('followup_photo') or 'None requested')
                with st.expander('Structured contextual-model output'):
                    st.json(vision)
                st.download_button('Download contextual assessment JSON', json.dumps(vision, indent=2), 'batteryguard-context.json', 'application/json')
        st.metric('Status', result['status'].replace('_', ' ').title())
        st.write(result['recommendation'])
        for warning in result['quality']['warnings']:
            st.warning(warning)
        st.write(f"**Color candidates:** {len(result['regions'])} · **Line-mark candidates:** {len(result.get('surface_line_candidates', []))} · **Pale residue candidates:** {len(result.get('residue_candidates', []))} · **Blur variance:** {result['quality']['blur_variance']} · **OpenCV:** {result['opencv_version']}")
        with st.expander('Inspection evidence and limitations'):
            st.json(result)
        st.download_button('Download annotated image', annotated, 'batteryguard-annotated.jpg', 'image/jpeg')
        st.download_button('Download report JSON', json.dumps(result, indent=2), 'batteryguard-report.json', 'application/json')
    except Exception as exc:
        st.error(f'Inspection failed: {exc}')
        if mode.startswith('AWS'):
            st.info('Check the batteryguard AWS profile, Lambda invoke permission, and region. Switch to Local OpenCV to troubleshoot without AWS.')
