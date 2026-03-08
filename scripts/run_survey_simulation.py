"""CLI utility for survey simulation workflows."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from adsp.config import PROCESSED_DATA_DIR
from adsp.core.survey import GroupGenerator, ResponseSynthesizer, SurveyManager


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Survey simulation workflow")
    parser.add_argument("--base-dir", type=Path, default=PROCESSED_DATA_DIR / "surveys")

    parser.add_argument("--create-survey", type=Path, help="Path to survey definition JSON")
    parser.add_argument("--create-group", type=Path, help="Path to group composition JSON")
    parser.add_argument("--simulate", action="store_true", help="Run simulation")
    parser.add_argument("--survey-id", type=str, help="Survey id for simulation/export")
    parser.add_argument("--group-id", type=str, help="Group id for simulation")
    parser.add_argument("--mode", type=str, default="random", choices=["random", "llm"])
    parser.add_argument("--sampling-ratio", type=float, default=0.7)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument("--export-format", type=str, choices=["csv", "json"], default="csv")

    args = parser.parse_args()

    surveys = SurveyManager(base_dir=args.base_dir)
    groups = GroupGenerator(base_dir=args.base_dir)
    responses = ResponseSynthesizer(base_dir=args.base_dir)

    created_survey_id = args.survey_id
    created_group_id = args.group_id

    if args.create_survey:
        survey = surveys.create_survey(_load_json(args.create_survey))
        created_survey_id = survey.survey_id
        print(f"Created survey: {survey.survey_id}")

    if args.create_group:
        payload = _load_json(args.create_group)
        composition = payload.get("composition") if isinstance(payload, dict) else payload
        group = groups.create_group(
            composition,
            mode=args.mode,
            sampling_ratio=args.sampling_ratio,
            seed=args.seed,
        )
        created_group_id = group.group_id
        print(f"Created group: {group.group_id} ({len(group.respondents)} respondents)")

    if args.simulate:
        if not created_survey_id or not created_group_id:
            raise SystemExit("--simulate requires survey_id and group_id (or creation in the same command)")

        result = responses.run_simulation(
            survey_id=created_survey_id,
            group_id=created_group_id,
            batch_size=args.batch_size,
        )
        output = responses.export_responses(
            survey_id=created_survey_id,
            simulation_id=result.simulation_id,
            format=args.export_format,
        )
        print(f"Simulation: {result.simulation_id}")
        print(f"Responses exported: {output}")


if __name__ == "__main__":
    main()
