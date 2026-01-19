# Evaluation – Authenticity Results

## Configuration

### Models

* **Filter context model:** `mistralai/mistral-medium-3-instruct`
* **Generation model:** `mistralai/mistral-small-24b-instruct`

### RAG Setup

* **Chunk Size:** 1,200 characters (~300–350 tokens)
* **Chunk Overlap:** 50 characters (to preserve context continuity)
* **Input:** 222-page document split into 712 total text chunks

### Test Dataset

* **Source:** Customer Segmentation Analysis PDF
* **Ground Truth:** 31 evaluation questions focused on the *Curious Connoisseurs* segment

## Results

| Metric                    | Score    | Interpretation                                       |
| ------------------------- |----------| ---------------------------------------------------- |
| Expert Authenticity Score | 4.66 / 5 | Persona behavior is highly authentic                 |
| Style Alignment Score     | 4.74 / 5 | Style is highly consistent, with minimal drift       |
| Factual Grounding Score   | 4.44 / 5 | Responses are well grounded                          |

**Key Finding**: Authenticity, style alignment, and grounding all score above 4.4/5, indicating strong persona fidelity with consistent style and reliable grounding.
