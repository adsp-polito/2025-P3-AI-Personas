# Evaluation – Retrieval Relevance

## Configuration

### Models

* **Embedding:** `sentence-transformers/all-mpnet-base-v2`

### RAG Setup

* **Chunk Size:** 1,200 characters
* **Chunk Overlap:** 50 characters
* **Input:** 222-page document split into 712 total text chunks

### Test Dataset

* **Source:** Customer Segmentation Analysis PDF
* **Ground Truth:** 31 evaluation questions focused on the *Curious Connoisseurs* segment

## Results

| Metric        | Score      | Interpretation                                  |
| ------------- | ---------- | ----------------------------------------------- |
| Precision@3   | 58.10%     | Top-3 results are moderately relevant           |
| Precision@5   | 56.80%     | Relevance remains stable in top-5               |
| Precision@10  | 54.20%     | Slight precision drop                           |
| Precision@20  | 55.50%     | Precision stabilizes at broader context window  |
| Recall@3      | 16.70%     | Limited coverage with very short context        |
| Recall@5      | 24.30%     | Partial retrieval of relevant context           |
| Recall@10     | 45.10%     | Balanced trade-off between precision and recall |
| **Recall@20** | **94.10%** | **Near-complete retrieval of relevant content** |
