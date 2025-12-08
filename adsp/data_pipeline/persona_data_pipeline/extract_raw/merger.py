"""Merge and validation utilities for persona extraction results. Merge together JSON results from individual pages into a single, coherent data structure."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from loguru import logger

from .models import PageExtractionResult


class PersonaMerger:
    def __init__(self, document_name: str, merge_strategy: Optional[Dict[str, str]] = None):
        self.document_name = document_name
        self.merge_strategy = merge_strategy or {}
        self.personas: Dict[str, Dict[str, Any]] = {}
        self.general_content: List[dict] = []
        self.pages: List[dict] = []
        self.parse_failures: List[dict] = []

    def apply_page_result(self, result: PageExtractionResult) -> None:
        """
        It takes a single PageExtractionResult and integrates its data into the main self.personas and self.general_content stores
        """
        if result.error:
            self.parse_failures.append(
                {"page": result.page_number, "error": result.error, "raw": result.raw_text}
            )
            return
        parsed: Dict[str, Any] = result.parsed or {}
        page_metadata = parsed.get("page_metadata") or {}
        self.pages.append({"page_number": result.page_number, **parsed})

        general_content = parsed.get("general_content")
        if general_content:
            self.general_content.append(
                {
                    "page_number": result.page_number,
                    "page_metadata": page_metadata,
                    "content": general_content,
                }
            )

        for persona_data in parsed.get("personas") or []:
            if not isinstance(persona_data, dict):
                continue
            persona_id = self._resolve_persona_id(persona_data, result.page_number)
            persona_data = {**persona_data, "persona_id": persona_id}
            self._stamp_indicator_sources(persona_data, result.page_number)
            persona = self.personas.setdefault(
                persona_id,
                {"persona_id": persona_id, "source_pages": [], "document": self.document_name},
            )
            self._deep_merge(persona, persona_data, parent_path="")
            self._attach_pages(persona, result.page_number, page_metadata)

    def _attach_pages(self, persona: Dict[str, Any], page_number: int, page_metadata: dict) -> None:
        pages = persona.setdefault("source_pages", [])
        if page_number not in pages:
            pages.append(page_number)
        related = page_metadata.get("related_page_numbers") if isinstance(page_metadata, dict) else None
        if isinstance(related, list):
            for num in related:
                try:
                    normalized = int(num)
                except Exception:
                    continue
                if normalized not in pages:
                    pages.append(normalized)

    def _resolve_persona_id(self, persona_data: Dict[str, Any], page_number: int) -> str:
        candidate = persona_data.get("persona_id") or persona_data.get("persona_name")
        if candidate:
            slug = self._slugify(str(candidate))
            if slug:
                return slug
        return f"persona-page-{page_number}-{len(self.personas) + 1}"

    @staticmethod
    def _slugify(text: str) -> str:
        cleaned = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
        cleaned = re.sub(r"-{2,}", "-", cleaned)
        return cleaned

    def _indicator_key(self, indicator: Any) -> Optional[str]:
        if not isinstance(indicator, dict):
            return None
        for candidate in ("id", "indicator_id", "label"):
            raw = indicator.get(candidate)
            if raw is None:
                continue
            try:
                text = str(raw).strip()
            except Exception:
                continue
            if text:
                return self._slugify(text)
        return None

    def _merge_indicator_lists(
        self, existing: List[Any], incoming: List[Any], path: str
    ) -> List[Any]:
        """
        A specialized function for merging lists of indicators. It can find indicators with the same ID/label and
        deep-merge their contents, rather than just appending duplicates
        """
        merged: List[Any] = []
        lookup: Dict[str, Dict[str, Any]] = {}
        seen_misc: set[Any] = set()

        def handle(item: Any) -> None:
            if not isinstance(item, dict):
                if isinstance(item, (int, float, str)):
                    marker = item
                else:
                    try:
                        marker = json.dumps(item, sort_keys=True)
                    except Exception:
                        marker = repr(item)
                if marker in seen_misc:
                    return
                seen_misc.add(marker)
                merged.append(item)
                return

            key = self._indicator_key(item)
            if key and key in lookup:
                self._deep_merge(lookup[key], item, path)
                return

            merged.append(item)
            if key:
                lookup[key] = item

        for item in existing:
            handle(item)
        for item in incoming:
            handle(item)
        return merged

    def _stamp_indicator_sources(self, persona_data: Dict[str, Any], page_number: int) -> None:
        indicators = persona_data.get("indicators")
        if not isinstance(indicators, list):
            return
        for indicator in indicators:
            if not isinstance(indicator, dict):
                continue
            sources = indicator.get("sources")
            if not isinstance(sources, list):
                sources = []
            updated_sources: List[Dict[str, Any]] = []
            for source in sources:
                if not isinstance(source, dict):
                    continue
                doc_id = source.get("doc_id")
                if not isinstance(doc_id, str) or not doc_id.strip():
                    source = {**source, "doc_id": self.document_name}
                pages = source.get("pages")
                if isinstance(pages, list):
                    if page_number not in pages:
                        source["pages"] = [*pages, page_number]
                else:
                    source["pages"] = [page_number]
                updated_sources.append(source)
            if updated_sources:
                indicator["sources"] = updated_sources
            else:
                indicator["sources"] = [{"doc_id": self.document_name, "pages": [page_number]}]

    def _deep_merge(
        self, target: Dict[str, Any], incoming: Dict[str, Any], parent_path: str
    ) -> None:
        """
        This is the core merging logic. It recursively traverses the incoming JSON from a new page and merges it into the
        existing target persona dictionary. It handles different data types (dicts, lists) and uses the merge_strategy from the config to
        decide whether to overwrite existing values, fill them if empty, or append to lists
        """
        for key, value in incoming.items():
            if key == "persona_id":
                continue
            path = f"{parent_path}.{key}" if parent_path else key
            if isinstance(value, dict):
                target.setdefault(key, {})
                if isinstance(target[key], dict):
                    self._deep_merge(target[key], value, path)
                else:
                    target[key] = value
            elif isinstance(value, list):
                strategy = self.merge_strategy.get(path, "append")
                if path.endswith("indicators") and strategy != "overwrite":
                    existing_list = target.get(key, [])
                    if not isinstance(existing_list, list):
                        existing_list = []
                    target[key] = self._merge_indicator_lists(existing_list, value, path)
                    continue
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
            if not payload.get("persona_name"):
                invalid.setdefault(persona_id, []).append("missing persona_name")
        return invalid

    def write_outputs(
        self,
        output_path: Path,
        qa_report_path: Path,
        page_results: Sequence[PageExtractionResult],
        persona_output_dir: Optional[Path] = None,
    ) -> None:
        """
        After all pages have been applied, this method writes the final merged data to several files: the main personas.json,
        individual files for each persona, and a qa_report.json that summarizes the extraction process (e.g., which pages failed to
        parse)
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        qa_report_path.parent.mkdir(parents=True, exist_ok=True)

        merged_payload = {
            "personas": list(self.personas.values()),
            "general_content": self.general_content,
            "pages": self.pages,
        }
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(merged_payload, f, indent=2, ensure_ascii=False)

        if persona_output_dir:
            persona_output_dir.mkdir(parents=True, exist_ok=True)
            for persona_id, payload in self.personas.items():
                out_path = persona_output_dir / f"{persona_id}.json"
                with out_path.open("w", encoding="utf-8") as pf:
                    json.dump(payload, pf, indent=2, ensure_ascii=False)
            logger.info(f"Wrote individual persona files to {persona_output_dir}")

        qa_report = {
            "personas": list(self.personas.keys()),
            "validation_errors": self.validate(),
            "parse_failures": self.parse_failures,
            "pages_processed": [r.page_number for r in page_results],
            "pages_with_persona": [
                r.page_number
                for r in page_results
                if r.parsed and isinstance(r.parsed.get("personas"), list) and r.parsed.get("personas")
            ],
        }
        with qa_report_path.open("w", encoding="utf-8") as f:
            json.dump(qa_report, f, indent=2, ensure_ascii=False)
        logger.info(f"Wrote merged persona bundle to {output_path}")
        logger.info(f"Wrote QA report to {qa_report_path}")
