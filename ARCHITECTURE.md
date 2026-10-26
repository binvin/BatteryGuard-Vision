# BatteryGuard Vision - Architecture

```mermaid
flowchart TD
    A[Battery photo JPG / PNG] --> B[Streamlit UI running locally]
    B -->|Authenticated boto3 invoke| C[AWS Lambda us-east-2]
    D[Amazon ECR private image] -.-> C
    C --> E[OpenCV 5 image-quality checks and candidate cues]
    E --> F[Annotated JPEG + structured JSON]
    F --> B
    B -->|Optional experimental image request| G[Amazon Bedrock Nova Lite us-east-2]
    G --> H[Contextual assessment / uncertainty / follow-up]
    H --> B
    B --> I[Inspector reviews evidence; no safety certification]
```

**Implemented:** Streamlit, private Lambda container, ECR, OpenCV 5, optional Bedrock call. **Not implemented:** COOL/Graviton, MCP, fully autonomous agent/tool loop, public production endpoint, validated battery diagnosis.
