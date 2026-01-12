"""
Tests for monitoring and evaluation helpers.
"""

import json
from decimal import Decimal
from pathlib import Path

from adsp.monitoring.evaluation import EvaluationSuite
from adsp.monitoring.evaluation_pipeline import (
    AuthenticityEvaluator,
    FactExtractionEvaluator,
    PersonaExtractionEvaluator,
    RAGRetrievalEvaluator,
    _MetricEntry,
    _determine_mismatch_reason,
    _extract_ground_truth_metrics,
    _extract_persona_ids,
    _extract_persona_metrics,
    _ground_truth_word_coverage,
    _indicator_matches,
    _match_metrics_with_mismatches,
    _normalize_match_text,
    _normalize_persona_id,
    _normalize_text,
    _normalize_unit,
    _parse_page_number,
    _safe_decimal,
    _statement_matches,
    _tokenize_words,
    _units_match,
    _values_match,
    _word_overlap_ratio,
)
from adsp.monitoring.metrics import MetricsCollector
from adsp.monitoring.synonyms import WORD_SYNONYMS


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_metrics_collector_increments():
    metrics = MetricsCollector()
    metrics.incr("hits")
    metrics.incr("hits", 2.5)
    assert metrics.read("hits") == 3.5


def test_metrics_collector_write_overrides_value():
    metrics = MetricsCollector()
    metrics.incr("latency", 5)
    metrics.write("latency", 2)
    assert metrics.read("latency") == 2


def test_metrics_collector_read_missing_returns_zero():
    metrics = MetricsCollector()
    assert metrics.read("missing") == 0.0


def test_evaluation_suite_runs_checks():
    def check_length(response: str) -> bool:
        return len(response) > 3

    def check_contains(response: str) -> bool:
        return "ok" in response

    suite = EvaluationSuite(checks=[check_length, check_contains])
    result = suite.run("ok fine")
    assert result == {"check_length": True, "check_contains": True}


def test_evaluation_suite_empty_checks():
    suite = EvaluationSuite()
    assert suite.run("anything") == {}


def test_normalize_text_strips_punctuation_and_case():
    assert _normalize_text("Hello, World!") == "hello world"


def test_normalize_text_collapses_whitespace():
    assert _normalize_text("A\n\nB\tC") == "a b c"


def test_normalize_match_text_applies_synonyms():
    assert _normalize_match_text("USD price") == "$ price"


def test_word_overlap_ratio_basic():
    assert _word_overlap_ratio("price is low", "price range") == 0.5


def test_tokenize_words_returns_clean_words():
    assert _tokenize_words("Hello, world!") == ["hello", "world"]


def test_ground_truth_word_coverage_matches():
    coverage = _ground_truth_word_coverage("low price", "price is low and fair")
    assert coverage == 1.0


def test_parse_page_number_from_string():
    assert _parse_page_number({"page_number": "page 12"}) == 12


def test_safe_decimal_from_string():
    assert _safe_decimal("USD 2,500") == Decimal("2500")


def test_normalize_persona_id_replaces_spaces():
    assert _normalize_persona_id("My Persona") == "my-persona"


def test_normalize_unit_maps_symbols():
    assert _normalize_unit("USD") == "$"


def test_indicator_matches_with_description_overlap():
    assert _indicator_matches("price", "", "price range", 0.5) is True


def test_statement_matches_basic():
    assert _statement_matches("value", "value", "", 0.5) is True
    assert _statement_matches("value", "quality", "", 0.5) is False


def test_values_match_numeric():
    assert _values_match("2", 2.0) is True
    assert _values_match("3", 4) is False


def test_units_match_symbol_equivalence():
    assert _units_match("USD", "$") is True


def test_extract_persona_ids_from_parsed_payload():
    payload = {
        "personas": [
            {"persona_id": "p1"},
            {"persona_name": "Persona Two"},
        ]
    }
    assert _extract_persona_ids(payload) == ["p1", "persona-two"]


def test_extract_ground_truth_metrics_basic():
    payload = {
        "ground_truth": {
            "indicators": [
                {
                    "label": "Price",
                    "description": "Cost",
                    "statements": [
                        {
                            "label": "Budget",
                            "description": "Low",
                            "metrics": [{"value": 10, "unit": "$"}],
                        }
                    ],
                }
            ]
        }
    }
    metrics = _extract_ground_truth_metrics(payload)
    assert len(metrics) == 1
    assert metrics[0].indicator_label == "Price"
    assert metrics[0].statement_label == "Budget"
    assert metrics[0].unit == "$"


def test_extract_persona_metrics_from_parsed_payload():
    parsed = {
        "personas": [
            {
                "persona_id": "p1",
                "indicators": [
                    {
                        "label": "Service",
                        "description": "Quality",
                        "statements": [
                            {
                                "label": "Speed",
                                "description": "Fast",
                                "metrics": [{"value": 5, "unit": "%"}],
                            }
                        ],
                    }
                ],
            }
        ]
    }
    metrics = _extract_persona_metrics(parsed)
    assert len(metrics) == 1
    assert metrics[0].indicator_label == "Service"
    assert metrics[0].statement_label == "Speed"
    assert metrics[0].unit == "%"


def test_match_metrics_with_mismatches_value_mismatch():
    ground_truth = _extract_ground_truth_metrics(
        {
            "ground_truth": {
                "indicators": [
                    {
                        "label": "Price",
                        "description": "Cost",
                        "statements": [
                            {
                                "label": "Budget",
                                "description": "Low",
                                "metrics": [{"value": 10, "unit": "$"}],
                            }
                        ],
                    }
                ]
            }
        }
    )
    system = _extract_persona_metrics(
        {
            "personas": [
                {
                    "indicators": [
                        {
                            "label": "Price",
                            "description": "Cost",
                            "statements": [
                                {
                                    "label": "Budget",
                                    "description": "Low",
                                    "metrics": [{"value": 12, "unit": "$"}],
                                }
                            ],
                        }
                    ]
                }
            ]
        }
    )
    matched, gt_miss, sys_miss = _match_metrics_with_mismatches(ground_truth, system, 0.5)
    assert matched == 0
    assert len(gt_miss) == 1
    assert gt_miss[0]["mismatch_step"] == "value_match"
    assert len(sys_miss) == 1


def test_determine_mismatch_reason_unit_mismatch():
    gt_metric = _MetricEntry(
        indicator_label="Price",
        indicator_description="Cost",
        statement_label="Budget",
        statement_description="Low",
        value=10,
        unit="$",
    )
    sys_metric = _MetricEntry(
        indicator_label="Price",
        indicator_description="Cost",
        statement_label="Budget",
        statement_description="Low",
        value=10,
        unit="%",
    )
    mismatch_step, reason = _determine_mismatch_reason(gt_metric, [sys_metric], 0.5, set())
    assert mismatch_step == "unit_match"
    assert reason == "unit_mismatch"


def test_persona_extraction_evaluator_basic(tmp_path: Path):
    ground_truth_dir = tmp_path / "gt"
    ground_truth_dir.mkdir()
    system_output = tmp_path / "system.json"

    gt_payload = {
        "page_number": 1,
        "ground_truth": {
            "personas": ["p1"],
            "indicators": [
                {
                    "label": "Price",
                    "description": "Cost",
                    "statements": [
                        {
                            "label": "Budget",
                            "description": "Low",
                            "metrics": [{"value": 10, "unit": "$"}],
                        }
                    ],
                }
            ],
        },
    }
    _write_json(ground_truth_dir / "page_1.json", gt_payload)

    system_payload = [
        {
            "page_number": 1,
            "parsed": {
                "personas": [
                    {
                        "persona_id": "p1",
                        "indicators": [
                            {
                                "label": "Price",
                                "description": "Cost",
                                "statements": [
                                    {
                                        "label": "Budget",
                                        "description": "Low",
                                        "metrics": [{"value": 10, "unit": "USD"}],
                                    }
                                ],
                            }
                        ],
                    }
                ]
            },
        }
    ]
    _write_json(system_output, system_payload)

    evaluator = PersonaExtractionEvaluator(
        ground_truth_dir=ground_truth_dir,
        system_output_path=system_output,
        word_overlap_threshold=0.5,
    )
    result = evaluator.run_evaluation()
    assert result["counts"]["ground_truth_personas"] == 1
    assert result["counts"]["detected_personas"] == 1
    assert result["counts"]["matched_metrics"] == 1


def test_fact_extraction_evaluator_markdown(tmp_path: Path):
    ground_truth_file = tmp_path / "gt.json"
    system_dir = tmp_path / "pages"
    system_dir.mkdir()

    payload = [
        {
            "page_number": 1,
            "facts": [
                {"attribute": "price", "value": "low"},
                {"attribute": "origin", "value": "italy"},
            ],
        }
    ]
    _write_json(ground_truth_file, payload)

    page_file = system_dir / "page_1.md"
    page_file.write_text("Price is low. Origin is Italy.", encoding="utf-8")

    evaluator = FactExtractionEvaluator(
        ground_truth_file=ground_truth_file,
        system_output_path=system_dir,
    )
    result = evaluator.run_evaluation()
    assert result["total_values"] == 2
    assert result["matched_values"] == 2
    assert result["system_source"] == "markdown"


def test_rag_retrieval_evaluator_uses_relevant_docs(tmp_path: Path):
    queries_file = tmp_path / "queries.json"
    payload = [
        {
            "query_id": "q1",
            "query": "price",
            "relevant_docs": [
                {"page_content": "doc1", "relevance": 1},
                {"page_content": "doc2", "relevance": 0},
            ],
        }
    ]
    _write_json(queries_file, payload)

    evaluator = RAGRetrievalEvaluator(queries_file=queries_file, k_values=(1, 2))
    result = evaluator.run_evaluation()
    assert result["total_queries"] == 1
    assert result["precision_at_1"] == 1.0
    assert result["recall_at_2"] == 1.0


def test_authenticity_evaluator_scores(tmp_path: Path):
    eval_file = tmp_path / "eval.json"
    payload = [
        {
            "persona_id": "p1",
            "ratings": {
                "authenticity": {"score": 4},
                "style_alignment": {"score": 3},
                "factual_grounding": {"factually_accurate": True},
            },
        },
        {
            "persona_id": "p1",
            "ratings": {
                "authenticity": {"score": 2},
                "style_alignment": {"score": 4},
                "factual_grounding": {"factually_accurate": False},
            },
        },
    ]
    _write_json(eval_file, payload)

    evaluator = AuthenticityEvaluator(evaluations_file=eval_file)
    result = evaluator.run_evaluation()
    assert result["total_evaluations"] == 2
    assert result["persona_scores"]["p1"]["total_evaluations"] == 2
    assert result["expert_authenticity_score"] == 3.0
    assert result["factual_grounding_score"] == 0.5


def test_word_synonyms_contains_capsule_variants():
    assert WORD_SYNONYMS["cap"] == "capsule"
    assert WORD_SYNONYMS["caps"] == "capsule"
    assert WORD_SYNONYMS["capsule"] == "capsule"
    assert WORD_SYNONYMS["capsules"] == "capsule"


def test_normalize_text_empty_returns_empty():
    assert _normalize_text("") == ""


def test_word_overlap_ratio_handles_empty():
    assert _word_overlap_ratio("", "something") == 0.0
    assert _word_overlap_ratio("value", "") == 0.0


def test_ground_truth_word_coverage_partial():
    coverage = _ground_truth_word_coverage("low price", "price is fair")
    assert coverage == 0.5


def test_parse_page_number_missing_returns_none():
    assert _parse_page_number({"page_id": None}) is None


def test_safe_decimal_invalid_string_returns_none():
    assert _safe_decimal("none") is None


def test_normalize_unit_unknown_kept():
    assert _normalize_unit("custom") == "custom"


def test_units_match_when_ground_truth_empty():
    assert _units_match("", "usd") is True


def test_units_match_mismatch():
    assert _units_match("%", "usd") is False


def test_extract_ground_truth_metrics_handles_empty():
    metrics = _extract_ground_truth_metrics({"ground_truth": {"indicators": []}})
    assert metrics == []


def test_match_metrics_with_mismatches_full_match():
    ground_truth = _extract_ground_truth_metrics(
        {
            "ground_truth": {
                "indicators": [
                    {
                        "label": "Price",
                        "description": "Cost",
                        "statements": [
                            {
                                "label": "Budget",
                                "description": "Low",
                                "metrics": [{"value": 10, "unit": "$"}],
                            }
                        ],
                    }
                ]
            }
        }
    )
    system = _extract_persona_metrics(
        {
            "personas": [
                {
                    "indicators": [
                        {
                            "label": "Price",
                            "description": "Cost",
                            "statements": [
                                {
                                    "label": "Budget",
                                    "description": "Low",
                                    "metrics": [{"value": 10, "unit": "USD"}],
                                }
                            ],
                        }
                    ]
                }
            ]
        }
    )
    matched, gt_miss, sys_miss = _match_metrics_with_mismatches(ground_truth, system, 0.5)
    assert matched == 1
    assert gt_miss == []
    assert sys_miss == []


def test_match_metrics_with_mismatches_indicator_mismatch():
    ground_truth = _extract_ground_truth_metrics(
        {
            "ground_truth": {
                "indicators": [
                    {
                        "label": "Price",
                        "description": "Cost",
                        "statements": [
                            {
                                "label": "Budget",
                                "description": "Low",
                                "metrics": [{"value": 10, "unit": "$"}],
                            }
                        ],
                    }
                ]
            }
        }
    )
    system = _extract_persona_metrics(
        {
            "personas": [
                {
                    "indicators": [
                        {
                            "label": "Taste",
                            "description": "Flavor",
                            "statements": [
                                {
                                    "label": "Rich",
                                    "description": "Strong",
                                    "metrics": [{"value": 10, "unit": "$"}],
                                }
                            ],
                        }
                    ]
                }
            ]
        }
    )
    matched, gt_miss, sys_miss = _match_metrics_with_mismatches(ground_truth, system, 0.5)
    assert matched == 0
    assert gt_miss[0]["mismatch_step"] == "indicator_match"
    assert sys_miss[0]["mismatch_step"] == "extra_extraction"


def test_match_metrics_with_mismatches_duplicate_match():
    ground_truth = _extract_ground_truth_metrics(
        {
            "ground_truth": {
                "indicators": [
                    {
                        "label": "Price",
                        "description": "Cost",
                        "statements": [
                            {
                                "label": "Budget",
                                "description": "Low",
                                "metrics": [
                                    {"value": 10, "unit": "$"},
                                    {"value": 10, "unit": "$"},
                                ],
                            }
                        ],
                    }
                ]
            }
        }
    )
    system = _extract_persona_metrics(
        {
            "personas": [
                {
                    "indicators": [
                        {
                            "label": "Price",
                            "description": "Cost",
                            "statements": [
                                {
                                    "label": "Budget",
                                    "description": "Low",
                                    "metrics": [{"value": 10, "unit": "$"}],
                                }
                            ],
                        }
                    ]
                }
            ]
        }
    )
    matched, gt_miss, sys_miss = _match_metrics_with_mismatches(ground_truth, system, 0.5)
    assert matched == 1
    assert len(gt_miss) == 1
    assert gt_miss[0]["mismatch_step"] == "duplicate_match"
    assert sys_miss == []


def test_determine_mismatch_reason_value_mismatch():
    gt_metric = _MetricEntry(
        indicator_label="Price",
        indicator_description="Cost",
        statement_label="Budget",
        statement_description="Low",
        value=10,
        unit="$",
    )
    sys_metric = _MetricEntry(
        indicator_label="Price",
        indicator_description="Cost",
        statement_label="Budget",
        statement_description="Low",
        value=12,
        unit="$",
    )
    mismatch_step, reason = _determine_mismatch_reason(gt_metric, [sys_metric], 0.5, set())
    assert mismatch_step == "value_match"
    assert reason == "value_mismatch"


def test_persona_extraction_evaluator_handles_missing_pages(tmp_path: Path):
    ground_truth_dir = tmp_path / "gt"
    ground_truth_dir.mkdir()
    system_output = tmp_path / "system.json"

    gt_payload = {
        "page_number": 1,
        "ground_truth": {"personas": ["p1"], "indicators": []},
    }
    _write_json(ground_truth_dir / "page_1.json", gt_payload)
    _write_json(system_output, [])

    evaluator = PersonaExtractionEvaluator(
        ground_truth_dir=ground_truth_dir,
        system_output_path=system_output,
    )
    result = evaluator.run_evaluation()
    assert result["counts"]["ground_truth_personas"] == 1
    assert result["counts"]["detected_personas"] == 0


def test_fact_extraction_evaluator_mismatch(tmp_path: Path):
    ground_truth_file = tmp_path / "gt.json"
    system_file = tmp_path / "page_2.md"

    payload = {"page_number": 2, "facts": [{"attribute": "price", "value": "high"}]}
    _write_json(ground_truth_file, payload)

    system_file.write_text("Price is low.", encoding="utf-8")

    evaluator = FactExtractionEvaluator(
        ground_truth_file=ground_truth_file,
        system_output_path=system_file,
    )
    result = evaluator.run_evaluation()
    assert result["matched_values"] == 0
    assert result["mismatched_values"][0]["mismatch_reason"] == "value_not_found"


def test_rag_retrieval_evaluator_with_results_file(tmp_path: Path):
    queries_file = tmp_path / "queries.json"
    results_file = tmp_path / "results.json"

    queries_payload = [
        {"query_id": "q1", "query": "taste", "relevant_indicators": ["a", "b"]}
    ]
    results_payload = {"results": [{"query_id": "q1", "retrieved_indicators": ["a", "c"]}]}

    _write_json(queries_file, queries_payload)
    _write_json(results_file, results_payload)

    evaluator = RAGRetrievalEvaluator(
        queries_file=queries_file,
        retrieval_results_file=results_file,
        k_values=(1, 2),
    )
    result = evaluator.run_evaluation()
    assert result["total_queries"] == 1
    assert result["precision_at_1"] == 1.0
    assert result["recall_at_2"] == 0.5
