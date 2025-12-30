"""Run persona extraction evaluation metrics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from adsp.monitoring.evaluation_pipeline import PersonaExtractionEvaluator


REPO_ROOT = Path(__file__).resolve().parents[2]


def _default_system_output() -> Path:
    primary = REPO_ROOT / "data/evaluation/persona_extraction/system_output"
    if primary.exists() and any(primary.glob("*.json")):
        return primary
    fallback = REPO_ROOT / "data/interim/persona_extraction/pages"
    if fallback.exists() and any(fallback.glob("*.json")):
        return fallback
    return primary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate persona extraction metrics.")
    parser.add_argument(
        "--ground-truth-dir",
        type=Path,
        default=REPO_ROOT / "data/evaluation/persona_extraction/ground_truth",
        help="Directory containing ground truth page annotations.",
    )
    parser.add_argument(
        "--system-output",
        type=Path,
        default=_default_system_output(),
        help="Directory or JSON file containing system extraction output.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "data/evaluation/persona_extraction/evaluation_results.json",
        help="Where to write the evaluation results JSON.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.5,
        help="Word overlap threshold for indicator and statement matching.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.ground_truth_dir.exists():
        raise FileNotFoundError(f"Ground truth dir not found: {args.ground_truth_dir}")
    if not args.system_output.exists():
        raise FileNotFoundError(f"System output not found: {args.system_output}")

    evaluator = PersonaExtractionEvaluator(
        ground_truth_dir=args.ground_truth_dir,
        system_output_path=args.system_output,
        word_overlap_threshold=args.threshold,
    )
    results = evaluator.run_evaluation()

    print("Persona Extraction Evaluation")
    print(f"Persona Detection Rate: {results['persona_detection_rate']:.2%}")
    print(f"Metrics Recall: {results['metrics_recall']:.2%}")
    print(f"Metrics Precision: {results['metrics_precision']:.2%}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2)
    print(f"Results saved to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
