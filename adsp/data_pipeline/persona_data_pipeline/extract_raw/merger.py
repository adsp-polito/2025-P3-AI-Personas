"""Merge and validation utilities for persona extraction results."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from loguru import logger

try:
    from adsp.data_pipeline.schema import PersonaProfileModel
    from pydantic import ValidationError
except ImportError as exc:  # pragma: no cover - import guard
    raise ImportError(
        "pydantic is required for the persona extraction pipeline. "
        "Install with `pip install pydantic`."
    ) from exc

from .models import PageExtractionResult


class PersonaMerger:
    def __init__(self, document_name: str, merge_strategy: Optional[Dict[str, str]] = None):
        self.document_name = document_name
        self.merge_strategy = merge_strategy or {}
        self.personas: Dict[str, Dict[str, Any]] = {}
        self.parse_failures: List[dict] = []

    def apply_page_result(self, result: PageExtractionResult) -> None:
        if result.error:
            self.parse_failures.append(
                {"page": result.page_number, "error": result.error, "raw": result.raw_text}
            )
            return
        if not result.persona_id:
            return
        persona = self.personas.setdefault(
            result.persona_id,
            {
                "persona_id": result.persona_id,
                "source_reference": {
                    "document": self.document_name,
                    "pages": [],
                    "extraction_notes": "",
                },
            },
        )
        source_refs = persona.setdefault("source_reference", {})
        pages = source_refs.setdefault("pages", [])
        if result.page_number not in pages:
            pages.append(result.page_number)
        if result.parsed and result.parsed.get("notes"):
            note = result.parsed["notes"]
            existing = source_refs.get("extraction_notes") or ""
            source_refs["extraction_notes"] = (
                f"{existing}\nPage {result.page_number}: {note}"
            ).strip()
        self._deep_merge(persona, result.patch, parent_path="")

    def _deep_merge(
        self, target: Dict[str, Any], incoming: Dict[str, Any], parent_path: str
    ) -> None:
        for key, value in incoming.items():
            path = f"{parent_path}.{key}" if parent_path else key
            if isinstance(value, dict):
                target.setdefault(key, {})
                if isinstance(target[key], dict):
                    self._deep_merge(target[key], value, path)
                else:
                    target[key] = value
            elif isinstance(value, list):
                strategy = self.merge_strategy.get(path, "append")
                target.setdefault(key, [])
                if strategy == "overwrite":
                    target[key] = value
                else:
                    existing = target.get(key, [])
                    merged = existing + value
                    seen = set()
                    deduped = []
                    for item in merged:
                        marker = (
                            json.dumps(item, sort_keys=True) if isinstance(item, dict) else item
                        )
                        if marker in seen:
                            continue
                        seen.add(marker)
                        deduped.append(item)
                    target[key] = deduped
            else:
                strategy = self.merge_strategy.get(path, "fill")
                if strategy == "overwrite" or target.get(key) in (None, "", [], {}):
                    target[key] = value

    def validate(self) -> Dict[str, List[str]]:
        invalid: Dict[str, List[str]] = {}
        for persona_id, payload in self.personas.items():
            try:
                PersonaProfileModel(**payload)
            except ValidationError as exc:
                invalid[persona_id] = [e.get("msg", str(e)) for e in exc.errors()]
        return invalid

    def write_outputs(
        self,
        output_path: Path,
        qa_report_path: Path,
        page_results: Sequence[PageExtractionResult],
    ) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        qa_report_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("w", encoding="utf-8") as f:
            json.dump(list(self.personas.values()), f, indent=2, ensure_ascii=False)
        qa_report = {
            "personas": list(self.personas.keys()),
            "validation_errors": self.validate(),
            "parse_failures": self.parse_failures,
            "pages_processed": [r.page_number for r in page_results],
            "pages_with_persona": [r.page_number for r in page_results if r.persona_id],
        }
        with qa_report_path.open("w", encoding="utf-8") as f:
            json.dump(qa_report, f, indent=2, ensure_ascii=False)
        logger.info(f"Wrote merged personas to {output_path}")
        logger.info(f"Wrote QA report to {qa_report_path}")
