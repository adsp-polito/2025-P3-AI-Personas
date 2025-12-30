"""Run retrieval relevance evaluation pipelines."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Sequence

from adsp.core.rag.fact_data_index import build_fact_data_index_from_markdown


REPO_ROOT = Path(__file__).resolve().parents[2]


def _default_queries_file() -> Path:
    return REPO_ROOT / "data/evaluation/rag_retrieval/ground_truth/test_queries.json"


def _default_retrieval_output() -> Path:
    return REPO_ROOT / "data/evaluation/rag_retrieval/system_output/retrieval_results.json"


def _default_evaluation_output() -> Path:
    return REPO_ROOT / "data/evaluation/rag_retrieval/evaluation_results.json"


def _default_fact_data_dir() -> Path:
    return REPO_ROOT / "data/processed/fact_data/pages"


def _load_queries(path: Path) -> List[Dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and isinstance(payload.get("test_queries"), list):
        return payload["test_queries"]
    return payload


def _doc_to_payload(doc: Any, *, rank: int, score: float | None) -> Dict[str, Any]:
    return {
        "page_content": doc.page_content,
        "metadata": doc.metadata or {},
        "rank": rank,
        "score": score,
        "relevance": None,
    }

def _build_fact_index(markdown_dir: Path) -> Any:
    index = build_fact_data_index_from_markdown(markdown_dir)
    if index is None:
        raise FileNotFoundError(f"No fact data markdown found in {markdown_dir}")
    return index


def _search_with_scores(index: Any, query: str, *, k: int) -> List[Dict[str, Any]]:
    vectorstore = index.rag.vectorstore
    if hasattr(vectorstore, "similarity_search_with_score"):
        try:
            results = vectorstore.similarity_search_with_score(query, k=k)
            return [
                {"doc": doc, "score": float(score) if score is not None else None}
                for doc, score in results
            ]
        except Exception:
            pass
    docs = index.search(query, k=k)
    return [{"doc": doc, "score": None} for doc in docs]


def _parse_k_values(raw: str) -> List[int]:
    values: List[int] = []
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        value = int(item)
        if value <= 0:
            raise ValueError("k values must be positive integers")
        values.append(value)
    if not values:
        raise ValueError("k values cannot be empty")
    return values


def _is_relevant(doc: Dict[str, Any]) -> bool:
    return doc.get("relevance") == 1 or doc.get("relevance_label") == 1


def _compute_metrics(
    labeled_results: List[Dict[str, Any]],
    k_values: Sequence[int],
) -> Dict[str, Any]:
    totals = {k: {"precision": 0.0, "recall": 0.0} for k in k_values}
    details: List[Dict[str, Any]] = []
    unlabeled_total = 0

    for entry in labeled_results:
        retrieved_docs = entry.get("retrieved_docs") or entry.get("relevant_docs") or []
        if not isinstance(retrieved_docs, list):
            retrieved_docs = []

        relevant_count = sum(1 for doc in retrieved_docs if _is_relevant(doc))
        unlabeled = sum(
            1
            for doc in retrieved_docs
            if doc.get("relevance") is None and doc.get("relevance_label") is None
        )
        unlabeled_total += unlabeled
        detail_entry = {
            "query_id": entry.get("query_id"),
            "query": entry.get("query"),
            "retrieved_total": len(retrieved_docs),
            "relevant_total": relevant_count,
            "unlabeled_total": unlabeled,
        }

        for k in k_values:
            top_k = retrieved_docs[:k]
            hits = sum(1 for doc in top_k if _is_relevant(doc))
            precision = hits / k if k else 0.0
            recall = hits / relevant_count if relevant_count else 0.0
            totals[k]["precision"] += precision
            totals[k]["recall"] += recall
            detail_entry[f"precision_at_{k}"] = precision
            detail_entry[f"recall_at_{k}"] = recall

        details.append(detail_entry)

    query_count = len(labeled_results)
    averages = {
        f"precision_at_{k}": totals[k]["precision"] / query_count if query_count else 0.0
        for k in k_values
    }
    averages.update(
        {
            f"recall_at_{k}": totals[k]["recall"] / query_count if query_count else 0.0
            for k in k_values
        }
    )
    return {
        **averages,
        "total_queries": query_count,
        "unlabeled_total": unlabeled_total,
        "query_details": details,
        "k_values": list(k_values),
    }


def _add_retrieval_subparser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("retrieve", help="Run retrieval for all test queries.")
    parser.add_argument(
        "--queries-file",
        type=Path,
        default=_default_queries_file(),
        help="JSON file containing test queries.",
    )
    parser.add_argument(
        "--fact-data-dir",
        "--markdown-dir",
        type=Path,
        dest="fact_data_dir",
        default=_default_fact_data_dir(),
        help="Directory containing fact data markdown pages to index.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=_default_retrieval_output(),
        help="Where to write the retrieval results JSON.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=20,
        help="Number of documents to retrieve per query.",
    )


def _add_evaluate_subparser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("evaluate", help="Compute metrics from labeled results.")
    parser.add_argument(
        "--labeled-results",
        type=Path,
        default=_default_retrieval_output(),
        help="JSON file containing retrieved docs with manual relevance labels.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=_default_evaluation_output(),
        help="Where to write the evaluation results JSON.",
    )
    parser.add_argument(
        "--k-values",
        type=_parse_k_values,
        default=_parse_k_values("3,5,10,20"),
        help="Comma-separated list of K values for precision/recall (e.g., 3,5,10,20).",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="RAG retrieval evaluation pipelines.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    _add_retrieval_subparser(subparsers)
    _add_evaluate_subparser(subparsers)
    return parser.parse_args()


def _run_retrieval(args: argparse.Namespace) -> int:
    if not args.queries_file.exists():
        raise FileNotFoundError(f"Queries file not found: {args.queries_file}")
    if not args.fact_data_dir.exists():
        raise FileNotFoundError(f"Fact data dir not found: {args.fact_data_dir}")

    queries = _load_queries(args.queries_file)
    index = _build_fact_index(args.fact_data_dir)

    results: List[Dict[str, Any]] = []
    for query in queries:
        if not isinstance(query, dict):
            continue
        persona_id = query.get("persona_id") or ""
        query_text = query.get("query") or ""
        if not persona_id or not query_text:
            results.append(
                {
                    "query_id": query.get("query_id"),
                    "persona_id": persona_id,
                    "query": query_text,
                    "relevant_docs": [],
                }
            )
            continue

        retrieved = _search_with_scores(index, query_text, k=args.top_k)
        results.append(
            {
                "query_id": query.get("query_id"),
                "persona_id": persona_id,
                "query": query_text,
                "relevant_docs": [
                    _doc_to_payload(item["doc"], rank=rank, score=item["score"])
                    for rank, item in enumerate(retrieved, start=1)
                ],
            }
        )

    payload = {"top_k": args.top_k, "results": results}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    print(f"Retrieval results saved to {args.output}")
    return 0


def _run_evaluation(args: argparse.Namespace) -> int:
    if not args.labeled_results.exists():
        raise FileNotFoundError(f"Labeled results file not found: {args.labeled_results}")

    payload = json.loads(args.labeled_results.read_text(encoding="utf-8"))
    labeled_results = payload.get("results", payload)
    if not isinstance(labeled_results, list):
        raise ValueError("Labeled results must be a list of query result entries.")

    results = _compute_metrics(labeled_results, args.k_values)

    print("RAG Retrieval Evaluation")
    for key, value in results.items():
        if key.startswith(("precision_at_", "recall_at_")):
            print(f"{key}: {value:.2%}")
    print(f"Total Queries: {results['total_queries']}")
    if results["unlabeled_total"]:
        print(f"Unlabeled Docs: {results['unlabeled_total']}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2)
    print(f"Results saved to {args.output}")
    return 0


def main() -> int:
    args = parse_args()
    if args.command == "retrieve":
        return _run_retrieval(args)
    if args.command == "evaluate":
        return _run_evaluation(args)
    raise ValueError(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
