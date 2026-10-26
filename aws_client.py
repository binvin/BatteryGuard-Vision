"""Invoke the private BatteryGuard Vision Lambda using a named AWS CLI profile."""
import base64
import json
import os


def analyze_in_aws(image_bytes: bytes):
    import boto3
    from botocore.config import Config

    # Lambda synchronous invocation payload maximum is 6 MB, including base64 overhead.
    if len(image_bytes) > 3 * 1024 * 1024:
        raise ValueError('AWS mode accepts images up to 3 MB. Export a smaller JPEG first.')
    profile = os.environ.get('BATTERYGUARD_AWS_PROFILE') or None
    region = os.environ.get('BATTERYGUARD_AWS_REGION', 'us-east-2')
    function = os.environ.get('BATTERYGUARD_LAMBDA_FUNCTION', 'batteryguard-vision-api')
    session = boto3.Session(profile_name=profile, region_name=region)
    client = session.client('lambda', config=Config(connect_timeout=10, read_timeout=90, retries={'max_attempts': 2}))
    payload = {'image_base64': base64.b64encode(image_bytes).decode('ascii')}
    response = client.invoke(FunctionName=function, InvocationType='RequestResponse', Payload=json.dumps(payload).encode())
    raw = response['Payload'].read()
    output = json.loads(raw)
    if response.get('FunctionError'):
        raise RuntimeError('Lambda execution error: ' + str(output)[:600])
    if output.get('statusCode') != 200:
        body = output.get('body', {})
        raise RuntimeError('Lambda rejected image: ' + str(body.get('error', body))[:600])
    body = output['body']
    if isinstance(body, str):
        body = json.loads(body)
    return body['report'], base64.b64decode(body['annotated_base64'], validate=True)
