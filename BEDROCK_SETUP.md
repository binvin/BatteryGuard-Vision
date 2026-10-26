# Amazon Bedrock Vision Integration

BatteryGuard Vision optionally uses **Amazon Bedrock Nova Lite** to provide contextual visual analysis of battery photographs.

This complements the OpenCV 5 image-processing engine running on AWS Lambda. OpenCV identifies image-quality issues and candidate visual anomalies, while Bedrock evaluates potential defects in context and provides evidence-aware findings.

The Bedrock integration is invoked separately by the Streamlit application. No modification to the existing Lambda container is required.

## Prerequisites

- An AWS account with access to Amazon Bedrock.
- AWS credentials configured through an IAM role, IAM Identity Center, AWS CLI profile, or another supported boto3 credential provider.
- Permission to invoke the configured Bedrock model.
- An AWS region where Amazon Nova Lite is available.

## AWS Configuration

BatteryGuard Vision supports these environment variables:

| Variable | Default | Description |
|---|---|---|
| `BATTERYGUARD_AWS_REGION` | `us-east-2` | AWS region |
| `BATTERYGUARD_AWS_PROFILE` | Optional | Named AWS CLI profile, if applicable |
| `BATTERYGUARD_BEDROCK_MODEL_ID` | `amazon.nova-lite-v1:0` | Bedrock model identifier |

When `BATTERYGUARD_AWS_PROFILE` is not specified, boto3 uses its standard credential provider chain.

## IAM Permissions

The AWS identity running BatteryGuard Vision must have permission to invoke the configured Bedrock model.

For Amazon Nova Lite in `us-east-2`, the following is an example of a narrowly scoped IAM policy:

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

Attach this policy only through an appropriately authorized AWS administrator. Other models, regions, or inference profiles may require different resource permissions.

Organizational service control policies or other AWS restrictions may prevent model invocation even when IAM permissions are granted.

## Installation and Execution

Install project dependencies:

```bash
python -m pip install -r requirements.txt
```

Launch the Streamlit application:

```bash
python -m streamlit run app.py
```

Open `http://localhost:8501` and select **AWS Lambda + Bedrock Vision (experimental)**.

Upload a JPG or PNG battery photograph to begin the inspection.

In this mode, the application:

1. Invokes the private AWS Lambda function for OpenCV 5 image processing.
2. Sends the image to Amazon Bedrock Nova Lite for contextual visual analysis.
3. Displays OpenCV candidate regions alongside Bedrock's structured assessment.
4. Provides potential findings, uncertainty, and suggested follow-up evidence when appropriate.

The Bedrock assessment is separate from the OpenCV annotations. Model-generated findings are not automatically mapped to bounding boxes.

## Handling Errors

If Bedrock is unavailable because of IAM permissions, model availability, or account restrictions, the application reports the error while retaining the OpenCV analysis.

Users can also select **AWS Lambda** or **Local OpenCV** to run the application without Bedrock inference.

The application does not automatically substitute another model when Nova Lite is unavailable.

## Cost and Security

- Amazon Bedrock inference is usage-based and may incur charges.
- Monitor AWS usage and available credits during testing.
- Do not commit access keys, secret keys, or credential files to the repository.
- Use least-privilege IAM permissions wherever possible.
- Keep the Lambda function private and use authenticated AWS SDK calls.

## Known Limitations

Amazon Nova Lite provides contextual visual assessments but is not a specialized, clinically or industrially validated battery-defect detector.

The model may misidentify ordinary battery features, overlook visible abnormalities, or provide inaccurate descriptions.

Potential swelling, corrosion, leakage, or casing damage must be treated as preliminary observations requiring human verification.

BatteryGuard Vision cannot determine battery safety, predict thermal runaway, or establish the absence of hidden damage from a photograph.

**The application is intended for experimental visual screening and decision support, not safety certification.**
