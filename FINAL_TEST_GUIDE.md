# Final test: v4.1 frozen prompt pilot

Run `python -m pytest -q` and `python -m streamlit run app.py --server.port 8502`. Choose **AWS Lambda + Bedrock Vision (experimental)**.

Evaluate on photographs **not used to change the prompt**, without retuning after each outcome. Suggested holdout: 2 leakage/corrosion, 2 normal with colorful labels, 2 swelling/deformation, 1 blurry photo.

Record for each: visual ground truth (human-observed, not chemical certainty), returned category, whether evidence description matches the visible feature, false positives, false negatives, and whether next-evidence request is safe.

The bounding boxes remain the original OpenCV candidate overlays. They are **not Bedrock-localized defect boxes**. The Bedrock output is an independent textual interpretation. No trained battery defect classifier or quantitative accuracy has been established.

If Bedrock hallucinations persist, retain the documented limitations and do not advertise reliable swelling detection or battery safety verification.
