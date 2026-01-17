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

| Metric       | Score  | Interpretation                              |
|--------------| ------ | ------------------------------------------- |
| Precision@3  | 89.25% | Top 3 results are mostly relevant; strong early ranking focus. |
| Precision@5  | 88.39% | High relevance persists in top 5 with minimal noise. |
| Precision@10 | 86.13% | Top 10 remains strong, though a few off-topic items appear. |
| Precision@20 | 82.58% | Relevance is still the majority, but dilution increases with depth. |
| Precision@25 | 80.90% | About 4/5 of top 25 are relevant; moderate noise beyond top 20. |
| Recall@3     | 14.87% | Only a small share of all relevant docs appear in top 3. |
| Recall@5     | 23.35% | Less than a quarter of relevant docs are in the top 5. |
| Recall@10    | 45.98% | Roughly half of all relevant docs are captured by top 10. |
| Recall@20    | 82.08% | Most relevant docs are retrieved by top 20. |
| Recall@25    | 100.00% | All relevant docs are retrieved by top 25 in this set. |

Overall, the system prioritizes precision at shallow depths while recall improves steadily with larger k. For use cases that need fast, concise answers, k=3–5 is strong on relevance but may miss many relevant chunks; k=10–20 offers a better balance.
