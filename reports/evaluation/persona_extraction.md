
# Evaluation – Persona Extraction

## Configuration

### Models

* **Extract indicators:** `mistralai/mistral-medium-3-instruct`
* **Persona traits reasoning:** `mistralai/mistral-medium-3-instruct`

### Test Dataset

* **Scope:** 23 pages focused on the *Curious Connoisseurs* segment
* **Source:** Customer Segmentation Analysis PDF
* **Ground Truth:** 1,051 metrics manually extracted and validated from the PDF

## Results

| Metric                 | Score  | Interpretation                                         |
| ---------------------- | ------ | ------------------------------------------------------ |
| Persona Detection Rate | 100%   | All personas correctly identified (23/23)              |
| Metrics Recall         | 95.30% | Very high coverage of ground-truth metrics (1002/1051) |
| Metrics Precision      | 96.80% | Minimal noise in extracted metrics (1002/1035)         |

