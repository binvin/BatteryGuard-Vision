# BatteryGuard Vision

**Photo-quality and visual color-anomaly triage**, built with OpenCV 5 and optionally processed on AWS Lambda. **Not a battery safety determination**. Detects orange-brown *color candidates*, not verified corrosion or other damage. No automatic battery localization. Do not handle damaged batteries to get demo images.

## Run on Windows

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

### AWS Configuration

BatteryGuard Vision supports three processing modes:

- **Local OpenCV:** Runs image analysis locally without AWS credentials.
- **AWS Lambda:** Executes OpenCV 5 image processing using a private AWS Lambda function.
- **AWS Lambda + Bedrock Vision:** Combines OpenCV 5 processing with contextual visual analysis using Amazon Bedrock Nova Lite.

AWS configuration can be customized using environment variables:

| Variable | Default |
|---|---|
| `BATTERYGUARD_AWS_REGION` | `us-east-2` |
| `BATTERYGUARD_AWS_PROFILE` | Optional (uses standard AWS credentials if unset) |
| `BATTERYGUARD_LAMBDA_FUNCTION` | `batteryguard-vision-api` |
| `BATTERYGUARD_BEDROCK_MODEL_ID` | `amazon.nova-lite-v1:0` |

When no AWS profile is specified, boto3 uses its standard credential provider chain. AWS processing requires appropriate Lambda and Bedrock permissions.

**Security:** Never commit AWS credentials or secret keys to the repository. Keep the Lambda function private and do not enable a public unauthenticated Function URL.

**Image limits:** The application uses a 3 MB image-size guideline to accommodate base64 encoding and Lambda's synchronous request/response payload limits. This is not the AWS service's actual image-size limit.

**Judge access:** Local OpenCV mode works without AWS credentials. AWS-integrated functionality can be demonstrated through an authorized live screen-share or recorded demo.

## Validation

```powershell
python -m pip install pytest
python -m pytest -q
```

For the hackathon, test multiple labeled photos, including blurred and dark cases, and document false positives/negatives honestly. The app cannot establish swelling, cracks, thermal hazards, or battery safety.

## Experimental surface-line cue (v2)

In addition to amber/brown color candidates (orange outline), OpenCV black-hat morphology finds narrow dark line candidates (blue outline). This may react to printed text, normal seams, tape edges, shadows, and surface marks; it is not a trained scratch or crack classifier. Do not use the findings to declare a battery safe or damaged. Use labeled photos to assess false positives and misses. The included synthetic line test validates the pipeline only, not real-world defect accuracy.

### Redeploy an existing image-based Lambda

After building/pushing a fresh `latest` ECR image, Lambda does **not** automatically pull an overwritten tag. Update function code using the new image URI (with a deployer identity authorized to update the function) and wait for the update to succeed. Default AWS region for this project: `us-east-2`.

## v3: Pale granular residue candidates
Highlights some bright low-saturation high-texture clusters in magenta. This is a heuristic, not a trained leakage detector: paper, dust, labels, concrete and glare can be mistaken for residue. Test on known-negative images and label failures.
