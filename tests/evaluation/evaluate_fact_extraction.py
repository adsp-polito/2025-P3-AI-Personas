"""Run fact extraction evaluation metrics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from adsp.monitoring.evaluation_pipeline import FactExtractionEvaluator


REPO_ROOT = Path(__file__).resolve().parents[2]


def _default_system_output() -> Path:
    primary = REPO_ROOT / "data/evaluation/fact_extraction/system_output/extraction_results.json"
    if primary.exists():
        return primary
    fallback = REPO_ROOT / "data/processed/fact_data/pages"
    if fallback.exists():
        return fallback
    return primary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate fact extraction accuracy.")
    parser.add_argument(
        "--ground-truth-file",
        type=Path,
        default=REPO_ROOT / "data/evaluation/fact_extraction/ground_truth/facts_ground_truth.json",
        help="JSON file containing fact extraction ground truth.",
    )
    parser.add_argument(
        "--system-output",
        type=Path,
        default=_default_system_output(),
        help="Directory or JSON file containing system output.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "data/evaluation/fact_extraction/evaluation_results.json",
        help="Where to write the evaluation results JSON.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.ground_truth_file.exists():
        raise FileNotFoundError(f"Ground truth file not found: {args.ground_truth_file}")
    if not args.system_output.exists():
        raise FileNotFoundError(f"System output not found: {args.system_output}")

    evaluator = FactExtractionEvaluator(
        ground_truth_file=args.ground_truth_file,
        system_output_path=args.system_output,
    )
    results = evaluator.run_evaluation()

    print("Fact Extraction Evaluation")
    print(f"Exact Match Accuracy: {results['exact_match_accuracy']:.2%}")
    print(f"Total Values: {results['total_values']}")
    print(f"Matched Values: {results['matched_values']}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2)
    print(f"Results saved to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
