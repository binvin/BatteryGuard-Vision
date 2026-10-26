# BatteryGuard Vision

### See the signs. Understand the evidence. Guide the next action.

**BatteryGuard Vision** is an AI-assisted visual inspection prototype that combines **OpenCV 5, AWS Lambda, and Amazon Bedrock Nova Lite** to help identify potential visible battery abnormalities and support evidence-aware inspections.

Designed for electronics repair, battery recycling, and maintenance workflows, the application analyzes battery photographs for image quality, candidate surface irregularities, and contextual signs of possible residue, corrosion, casing damage, or deformation.

Instead of making definitive safety judgments, BatteryGuard Vision highlights visual evidence, communicates uncertainty, and recommends additional inspection when appropriate.

> **Disclaimer:** BatteryGuard Vision is an experimental visual screening tool, not a certified battery diagnostic or safety assessment system. It cannot establish whether a battery is safe. Do not handle or disturb potentially damaged batteries to obtain photographs.

## Features

- **Image-quality assessment:** Evaluates resolution, sharpness, and lighting using OpenCV 5.
- **Visual anomaly highlighting:** Identifies candidate color, texture, and surface irregularities.
- **Residue screening:** Highlights some pale granular regions that may resemble leakage deposits.
- **Contextual AI analysis:** Uses Amazon Bedrock Nova Lite to interpret possible visible abnormalities in context.
- **Evidence-aware recommendations:** Provides findings, approximate locations, uncertainty, and suggested follow-up inspection.
- **Cloud-native processing:** Runs the OpenCV 5 analysis engine in a containerized AWS Lambda function.
- **Multiple processing modes:** Supports local computer vision, AWS Lambda, and AWS Lambda with Bedrock Vision.
- **Inspection reports:** Displays annotated images and structured inspection results.

## Technology Stack

| Component | Technology |
|---|---|
| Programming language | Python |
| Computer vision | OpenCV 5, NumPy |
| Interface | Streamlit |
| Cloud image processing | AWS Lambda |
| Container registry | Amazon ECR |
| Contextual vision AI | Amazon Bedrock — Nova Lite |
| Containerization | Docker |
| AWS integration | boto3, AWS CLI |
| Image handling | Pillow |

## Architecture

BatteryGuard Vision follows a hybrid computer-vision and multimodal-AI workflow.

```text
User uploads battery photograph
               |
               v
       Streamlit Web UI
               |
               v
       AWS Lambda (Ohio)
               |
               v
     OpenCV 5 Image Analysis
       |                 |
       v                 v
 Image Quality      Candidate Visual
 Assessment         Anomaly Regions
       |                 |
       +--------+--------+
                |
                v
        Annotated Results
                |
                v
     Amazon Bedrock Nova Lite
                |
                v
   Contextual Visual Assessment
                |
                v
     Inspection Findings and
    Follow-up Recommendations
```

In the AWS Lambda + Bedrock mode, the Streamlit application invokes the private Lambda function for OpenCV analysis and separately calls Amazon Bedrock for contextual interpretation. The results are displayed together; model-generated findings are not automatically mapped to OpenCV bounding boxes.

## Installation and Local Setup

### Prerequisites

- Python 3.11 or later, compatible with the pinned dependencies
- Windows, Linux, or macOS
- Git (optional)
- AWS credentials for cloud processing modes

### 1. Clone the repository

```bash
git clone https://github.com/binvin/BatteryGuard-Vision
cd BatteryGuardVision
```

### 2. Create a virtual environment

**Windows PowerShell:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Linux/macOS:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Verify OpenCV:

```bash
python -c "import cv2; print(cv2.__version__)"
```

The application was developed with OpenCV 5.0.0.

### 4. Launch the application

```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

## Processing Modes

BatteryGuard Vision supports three modes:

**1. Local OpenCV**

Runs OpenCV analysis locally. No AWS credentials are required.

**2. AWS Lambda**

Invokes a private AWS Lambda function running the OpenCV 5 image-analysis engine.

**3. AWS Lambda + Bedrock Vision**

Combines the AWS Lambda/OpenCV results with contextual AI interpretation using Amazon Bedrock Nova Lite.

Cloud modes require access to appropriately configured AWS resources and IAM permissions.

## AWS Configuration

The application supports these environment variables:

| Variable | Default |
|---|---|
| `BATTERYGUARD_AWS_REGION` | `us-east-2` |
| `BATTERYGUARD_AWS_PROFILE` | Optional |
| `BATTERYGUARD_LAMBDA_FUNCTION` | `batteryguard-vision-api` |
| `BATTERYGUARD_BEDROCK_MODEL_ID` | `amazon.nova-lite-v1:0` |

When no AWS profile is specified, boto3 uses its standard credential provider chain.

Example PowerShell configuration:

```powershell
$env:BATTERYGUARD_AWS_REGION = "us-east-2"
$env:BATTERYGUARD_AWS_PROFILE = "your-profile-name"
$env:BATTERYGUARD_LAMBDA_FUNCTION = "batteryguard-vision-api"
```

For Bedrock-specific permissions and configuration, see `bedrock_setup.md`.

### Security and Cost Considerations

- Never commit AWS access keys, secret keys, or credentials to the repository.
- Keep the Lambda function private and use authenticated SDK requests.
- Do not enable a public unauthenticated Lambda Function URL.
- AWS Lambda, ECR, and Bedrock may incur usage charges.
- Uploaded image size is recommended to remain under 3 MB for this prototype, subject to actual application enforcement and Lambda payload constraints.

## AWS Lambda Container Deployment

The OpenCV image-analysis engine is packaged as a Linux container and stored in Amazon ECR.

Typical deployment workflow:

1. Build the Docker image for Linux x86_64.
2. Push the image to a private Amazon ECR repository.
3. Create an image-based Lambda function using the ECR image.
4. Configure appropriate IAM permissions and runtime settings.
5. Test the function with a battery-image payload.
6. Configure Streamlit to invoke the deployed function.

**Important:** Pushing a new image to an existing ECR tag does not automatically update the Lambda function. Explicitly update the function's image reference and wait for deployment to complete.

See `ARCHITECTURE.md` and the deployment documentation for additional information.

## Testing

Run automated tests:

```bash
python -m pip install pytest
python -m pytest -q
```

Suggested manual evaluation scenarios:

| Test scenario | Expected behavior |
|---|---|
| Battery with visible leakage-like residue | Candidate regions and possible residue assessment |
| Clean battery | No unsupported damage claim from contextual AI |
| Battery with corrosion-like deposits | Potential abnormality identified for human review |
| Visibly deformed battery | Possible deformation reported when visual evidence supports it |
| Low-resolution or blurry image | Image-quality warning and recommendation for better evidence |

These are expected behaviors, not guarantees of detection.

### Evaluation and Known Limitations

Testing across cylindrical alkaline batteries, lithium-ion cells, lithium-polymer batteries, and 9V batteries demonstrated promising identification of some visible residue and corrosion-like regions.

The following limitations remain:

- OpenCV heuristics may highlight normal labels, tape, seams, reflections, and background textures.
- Candidate regions are not verified battery defects.
- Bedrock assessments can be incomplete, incorrect, or inconsistent.
- Swelling, punctures, and hidden damage cannot be reliably established from a single image.
- Model findings are not yet spatially linked to OpenCV-generated bounding boxes.
- The prototype has not undergone extensive validation on a representative labeled dataset.

The application is intended to support preliminary visual screening and human review, not replace professional inspection or determine battery safety.

## Responsible Use

BatteryGuard Vision should be used as a decision-support prototype only.

Potentially damaged lithium-ion batteries can present fire and injury risks even without visible defects. Users should follow applicable battery-handling guidance and consult qualified professionals when damage is suspected.

The application does not provide battery safety certification, electrical diagnostics, or thermal hazard prediction.

## Future Improvements

- Train battery-specific defect detection models using representative labeled datasets.
- Improve defect localization and reduce false positives.
- Expand multi-angle and deformation analysis.
- Introduce adaptive inspection workflows with human approval.
- Support batch inspection and historical comparisons.
- Explore edge-device deployment and specialized battery recycling workflows.

## Hackathon

Developed as a solo project for the **OpenCV AI Competition 2026**.

**Primary focus areas:** Safety, cloud-native computer vision, evidence-aware inspection, and potential applications in electronics recycling.

**Core technologies:** OpenCV 5, AWS Lambda, Amazon ECR, Amazon Bedrock Nova Lite, Python, and Streamlit.

## License

See the repository's license information. Licensing terms will be specified by the project owner before publication.
