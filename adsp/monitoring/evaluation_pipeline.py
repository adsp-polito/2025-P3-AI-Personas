"""Evaluation pipelines for persona extraction, fact extraction, retrieval, and authenticity."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .synonyms import WORD_SYNONYMS


_NON_WORD_RE = re.compile(r"[^\w\s]+")
_WHITESPACE_RE = re.compile(r"\s+")
_NUMBER_RE = re.compile(r"-?\d+(?:\.\d+)?")


def _normalize_text(text: str) -> str:
    cleaned = _NON_WORD_RE.sub(" ", text.lower())
    return _WHITESPACE_RE.sub(" ", cleaned).strip()


def _normalize_match_text(text: str) -> str:
    cleaned = _normalize_text(text)
    if not cleaned:
        return ""
    tokens = [WORD_SYNONYMS.get(token, token) for token in cleaned.split()]
    return " ".join(tokens)


def _word_overlap_ratio(left: str, right: str) -> float:
    left_words = set(_normalize_match_text(left).split())
    right_words = set(_normalize_match_text(right).split())
    if not left_words or not right_words:
        return 0.0
    shared = left_words & right_words
    return len(shared) / min(len(left_words), len(right_words))


def _parse_page_number(payload: Dict[str, Any]) -> Optional[int]:
    for key in ("page_number", "page", "page_id"):
        value = payload.get(key)
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            match = _NUMBER_RE.search(value)
            if match:
                return int(match.group(0))
    return None


def _safe_decimal(value: Any) -> Optional[Decimal]:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    if isinstance(value, str):
        match = _NUMBER_RE.search(value.replace(",", ""))
        if not match:
            return None
        try:
            return Decimal(match.group(0))
        except InvalidOperation:
            return None
    return None


def _normalize_persona_id(value: str) -> str:
    cleaned = _normalize_text(value)
    return cleaned.replace(" ", "-")


def _build_unit_synonyms() -> Dict[str, str]:
    groups = [
        ["%", "percentage"],
        ["index", "idx"],
        ["€", "euro", "eur"],
        ["$", "dollar", "usd"],
        ["£", "pound", "gbp"],
        ["¥", "yen", "jpy"],
        ["₹", "rupee", "inr"],
        ["₩", "won", "krw"],
        ["₽", "ruble", "rub"],
        ["₺", "lira", "try"],
        ["₫", "dong", "vnd"],
        ["₱", "peso", "php"],
        ["₦", "naira", "ngn"],
        ["₴", "hryvnia", "uah"],
        ["₡", "colon", "crc"],
        ["₲", "guarani", "pyg"],
        ["₵", "cedi", "ghc"],
        ["₸", "tenge", "kzt"],
        ["₼", "manat", "azn"],
    ]
    mapping: Dict[str, str] = {}
    for group in groups:
        canonical = group[0]
        for unit in group:
            mapping[unit.lower()] = canonical.lower()
    return mapping


_UNIT_SYNONYMS = _build_unit_synonyms()


def _normalize_unit(unit: Any) -> str:
    if unit is None:
        return ""
    cleaned = str(unit).strip().lower()
    if not cleaned:
        return ""
    cleaned = _WHITESPACE_RE.sub("", cleaned)
    return _UNIT_SYNONYMS.get(cleaned, cleaned)


@dataclass(frozen=True)
class _MetricEntry:
    indicator_label: str
    indicator_description: str
    statement_label: str
    statement_description: str
    value: Any
    unit: Any


def _indicator_matches(
    gt_label: str,
    sys_label: str,
    sys_description: str,
    threshold: float,
) -> bool:
    similarity = max(
        _word_overlap_ratio(gt_label, sys_label),
        _word_overlap_ratio(gt_label, sys_description),
    )
    return similarity >= threshold


def _statement_matches(
    gt_label: str,
    sys_label: str,
    sys_description: str,
    threshold: float,
) -> bool:
    similarity = max(
        _word_overlap_ratio(gt_label, sys_label),
        _word_overlap_ratio(gt_label, sys_description),
    )
    return similarity >= threshold


def _values_match(gt_value: Any, sys_value: Any) -> bool:
    gt_decimal = _safe_decimal(gt_value)
    sys_decimal = _safe_decimal(sys_value)
    if gt_decimal is not None and sys_decimal is not None:
        return gt_decimal == sys_decimal
    return _normalize_text(str(gt_value)) == _normalize_text(str(sys_value))


def _units_match(gt_unit: Any, sys_unit: Any) -> bool:
    normalized_gt = _normalize_unit(gt_unit)
    if not normalized_gt:
        return True
    return normalized_gt == _normalize_unit(sys_unit)


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_json_files(directory: Path) -> List[Dict[str, Any]]:
    return [_load_json(path) for path in sorted(directory.glob("*.json"))]


def _extract_persona_metrics(parsed: Dict[str, Any]) -> List[_MetricEntry]:
    metrics: List[_MetricEntry] = []
    for persona in parsed.get("personas", []) if isinstance(parsed, dict) else []:
        for indicator in persona.get("indicators", []) or []:
            indicator_label = indicator.get("label") or ""
            indicator_description = indicator.get("description") or ""
            for statement in indicator.get("statements", []) or []:
                statement_metrics = statement.get("metrics") or []
                if not statement_metrics:
                    continue
                statement_label = statement.get("label") or ""
                statement_description = statement.get("description") or ""
                for metric in statement_metrics:
                    metrics.append(
                        _MetricEntry(
                            indicator_label=indicator_label,
                            indicator_description=indicator_description,
                            statement_label=statement_label,
                            statement_description=statement_description,
                            value=metric.get("value"),
                            unit=metric.get("unit", ""),
                        )
                    )
    return metrics


def _extract_ground_truth_metrics(payload: Dict[str, Any]) -> List[_MetricEntry]:
    metrics: List[_MetricEntry] = []
    ground_truth = payload.get("ground_truth", {})
    for indicator in ground_truth.get("indicators", []) or []:
        indicator_label = indicator.get("label") or ""
        indicator_description = indicator.get("description") or ""
        for statement in indicator.get("statements", []) or []:
            statement_metrics = statement.get("metrics") or []
            if not statement_metrics:
                continue
            statement_label = statement.get("label") or ""
            statement_description = statement.get("description") or ""
            for metric in statement_metrics:
                metrics.append(
                    _MetricEntry(
                        indicator_label=indicator_label,
                        indicator_description=indicator_description,
                        statement_label=statement_label,
                        statement_description=statement_description,
                        value=metric.get("value"),
                        unit=metric.get("unit", ""),
                    )
                )
    return metrics


def _extract_persona_ids(parsed: Dict[str, Any]) -> List[str]:
    persona_ids: List[str] = []
    for persona in parsed.get("personas", []) if isinstance(parsed, dict) else []:
        persona_id = persona.get("persona_id")
        if not persona_id and persona.get("persona_name"):
            persona_id = _normalize_persona_id(persona["persona_name"])
        if persona_id:
            persona_ids.append(persona_id)
    return persona_ids


def _metric_entry_to_dict(entry: _MetricEntry) -> Dict[str, Any]:
    return {
        "indicator_label": entry.indicator_label,
        "indicator_description": entry.indicator_description,
        "statement_label": entry.statement_label,
        "statement_description": entry.statement_description,
        "value": entry.value,
        "unit": entry.unit,
    }


def _determine_mismatch_reason(
    gt_metric: _MetricEntry,
    system_metrics: List[_MetricEntry],
    threshold: float,
    used_indices: set[int],
) -> Tuple[str, str]:
    full_match_indices: List[int] = []
    for index, sys_metric in enumerate(system_metrics):
        if not _indicator_matches(
            gt_metric.indicator_label,
            sys_metric.indicator_label,
            sys_metric.indicator_description,
            threshold,
        ):
            continue
        if not _statement_matches(
            gt_metric.statement_label,
            sys_metric.statement_label,
            sys_metric.statement_description,
            threshold,
        ):
            continue
        if not _values_match(gt_metric.value, sys_metric.value):
            continue
        if not _units_match(gt_metric.unit, sys_metric.unit):
            continue
        full_match_indices.append(index)

    if full_match_indices and all(index in used_indices for index in full_match_indices):
        return "duplicate_match", "already_matched"

    indicator_candidates = [
        sys_metric
        for sys_metric in system_metrics
        if _indicator_matches(
            gt_metric.indicator_label,
            sys_metric.indicator_label,
            sys_metric.indicator_description,
            threshold,
        )
    ]
    if not indicator_candidates:
        return "indicator_match", "no_indicator_overlap"

    statement_candidates = [
        sys_metric
        for sys_metric in indicator_candidates
        if _statement_matches(
            gt_metric.statement_label,
            sys_metric.statement_label,
            sys_metric.statement_description,
            threshold,
        )
    ]
    if not statement_candidates:
        return "statement_match", "statement_overlap_below_threshold"

    value_candidates = [
        sys_metric
        for sys_metric in statement_candidates
        if _values_match(gt_metric.value, sys_metric.value)
    ]
    if not value_candidates:
        return "value_match", "value_mismatch"

    unit_candidates = [
        sys_metric
        for sys_metric in value_candidates
        if _units_match(gt_metric.unit, sys_metric.unit)
    ]
    if not unit_candidates:
        return "unit_match", "unit_mismatch"

    return "unknown", "unknown"


def _match_metrics_with_mismatches(
    ground_truth_metrics: List[_MetricEntry],
    system_metrics: List[_MetricEntry],
    threshold: float,
) -> Tuple[int, List[Dict[str, Any]], List[Dict[str, Any]]]:
    matched = 0
    used_indices: set[int] = set()
    unmatched_ground_truth: List[Dict[str, Any]] = []
    for gt_metric in ground_truth_metrics:
        matched_this = False
        for index, sys_metric in enumerate(system_metrics):
            if index in used_indices:
                continue
            if not _indicator_matches(
                gt_metric.indicator_label,
                sys_metric.indicator_label,
                sys_metric.indicator_description,
                threshold,
            ):
                continue
            if not _statement_matches(
                gt_metric.statement_label,
                sys_metric.statement_label,
                sys_metric.statement_description,
                threshold,
            ):
                continue
            if not _values_match(gt_metric.value, sys_metric.value):
                continue
            if not _units_match(gt_metric.unit, sys_metric.unit):
                continue
            matched += 1
            used_indices.add(index)
            matched_this = True
            break
        if not matched_this:
            mismatch_step, mismatch_reason = _determine_mismatch_reason(
                gt_metric,
                system_metrics,
                threshold,
                used_indices,
            )
            unmatched_ground_truth.append(
                {
                    **_metric_entry_to_dict(gt_metric),
                    "mismatch_step": mismatch_step,
                    "mismatch_reason": mismatch_reason,
                }
            )

    unmatched_system = []
    for index, sys_metric in enumerate(system_metrics):
        if index in used_indices:
            continue
        unmatched_system.append(
            {
                **_metric_entry_to_dict(sys_metric),
                "mismatch_step": "extra_extraction",
                "mismatch_reason": "no_ground_truth_match",
            }
        )
    return matched, unmatched_ground_truth, unmatched_system


@dataclass
class PersonaExtractionEvaluator:
    ground_truth_dir: Path
    system_output_path: Path
    word_overlap_threshold: float = 0.5

    def _load_ground_truth(self) -> List[Dict[str, Any]]:
        pages: List[Dict[str, Any]] = []
        for payload in _load_json_files(self.ground_truth_dir):
            if "ground_truth" in payload and _parse_page_number(payload) is not None:
                pages.append(payload)
        return pages

    def _load_system_output(self) -> Dict[int, Dict[str, Any]]:
        payloads: List[Dict[str, Any]] = []
        if self.system_output_path.is_dir():
            payloads = _load_json_files(self.system_output_path)
        elif self.system_output_path.is_file():
            payload = _load_json(self.system_output_path)
            if isinstance(payload, list):
                payloads = payload
            elif isinstance(payload, dict):
                for key in ("pages", "page_results"):
                    if isinstance(payload.get(key), list):
                        payloads = payload[key]
                        break
        pages: Dict[int, Dict[str, Any]] = {}
        for payload in payloads:
            if not isinstance(payload, dict):
                continue
            page_number = _parse_page_number(payload)
            parsed = payload.get("parsed") if isinstance(payload, dict) else None
            if page_number is None or not isinstance(parsed, dict):
                continue
            pages[page_number] = parsed
        return pages

    def run_evaluation(self) -> Dict[str, Any]:
        ground_truth_pages = self._load_ground_truth()
        system_pages = self._load_system_output()

        total_personas = 0
        detected_personas = 0
        total_ground_truth_metrics = 0
        total_system_metrics = 0
        matched_metrics = 0
        mismatched_ground_truth_metrics: List[Dict[str, Any]] = []
        mismatched_system_metrics: List[Dict[str, Any]] = []

        for gt_page in ground_truth_pages:
            page_number = _parse_page_number(gt_page)
            if page_number is None:
                continue
            gt_personas = set(gt_page.get("ground_truth", {}).get("personas", []))
            total_personas += len(gt_personas)

            system_parsed = system_pages.get(page_number, {})
            sys_personas = set(_extract_persona_ids(system_parsed))
            detected_personas += len(gt_personas & sys_personas)

            gt_metrics = _extract_ground_truth_metrics(gt_page)
            sys_metrics = _extract_persona_metrics(system_parsed)

            total_ground_truth_metrics += len(gt_metrics)
            total_system_metrics += len(sys_metrics)
            matched, gt_mismatches, sys_mismatches = _match_metrics_with_mismatches(
                gt_metrics, sys_metrics, self.word_overlap_threshold
            )
            matched_metrics += matched
            for entry in gt_mismatches:
                mismatched_ground_truth_metrics.append(
                    {"page": page_number, **entry}
                )
            for entry in sys_mismatches:
                mismatched_system_metrics.append(
                    {"page": page_number, **entry}
                )

        persona_detection_rate = (
            detected_personas / total_personas if total_personas > 0 else 0.0
        )
        metrics_recall = (
            matched_metrics / total_ground_truth_metrics
            if total_ground_truth_metrics > 0
            else 0.0
        )
        metrics_precision = (
            matched_metrics / total_system_metrics if total_system_metrics > 0 else 0.0
        )

        return {
            "persona_detection_rate": persona_detection_rate,
            "metrics_recall": metrics_recall,
            "metrics_precision": metrics_precision,
            "counts": {
                "ground_truth_personas": total_personas,
                "detected_personas": detected_personas,
                "ground_truth_metrics": total_ground_truth_metrics,
                "system_metrics": total_system_metrics,
                "matched_metrics": matched_metrics,
                "mismatched_ground_truth_metrics": len(mismatched_ground_truth_metrics),
                "mismatched_system_metrics": len(mismatched_system_metrics),
            },
            "mismatched_ground_truth_metrics": mismatched_ground_truth_metrics,
            "mismatched_system_metrics": mismatched_system_metrics,
        }


def _extract_markdown_numbers(text: str) -> List[Decimal]:
    numbers: List[Decimal] = []
    for match in _NUMBER_RE.finditer(text.replace(",", "")):
        try:
            numbers.append(Decimal(match.group(0)))
        except InvalidOperation:
            continue
    return numbers


def _extract_fact_values_from_json(payload: List[Dict[str, Any]]) -> Dict[int, List[Decimal]]:
    values: Dict[int, List[Decimal]] = {}
    for entry in payload:
        if not isinstance(entry, dict):
            continue
        page_number = entry.get("page_number")
        if page_number is None:
            continue
        page_values = values.setdefault(int(page_number), [])
        for fact in entry.get("facts", []) or []:
            number = _safe_decimal(fact.get("value"))
            if number is not None:
                page_values.append(number)
    return values


@dataclass
class FactExtractionEvaluator:
    ground_truth_file: Path
    system_output_path: Path

    def _normalize_ground_truth_payload(self, payload: Any) -> List[Dict[str, Any]]:
        if isinstance(payload, list):
            return [entry for entry in payload if isinstance(entry, dict)]
        if isinstance(payload, dict):
            if "page_number" in payload:
                return [payload]
            facts = payload.get("facts")
            if isinstance(facts, list):
                return [entry for entry in facts if isinstance(entry, dict)]
            return [payload]
        return []

    def _load_ground_truth(self) -> List[Dict[str, Any]]:
        if self.ground_truth_file.is_dir():
            entries: List[Dict[str, Any]] = []
            for payload in _load_json_files(self.ground_truth_file):
                entries.extend(self._normalize_ground_truth_payload(payload))
            return entries

        payload = _load_json(self.ground_truth_file)
        return self._normalize_ground_truth_payload(payload)

    def _load_system_values(self) -> Tuple[Dict[int, List[Decimal]], str]:
        if self.system_output_path.is_dir():
            markdown_files = list(self.system_output_path.glob("*.md"))
            if markdown_files:
                values = {
                    int(_NUMBER_RE.search(path.stem).group(0)): _extract_markdown_numbers(
                        path.read_text(encoding="utf-8")
                    )
                    for path in markdown_files
                    if _NUMBER_RE.search(path.stem)
                }
                return values, "markdown"
            json_files = list(self.system_output_path.glob("*.json"))
            if json_files:
                payloads = _load_json_files(self.system_output_path)
                merged: Dict[int, List[Decimal]] = {}
                for payload in payloads:
                    if isinstance(payload, list):
                        for page, numbers in _extract_fact_values_from_json(payload).items():
                            merged.setdefault(page, []).extend(numbers)
                return merged, "json"
            return {}, "unknown"

        if self.system_output_path.suffix.lower() == ".md":
            page_number = int(_NUMBER_RE.search(self.system_output_path.stem).group(0))
            return {
                page_number: _extract_markdown_numbers(
                    self.system_output_path.read_text(encoding="utf-8")
                )
            }, "markdown"

        payload = _load_json(self.system_output_path)
        if isinstance(payload, list):
            return _extract_fact_values_from_json(payload), "json"
        if isinstance(payload, dict) and isinstance(payload.get("results"), list):
            return _extract_fact_values_from_json(payload["results"]), "json"
        return {}, "unknown"

    def run_evaluation(self) -> Dict[str, Any]:
        ground_truth = self._load_ground_truth()
        system_values, source = self._load_system_values()

        total_values = 0
        matched_values = 0
        details: List[Dict[str, Any]] = []

        for entry in ground_truth:
            if not isinstance(entry, dict):
                continue
            page_number = entry.get("page_number")
            if page_number is None:
                continue
            page_number = int(page_number)
            extracted_numbers = system_values.get(page_number, [])
            extracted_set = set(extracted_numbers)

            for fact in entry.get("facts", []) or []:
                total_values += 1
                gt_value = fact.get("value")
                gt_number = _safe_decimal(gt_value)
                matched = False
                if gt_number is not None:
                    matched = gt_number in extracted_set
                else:
                    matched = _normalize_text(str(gt_value)) in _normalize_text(
                        " ".join(str(value) for value in extracted_numbers)
                    )
                if matched:
                    matched_values += 1
                mismatch_reason = None if matched else "value_not_found"
                details.append(
                    {
                        "page": page_number,
                        "attribute": fact.get("attribute"),
                        "ground_truth_value": gt_value,
                        "matched": matched,
                        "mismatch_reason": mismatch_reason,
                    }
                )

        accuracy = matched_values / total_values if total_values > 0 else 0.0
        mismatched_values = [detail for detail in details if not detail["matched"]]
        return {
            "exact_match_accuracy": accuracy,
            "total_values": total_values,
            "matched_values": matched_values,
            "mismatched_values": mismatched_values,
            "system_source": source,
            "details": details,
        }


@dataclass
class RAGRetrievalEvaluator:
    queries_file: Path
    retrieval_results_file: Optional[Path] = None
    k_values: Sequence[int] = (3, 5, 10, 20)

    def _load_queries(self) -> List[Dict[str, Any]]:
        payload = _load_json(self.queries_file)
        if isinstance(payload, dict) and isinstance(payload.get("test_queries"), list):
            return payload["test_queries"]
        return payload

    def _load_retrieval_results(self) -> Dict[str, List[Any]]:
        if not self.retrieval_results_file:
            return {}
        payload = _load_json(self.retrieval_results_file)
        if isinstance(payload, dict) and isinstance(payload.get("results"), list):
            payload = payload["results"]
        results: Dict[str, List[Any]] = {}
        if isinstance(payload, list):
            for entry in payload:
                if not isinstance(entry, dict):
                    continue
                query_id = entry.get("query_id")
                if not query_id:
                    continue
                retrieved = None
                for key in ("retrieved_indicators", "retrieved_docs", "retrieved_documents"):
                    if key in entry:
                        retrieved = entry.get(key)
                        break
                if isinstance(retrieved, list):
                    results[str(query_id)] = retrieved
        return results

    def _get_relevant_ids(self, query: Dict[str, Any]) -> List[Any]:
        if isinstance(query.get("relevant_indicators"), list):
            return query["relevant_indicators"]
        relevance_scores = query.get("relevance_scores")
        if isinstance(relevance_scores, dict):
            return [key for key, score in relevance_scores.items() if score]
        return []

    def _compute_metrics_for_list(
        self,
        retrieved: List[Any],
        relevant_ids: Sequence[Any],
    ) -> Dict[int, Tuple[float, float]]:
        relevant_set = set(relevant_ids)
        metrics: Dict[int, Tuple[float, float]] = {}
        for k in self.k_values:
            top_k = retrieved[:k]
            hits = sum(1 for item in top_k if item in relevant_set)
            denom = min(k, len(retrieved)) if retrieved else 0
            precision = hits / denom if denom else 0.0
            recall = hits / len(relevant_set) if relevant_set else 0.0
            metrics[k] = (precision, recall)
        return metrics

    def run_evaluation(self) -> Dict[str, Any]:
        queries = self._load_queries()
        retrieval_results = self._load_retrieval_results()

        totals = {k: {"precision": 0.0, "recall": 0.0} for k in self.k_values}
        details: List[Dict[str, Any]] = []
        evaluated = 0
        max_k = max(self.k_values) if self.k_values else 0
        missing_relevant_total = 0
        irrelevant_retrieved_total = 0

        for query in queries:
            if not isinstance(query, dict):
                continue
            query_id = str(query.get("query_id") or "")
            relevant_docs = query.get("relevant_docs")

            if isinstance(relevant_docs, list) and not retrieval_results:
                retrieved = [doc.get("page_content", idx) for idx, doc in enumerate(relevant_docs)]
                relevant_ids = [
                    retrieved[idx]
                    for idx, doc in enumerate(relevant_docs)
                    if doc.get("relevance") == 1 or doc.get("relevance_label") == 1
                ]
            else:
                retrieved = retrieval_results.get(query_id, [])
                relevant_ids = self._get_relevant_ids(query)

            if not retrieved:
                continue

            metrics = self._compute_metrics_for_list(retrieved, relevant_ids)
            evaluated += 1
            detail_entry = {"query_id": query_id, "query": query.get("query")}
            for k, (precision, recall) in metrics.items():
                totals[k]["precision"] += precision
                totals[k]["recall"] += recall
                detail_entry[f"precision_at_{k}"] = precision
                detail_entry[f"recall_at_{k}"] = recall
            relevant_set = set(relevant_ids)
            retrieved_slice = retrieved[:max_k] if max_k else retrieved
            missing_relevant = [item for item in relevant_set if item not in retrieved_slice]
            irrelevant_retrieved = [
                item for item in retrieved_slice if item not in relevant_set
            ]
            detail_entry["missing_relevant"] = missing_relevant
            detail_entry["irrelevant_retrieved"] = irrelevant_retrieved
            missing_relevant_total += len(missing_relevant)
            irrelevant_retrieved_total += len(irrelevant_retrieved)
            details.append(detail_entry)

        averages = {
            f"precision_at_{k}": (totals[k]["precision"] / evaluated if evaluated else 0.0)
            for k in self.k_values
        }
        averages.update(
            {
                f"recall_at_{k}": (totals[k]["recall"] / evaluated if evaluated else 0.0)
                for k in self.k_values
            }
        )
        return {
            **averages,
            "total_queries": evaluated,
            "query_details": details,
            "missing_relevant_total": missing_relevant_total,
            "irrelevant_retrieved_total": irrelevant_retrieved_total,
            "max_k": max_k,
        }


@dataclass
class AuthenticityEvaluator:
    evaluations_file: Path

    def _normalize_evaluations_payload(self, payload: Any) -> List[Dict[str, Any]]:
        if isinstance(payload, dict) and isinstance(payload.get("test_questions"), list):
            return [entry for entry in payload["test_questions"] if isinstance(entry, dict)]
        if isinstance(payload, list):
            return [entry for entry in payload if isinstance(entry, dict)]
        if isinstance(payload, dict):
            return [payload]
        return []

    def _load_evaluations(self) -> List[Dict[str, Any]]:
        if self.evaluations_file.is_dir():
            entries: List[Dict[str, Any]] = []
            for payload in _load_json_files(self.evaluations_file):
                entries.extend(self._normalize_evaluations_payload(payload))
            return entries

        payload = _load_json(self.evaluations_file)
        return self._normalize_evaluations_payload(payload)

    def _extract_score(self, rating: Any) -> Optional[float]:
        if isinstance(rating, (int, float)):
            return float(rating)
        if isinstance(rating, dict):
            if isinstance(rating.get("score"), (int, float)):
                return float(rating["score"])
            criteria = rating.get("criteria")
            if isinstance(criteria, list) and criteria:
                scores = [
                    item.get("score")
                    for item in criteria
                    if isinstance(item.get("score"), (int, float))
                ]
                if scores:
                    return sum(scores) / len(scores)
        return None

    def _extract_factual_score(self, ratings: Dict[str, Any]) -> Optional[float]:
        factual_rating = ratings.get("factual_grounding", {})
        if isinstance(factual_rating, dict) and isinstance(
            factual_rating.get("factually_accurate"), bool
        ):
            return 1.0 if factual_rating["factually_accurate"] else 0.0
        return self._extract_score(factual_rating)

    def run_evaluation(self) -> Dict[str, Any]:
        evaluations = self._load_evaluations()

        total = 0
        authenticity_scores: List[float] = []
        style_scores: List[float] = []
        factual_scores: List[float] = []
        persona_buckets: Dict[str, Dict[str, List[float]]] = {}
        persona_totals: Dict[str, int] = {}

        for evaluation in evaluations:
            if not isinstance(evaluation, dict):
                continue
            ratings = evaluation.get("ratings", {})
            if not isinstance(ratings, dict):
                ratings = {}

            authenticity_score = self._extract_score(ratings.get("authenticity"))
            if authenticity_score is not None:
                authenticity_scores.append(authenticity_score)

            style_score = self._extract_score(ratings.get("style_alignment"))
            if style_score is not None:
                style_scores.append(style_score)

            factual_score = self._extract_factual_score(ratings)
            if factual_score is not None:
                factual_scores.append(factual_score)

            persona_id = evaluation.get("persona_id")
            if isinstance(persona_id, str) and persona_id:
                if persona_id not in persona_buckets:
                    persona_buckets[persona_id] = {
                        "authenticity": [],
                        "style_alignment": [],
                        "factual_grounding": [],
                    }
                    persona_totals[persona_id] = 0
                persona_totals[persona_id] += 1
                if authenticity_score is not None:
                    persona_buckets[persona_id]["authenticity"].append(authenticity_score)
                if style_score is not None:
                    persona_buckets[persona_id]["style_alignment"].append(style_score)
                if factual_score is not None:
                    persona_buckets[persona_id]["factual_grounding"].append(factual_score)
            total += 1

        avg_authenticity = (
            sum(authenticity_scores) / len(authenticity_scores)
            if authenticity_scores
            else 0.0
        )
        style_alignment = sum(style_scores) / len(style_scores) if style_scores else 0.0
        factual_grounding = sum(factual_scores) / len(factual_scores) if factual_scores else 0.0

        persona_scores: Dict[str, Dict[str, float]] = {}
        for persona_id, buckets in persona_buckets.items():
            persona_scores[persona_id] = {
                "authenticity": (
                    sum(buckets["authenticity"]) / len(buckets["authenticity"])
                    if buckets["authenticity"]
                    else 0.0
                ),
                "style_alignment": (
                    sum(buckets["style_alignment"]) / len(buckets["style_alignment"])
                    if buckets["style_alignment"]
                    else 0.0
                ),
                "factual_grounding": (
                    sum(buckets["factual_grounding"]) / len(buckets["factual_grounding"])
                    if buckets["factual_grounding"]
                    else 0.0
                ),
                "total_evaluations": persona_totals.get(persona_id, 0),
            }

        return {
            "expert_authenticity_score": avg_authenticity,
            "style_alignment_score": style_alignment,
            "factual_grounding_score": factual_grounding,
            "total_evaluations": total,
            "persona_scores": persona_scores,
        }
