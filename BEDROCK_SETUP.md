# Optional contextual vision pilot (Amazon Bedrock)

This is a **separate, opt-in** second-stage model call from local Streamlit. The existing cloud Lambda/OpenCV 5 image analysis is unchanged. No Docker rebuild or ECR upload needed.

## Amazon Bedrock Setup

1. Configure AWS credentials using an AWS CLI profile, IAM role, IAM Identity Center, or another supported boto3 credential provider. Set `BATTERYGUARD_AWS_PROFILE` only if using a named profile.

2. Set `BATTERYGUARD_AWS_REGION` to a region supporting Amazon Nova Lite (tested with `us-east-2`).

3. Open the [Amazon Bedrock Console](https://us-east-2.console.aws.amazon.com/bedrock/home?region=us-east-2) and verify model availability, access requirements, and pricing.

4. Ensure the AWS identity running the application has permission to invoke the configured model. For Nova Lite in `us-east-2`, the following example IAM policy grants access to that specific model:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowNovaLiteInference",
      "Effect": "Allow",
      "Action": "bedrock:InvokeModel",
      "Resource": "arn:aws:bedrock:us-east-2::foundation-model/amazon.nova-lite-v1:0"
    }
  ]
}
```

5. Run BatteryGuard Vision and select **AWS Lambda + Bedrock Vision (experimental)**.

If Bedrock access is unavailable or restricted, use **AWS Lambda** or **Local OpenCV** mode instead.

**Security:** Never commit AWS credentials to the repository. Organizational service control policies and other account restrictions may override IAM permissions.

## Run

```powershell
python -m pip install -r requirements.txt
streamlit run app.py
```

Select `AWS Lambda + Bedrock Vision (experimental)`. One upload runs the existing Lambda processing and an optional **charged** Bedrock inference call. Keep request counts low and monitor AWS credit usage. No known reliable defect detection accuracy; claims must be supported by held-out testing.

Model: `amazon.nova-lite-v1:0` via the documented Converse API. If denied, the UI reports the error without losing OpenCV analysis. Other models are not automatically substituted.
