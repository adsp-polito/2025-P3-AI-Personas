# Evaluation – Fact Extraction

## Configuration

### Models

* **PDF to Markdown Conversion:** `mistralai/mistral-large-3-675b-instruct-2512`

### Test Dataset

* **Scope:** 23 pages focused on the *Curious Connoisseurs* segment
* **Source:** Customer Segmentation Analysis PDF
* **Ground Truth:** 467 validated metric and statement snippets manually extracted from the PDF

## Results

| Metric               | Score | Interpretation                                                    |
| -------------------- | ----- | ----------------------------------------------------------------- |
| Exact Match Accuracy | 97%   | High extraction accuracy with minimal deviation from ground truth |
