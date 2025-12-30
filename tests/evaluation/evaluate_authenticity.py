"""Run persona authenticity evaluation pipelines."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Sequence

from adsp.core.orchestrator import Orchestrator
from adsp.core.rag.fact_data_index import build_fact_data_index_from_markdown
from adsp.core.rag.persona_index import PersonaRAGIndex
from adsp.core.types import ChatRequest
from adsp.data_pipeline.schema import load_persona_profile
from adsp.monitoring.evaluation_pipeline import AuthenticityEvaluator


REPO_ROOT = Path(__file__).resolve().parents[2]


def _default_questions_file() -> Path:
    return REPO_ROOT / "data/evaluation/authenticity/test_questions.json"


def _default_evaluations_file() -> Path:
    return REPO_ROOT / "data/evaluation/authenticity/system_output/generated_responses.json"


def _default_persona_dir() -> Path:
    return REPO_ROOT / "data/processed/personas/individual"


def _default_fact_data_dir() -> Path:
    return REPO_ROOT / "data/processed/fact_data/pages"


def _default_generated_output() -> Path:
    return REPO_ROOT / "data/evaluation/authenticity/system_output/generated_responses.json"


def _default_evaluation_output() -> Path:
    return REPO_ROOT / "data/evaluation/authenticity/evaluation_results.json"


def _parse_persona_ids(raw: str) -> List[str]:
    values = [item.strip() for item in raw.split(",") if item.strip()]
    if not values:
        raise ValueError("persona ids cannot be empty")
    return values


def _load_questions_file(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _normalize_question_entries(payload: Any) -> List[Dict[str, Any]]:
    if isinstance(payload, dict) and isinstance(payload.get("test_questions"), list):
        payload = payload["test_questions"]

    if isinstance(payload, dict) and not isinstance(payload.get("test_questions"), list):
        entries: List[Dict[str, Any]] = []
        for category, items in payload.items():
            if not isinstance(items, list):
                continue
            for item in items:
                if isinstance(item, str):
                    entries.append({"query": item, "category": category})
                elif isinstance(item, dict):
                    query = item.get("query") or item.get("question")
                    if query:
                        entries.append(
                            {
                                "query": query,
                                "category": item.get("category", category),
                                "persona_id": item.get("persona_id"),
                            }
                        )
        return entries

    if isinstance(payload, list):
        entries: List[Dict[str, Any]] = []
        for item in payload:
            if isinstance(item, str):
                entries.append({"query": item})
            elif isinstance(item, dict):
                query = item.get("query") or item.get("question")
                if not query:
                    continue
                entries.append(
                    {
                        "query": query,
                        "category": item.get("category"),
                        "persona_id": item.get("persona_id"),
                    }
                )
        return entries

    raise ValueError("Unsupported test questions format.")


def _resolve_persona_ids(
    entries: Sequence[Dict[str, Any]],
    persona_dir: Path,
    persona_ids: Sequence[str] | None,
) -> List[str]:
    if persona_ids:
        return list(persona_ids)

    from_entries = sorted(
        {
            entry.get("persona_id")
            for entry in entries
            if isinstance(entry.get("persona_id"), str) and entry.get("persona_id")
        }
    )
    if from_entries:
        return list(from_entries)

    persona_files = sorted(persona_dir.glob("*.json"))
    if not persona_files:
        raise FileNotFoundError(f"No persona profiles found in {persona_dir}")
    return [path.stem for path in persona_files]


def _expand_questions(
    entries: Sequence[Dict[str, Any]], persona_ids: Sequence[str]
) -> List[Dict[str, Any]]:
    expanded = []
    for entry in entries:
        query = entry.get("query")
        if not query:
            continue
        category = entry.get("category")
        persona_id = entry.get("persona_id")
        if persona_id:
            expanded.append({"persona_id": persona_id, "query": query, "category": category})
        else:
            for pid in persona_ids:
                expanded.append({"persona_id": pid, "query": query, "category": category})
    return expanded


def _load_persona_profiles(persona_dir: Path, persona_ids: Sequence[str]) -> List[Any]:
    profiles = []
    for persona_id in persona_ids:
        persona_path = persona_dir / f"{persona_id}.json"
        if not persona_path.exists():
            raise FileNotFoundError(f"Persona profile not found: {persona_path}")
        profiles.append(load_persona_profile(persona_path))
    return profiles


def _build_orchestrator(
    profiles: Sequence[Any],
    *,
    fact_data_dir: Path | None,
) -> Orchestrator:
    orchestrator = Orchestrator()
    orchestrator.prompt_builder.registry.upsert_many(
        [(profile.persona_id, profile) for profile in profiles if profile.persona_id]
    )

    persona_index = PersonaRAGIndex()
    persona_index.index_personas(profiles)
    orchestrator.retriever.persona_index = persona_index

    if fact_data_dir and fact_data_dir.exists():
        fact_index = build_fact_data_index_from_markdown(fact_data_dir)
        if fact_index is not None:
            orchestrator.fact_data_index = fact_index

    return orchestrator


def _add_generate_subparser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("generate", help="Generate persona responses for evaluation.")
    parser.add_argument(
        "--questions-file",
        type=Path,
        default=_default_questions_file(),
        help="JSON file containing test questions.",
    )
    parser.add_argument(
        "--persona-dir",
        type=Path,
        default=_default_persona_dir(),
        help="Directory containing persona profiles.",
    )
    parser.add_argument(
        "--persona-ids",
        type=_parse_persona_ids,
        default=None,
        help="Comma-separated list of persona ids to evaluate.",
    )
    parser.add_argument(
        "--fact-data-dir",
        type=Path,
        default=_default_fact_data_dir(),
        help="Directory containing fact data markdown pages (optional).",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Top-k documents to retrieve for each response.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=_default_generated_output(),
        help="Where to write the generated responses JSON.",
    )


def _add_evaluate_subparser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("evaluate", help="Compute authenticity metrics.")
    parser.add_argument(
        "--evaluations-file",
        type=Path,
        default=_default_evaluations_file(),
        help="JSON file containing persona responses with ratings.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=_default_evaluation_output(),
        help="Where to write the evaluation results JSON.",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Persona authenticity evaluation pipelines.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    _add_generate_subparser(subparsers)
    _add_evaluate_subparser(subparsers)
    return parser.parse_args()


def _build_questions_payload(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        fallback = _default_evaluations_file()
        if path == _default_questions_file() and fallback.exists():
            payload = _load_questions_file(fallback)
        else:
            raise FileNotFoundError(f"Questions file not found: {path}")
    else:
        payload = _load_questions_file(path)
    return _normalize_question_entries(payload)


def _generate_template_ratings() -> Dict[str, Any]:
    return {
        "authenticity": None,
        "style_alignment": None,
        "factual_grounding": None,
    }


def _run_generate(args: argparse.Namespace) -> int:
    if not args.persona_dir.exists():
        raise FileNotFoundError(f"Persona dir not found: {args.persona_dir}")

    question_entries = _build_questions_payload(args.questions_file)
    persona_ids = _resolve_persona_ids(question_entries, args.persona_dir, args.persona_ids)
    expanded_questions = _expand_questions(question_entries, persona_ids)

    profiles = _load_persona_profiles(args.persona_dir, persona_ids)
    orchestrator = _build_orchestrator(
        profiles,
        fact_data_dir=args.fact_data_dir if args.fact_data_dir.exists() else None,
    )

    generated: List[Dict[str, Any]] = []
    for entry in expanded_questions:
        persona_id = entry["persona_id"]
        query = entry["query"]
        response = orchestrator.handle(
            ChatRequest(
                persona_id=persona_id,
                query=query,
                session_id=f"auth_eval_{persona_id}",
                top_k=args.top_k,
            )
        )
        generated.append(
            {
                "persona_id": persona_id,
                "query": query,
                "category": entry.get("category"),
                "response": response.answer,
                "citations": [c.model_dump() for c in response.citations],
                "context": response.context,
                "ratings": _generate_template_ratings(),
            }
        )

    payload = {"test_questions": generated}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    print(f"Generated responses saved to {args.output}")
    return 0


def _run_evaluate(args: argparse.Namespace) -> int:
    if not args.evaluations_file.exists():
        raise FileNotFoundError(f"Evaluations file not found: {args.evaluations_file}")

    evaluator = AuthenticityEvaluator(evaluations_file=args.evaluations_file)
    results = evaluator.run_evaluation()

    print("Authenticity Evaluation")
    print(f"Expert Authenticity Score: {results['expert_authenticity_score']:.2f}")
    print(f"Style Alignment Score: {results['style_alignment_score']:.2f}")
    print(f"Factual Grounding Score: {results['factual_grounding_score']:.2f}")
    print(f"Total Evaluations: {results['total_evaluations']}")
    persona_scores = results.get("persona_scores", {})
    if persona_scores:
        print("Per-Persona Averages")
        for persona_id in sorted(persona_scores):
            scores = persona_scores[persona_id]
            print(
                "  "
                f"{persona_id}: authenticity={scores['authenticity']:.2f}, "
                f"style_alignment={scores['style_alignment']:.2f}, "
                f"factual_grounding={scores['factual_grounding']:.2f}, "
                f"total={scores['total_evaluations']}"
            )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2)
    print(f"Results saved to {args.output}")
    return 0


def main() -> int:
    args = parse_args()
    if args.command == "generate":
        return _run_generate(args)
    if args.command == "evaluate":
        return _run_evaluate(args)
    raise ValueError(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
