"""Monitoring helpers and evaluation pipeline tests."""

import json
from decimal import Decimal
from pathlib import Path

import pytest

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


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding='utf-8')


def basic_metric(value: int = 10, unit: str = '$') -> dict:
    return {'value': value, 'unit': unit}


def basic_indicator(label: str = 'Price') -> dict:
    return {
        'label': label,
        'description': 'Cost',
        'statements': [
            {
                'label': 'Budget',
                'description': 'Low',
                'metrics': [basic_metric()],
            }
        ],
    }


def ground_truth_payload(values: list[dict]) -> dict:
    return {
        'ground_truth': {
            'indicators': [
                {
                    'label': 'Price',
                    'description': 'Cost',
                    'statements': [
                        {
                            'label': 'Budget',
                            'description': 'Low',
                            'metrics': values,
                        }
                    ],
                }
            ]
        }
    }


def persona_payload(values: list[dict]) -> dict:
    return {
        'personas': [
            {
                'persona_id': 'p1',
                'indicators': [
                    {
                        'label': 'Price',
                        'description': 'Cost',
                        'statements': [
                            {
                                'label': 'Budget',
                                'description': 'Low',
                                'metrics': values,
                            }
                        ],
                    }
                ],
            }
        ]
    }


def test_metrics_collector_increments_accumulate():
    metrics = MetricsCollector()
    metrics.incr('hits')
    metrics.incr('hits', 2.5)
    assert metrics.read('hits') == 3.5


def test_metrics_collector_write_overrides_previous():
    metrics = MetricsCollector()
    metrics.incr('latency', 5)
    metrics.write('latency', 2)
    assert metrics.read('latency') == 2


def test_metrics_collector_read_missing_returns_zero():
    metrics = MetricsCollector()
    assert metrics.read('missing') == 0.0


def test_metrics_collector_tracks_multiple_keys():
    metrics = MetricsCollector()
    metrics.incr('a', 1.0)
    metrics.incr('b', 2.0)
    metrics.incr('a', 3.0)
    assert metrics.read('a') == 4.0
    assert metrics.read('b') == 2.0


def test_metrics_collector_negative_values():
    metrics = MetricsCollector()
    metrics.incr('delta', -1)
    assert metrics.read('delta') == -1


def test_evaluation_suite_runs_named_checks():
    def check_length(response: str) -> bool:
        return len(response) > 3

    def check_contains(response: str) -> bool:
        return 'ok' in response

    suite = EvaluationSuite(checks=[check_length, check_contains])
    result = suite.run('ok fine')
    assert result == {'check_length': True, 'check_contains': True}


def test_evaluation_suite_empty_checks():
    suite = EvaluationSuite()
    assert suite.run('anything') == {}


def test_evaluation_suite_preserves_check_names():
    def check_alpha(_: str) -> bool:
        return True

    def check_beta(_: str) -> bool:
        return False

    suite = EvaluationSuite(checks=[check_alpha, check_beta])
    result = suite.run('payload')
    assert result == {'check_alpha': True, 'check_beta': False}


@pytest.mark.parametrize(
    'text,expected',
    [
        ('Hello, World!', 'hello world'),
        ('A\n\nB\tC', 'a b c'),
        ('', ''),
        ('Mixed CASE', 'mixed case'),
        ('punctuation!!!', 'punctuation'),
    ],
)
def test_normalize_text_cases(text: str, expected: str):
    assert _normalize_text(text) == expected


@pytest.mark.parametrize(
    'left,right,expected',
    [
        ('price is low', 'price range', 0.5),
        ('', 'something', 0.0),
        ('value', '', 0.0),
        ('alpha beta', 'beta alpha', 1.0),
    ],
)
def test_word_overlap_ratio_cases(left: str, right: str, expected: float):
    assert _word_overlap_ratio(left, right) == expected


def test_normalize_match_text_applies_synonyms():
    assert _normalize_match_text('USD price') == '$ price'


def test_normalize_match_text_empty_returns_empty():
    assert _normalize_match_text('') == ''


def test_tokenize_words_returns_clean_words():
    assert _tokenize_words('Hello, world!') == ['hello', 'world']


def test_tokenize_words_empty_returns_empty():
    assert _tokenize_words('') == []


def test_tokenize_words_collapse_whitespace():
    assert _tokenize_words('A   B\nC') == ['a', 'b', 'c']


def test_ground_truth_word_coverage_matches():
    coverage = _ground_truth_word_coverage('low price', 'price is low and fair')
    assert coverage == 1.0


def test_ground_truth_word_coverage_partial():
    coverage = _ground_truth_word_coverage('low price', 'price is fair')
    assert coverage == 0.5


def test_ground_truth_word_coverage_empty_inputs():
    assert _ground_truth_word_coverage(None, 'text') == 0.0
    assert _ground_truth_word_coverage('value', '') == 0.0


@pytest.mark.parametrize(
    'payload,expected',
    [
        ({'page_number': 12}, 12),
        ({'page': 9}, 9),
        ({'page_id': 'page 4'}, 4),
        ({'page_number': 'page 12'}, 12),
        ({'page_id': None}, None),
    ],
)
def test_parse_page_number_cases(payload: dict, expected: int | None):
    assert _parse_page_number(payload) == expected


@pytest.mark.parametrize(
    'value,expected',
    [
        ('USD 2,500', Decimal('2500')),
        ('10', Decimal('10')),
        (10, Decimal('10')),
        (10.0, Decimal('10.0')),
        ('none', None),
        (None, None),
    ],
)
def test_safe_decimal_cases(value, expected):
    assert _safe_decimal(value) == expected


def test_normalize_persona_id_replaces_spaces():
    assert _normalize_persona_id('My Persona') == 'my-persona'


def test_normalize_unit_maps_symbols():
    assert _normalize_unit('USD') == '$'


def test_normalize_unit_unknown_kept():
    assert _normalize_unit('custom') == 'custom'


def test_indicator_matches_with_description_overlap():
    assert _indicator_matches('price', '', 'price range', 0.5) is True


def test_statement_matches_basic():
    assert _statement_matches('value', 'value', '', 0.5) is True
    assert _statement_matches('value', 'quality', '', 0.5) is False


@pytest.mark.parametrize(
    'gt,sys,expected',
    [
        ('2', 2.0, True),
        ('3', 4, False),
        ('10', '10', True),
        ('ten', 'ten', True),
        ('ten', 'eleven', False),
    ],
)
def test_values_match_cases(gt, sys, expected: bool):
    assert _values_match(gt, sys) is expected


@pytest.mark.parametrize(
    'gt,sys,expected',
    [
        ('USD', 'USD', True),
        ('USD', '$', True),
        ('', 'usd', True),
        ('%', 'usd', False),
    ],
)
def test_units_match_cases(gt, sys, expected: bool):
    assert _units_match(gt, sys) is expected


def test_units_match_empty_ground_truth_is_true():
    assert _units_match('', 'usd') is True


def test_extract_persona_ids_from_parsed_payload():
    payload = {
        'personas': [
            {'persona_id': 'p1'},
            {'persona_name': 'Persona Two'},
        ]
    }
    assert _extract_persona_ids(payload) == ['p1', 'persona-two']


def test_extract_persona_ids_empty_payload():
    assert _extract_persona_ids({}) == []


def test_extract_ground_truth_metrics_basic():
    payload = {'ground_truth': {'indicators': [basic_indicator()]}}
    metrics = _extract_ground_truth_metrics(payload)

    assert len(metrics) == 1
    assert metrics[0].indicator_label == 'Price'
    assert metrics[0].statement_label == 'Budget'
    assert metrics[0].unit == '$'


def test_extract_ground_truth_metrics_handles_empty():
    metrics = _extract_ground_truth_metrics({'ground_truth': {'indicators': []}})
    assert metrics == []


def test_extract_persona_metrics_from_parsed_payload():
    parsed = {
        'personas': [
            {
                'persona_id': 'p1',
                'indicators': [
                    {
                        'label': 'Service',
                        'description': 'Quality',
                        'statements': [
                            {
                                'label': 'Speed',
                                'description': 'Fast',
                                'metrics': [{'value': 5, 'unit': '%'}],
                            }
                        ],
                    }
                ],
            }
        ]
    }
    metrics = _extract_persona_metrics(parsed)

    assert len(metrics) == 1
    assert metrics[0].indicator_label == 'Service'
    assert metrics[0].statement_label == 'Speed'
    assert metrics[0].unit == '%'


def test_match_metrics_with_mismatches_value_mismatch():
    ground_truth = _extract_ground_truth_metrics(ground_truth_payload([basic_metric()]))
    system = _extract_persona_metrics(persona_payload([basic_metric(value=12)]))

    matched, gt_miss, sys_miss = _match_metrics_with_mismatches(ground_truth, system, 0.5)

    assert matched == 0
    assert len(gt_miss) == 1
    assert gt_miss[0]['mismatch_step'] == 'value_match'
    assert len(sys_miss) == 1


def test_match_metrics_with_mismatches_full_match():
    ground_truth = _extract_ground_truth_metrics(ground_truth_payload([basic_metric()]))
    system = _extract_persona_metrics(persona_payload([basic_metric(unit='USD')]))

    matched, gt_miss, sys_miss = _match_metrics_with_mismatches(ground_truth, system, 0.5)

    assert matched == 1
    assert gt_miss == []
    assert sys_miss == []


def test_match_metrics_with_mismatches_indicator_mismatch():
    ground_truth = _extract_ground_truth_metrics(ground_truth_payload([basic_metric()]))
    system = _extract_persona_metrics(
        {
            'personas': [
                {
                    'indicators': [
                        {
                            'label': 'Taste',
                            'description': 'Flavor',
                            'statements': [
                                {
                                    'label': 'Rich',
                                    'description': 'Strong',
                                    'metrics': [basic_metric()],
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
    assert gt_miss[0]['mismatch_step'] == 'indicator_match'
    assert sys_miss[0]['mismatch_step'] == 'extra_extraction'


def test_match_metrics_with_mismatches_duplicate_match():
    ground_truth = _extract_ground_truth_metrics(
        ground_truth_payload([basic_metric(), basic_metric()])
    )
    system = _extract_persona_metrics(persona_payload([basic_metric()]))

    matched, gt_miss, sys_miss = _match_metrics_with_mismatches(ground_truth, system, 0.5)

    assert matched == 1
    assert len(gt_miss) == 1
    assert gt_miss[0]['mismatch_step'] == 'duplicate_match'
    assert sys_miss == []


def test_determine_mismatch_reason_unit_mismatch():
    gt_metric = _MetricEntry(
        indicator_label='Price',
        indicator_description='Cost',
        statement_label='Budget',
        statement_description='Low',
        value=10,
        unit='$',
    )
    sys_metric = _MetricEntry(
        indicator_label='Price',
        indicator_description='Cost',
        statement_label='Budget',
        statement_description='Low',
        value=10,
        unit='%',
    )

    mismatch_step, reason = _determine_mismatch_reason(gt_metric, [sys_metric], 0.5, set())

    assert mismatch_step == 'unit_match'
    assert reason == 'unit_mismatch'


def test_determine_mismatch_reason_value_mismatch():
    gt_metric = _MetricEntry(
        indicator_label='Price',
        indicator_description='Cost',
        statement_label='Budget',
        statement_description='Low',
        value=10,
        unit='$',
    )
    sys_metric = _MetricEntry(
        indicator_label='Price',
        indicator_description='Cost',
        statement_label='Budget',
        statement_description='Low',
        value=12,
        unit='$',
    )

    mismatch_step, reason = _determine_mismatch_reason(gt_metric, [sys_metric], 0.5, set())

    assert mismatch_step == 'value_match'
    assert reason == 'value_mismatch'


def test_persona_extraction_evaluator_basic(tmp_path: Path):
    ground_truth_dir = tmp_path / 'gt'
    ground_truth_dir.mkdir()
    system_output = tmp_path / 'system.json'

    gt_payload = {
        'page_number': 1,
        'ground_truth': {
            'personas': ['p1'],
            'indicators': [basic_indicator()],
        },
    }
    write_json(ground_truth_dir / 'page_1.json', gt_payload)

    system_payload = [
        {
            'page_number': 1,
            'parsed': {
                'personas': [
                    {
                        'persona_id': 'p1',
                        'indicators': [
                            {
                                'label': 'Price',
                                'description': 'Cost',
                                'statements': [
                                    {
                                        'label': 'Budget',
                                        'description': 'Low',
                                        'metrics': [{'value': 10, 'unit': 'USD'}],
                                    }
                                ],
                            }
                        ],
                    }
                ]
            },
        }
    ]
    write_json(system_output, system_payload)

    evaluator = PersonaExtractionEvaluator(
        ground_truth_dir=ground_truth_dir,
        system_output_path=system_output,
        word_overlap_threshold=0.5,
    )
    result = evaluator.run_evaluation()

    assert result['counts']['ground_truth_personas'] == 1
    assert result['counts']['detected_personas'] == 1
    assert result['counts']['matched_metrics'] == 1


def test_persona_extraction_evaluator_handles_missing_pages(tmp_path: Path):
    ground_truth_dir = tmp_path / 'gt'
    ground_truth_dir.mkdir()
    system_output = tmp_path / 'system.json'

    gt_payload = {
        'page_number': 1,
        'ground_truth': {'personas': ['p1'], 'indicators': []},
    }
    write_json(ground_truth_dir / 'page_1.json', gt_payload)
    write_json(system_output, [])

    evaluator = PersonaExtractionEvaluator(
        ground_truth_dir=ground_truth_dir,
        system_output_path=system_output,
    )
    result = evaluator.run_evaluation()

    assert result['counts']['ground_truth_personas'] == 1
    assert result['counts']['detected_personas'] == 0


def test_fact_extraction_evaluator_markdown(tmp_path: Path):
    ground_truth_file = tmp_path / 'gt.json'
    system_dir = tmp_path / 'pages'
    system_dir.mkdir()

    payload = [
        {
            'page_number': 1,
            'facts': [
                {'attribute': 'price', 'value': 'low'},
                {'attribute': 'origin', 'value': 'italy'},
            ],
        }
    ]
    write_json(ground_truth_file, payload)

    page_file = system_dir / 'page_1.md'
    page_file.write_text('Price is low. Origin is Italy.', encoding='utf-8')

    evaluator = FactExtractionEvaluator(
        ground_truth_file=ground_truth_file,
        system_output_path=system_dir,
    )
    result = evaluator.run_evaluation()

    assert result['total_values'] == 2
    assert result['matched_values'] == 2
    assert result['system_source'] == 'markdown'


def test_fact_extraction_evaluator_mismatch(tmp_path: Path):
    ground_truth_file = tmp_path / 'gt.json'
    system_file = tmp_path / 'page_2.md'

    payload = {'page_number': 2, 'facts': [{'attribute': 'price', 'value': 'high'}]}
    write_json(ground_truth_file, payload)

    system_file.write_text('Price is low.', encoding='utf-8')

    evaluator = FactExtractionEvaluator(
        ground_truth_file=ground_truth_file,
        system_output_path=system_file,
    )
    result = evaluator.run_evaluation()

    assert result['matched_values'] == 0
    assert result['mismatched_values'][0]['mismatch_reason'] == 'value_not_found'


def test_rag_retrieval_evaluator_uses_relevant_docs(tmp_path: Path):
    queries_file = tmp_path / 'queries.json'
    payload = [
        {
            'query_id': 'q1',
            'query': 'price',
            'relevant_docs': [
                {'page_content': 'doc1', 'relevance': 1},
                {'page_content': 'doc2', 'relevance': 0},
            ],
        }
    ]
    write_json(queries_file, payload)

    evaluator = RAGRetrievalEvaluator(queries_file=queries_file, k_values=(1, 2))
    result = evaluator.run_evaluation()

    assert result['total_queries'] == 1
    assert result['precision_at_1'] == 1.0
    assert result['recall_at_2'] == 1.0


def test_rag_retrieval_evaluator_with_results_file(tmp_path: Path):
    queries_file = tmp_path / 'queries.json'
    results_file = tmp_path / 'results.json'

    queries_payload = [
        {'query_id': 'q1', 'query': 'taste', 'relevant_indicators': ['a', 'b']}
    ]
    results_payload = {'results': [{'query_id': 'q1', 'retrieved_indicators': ['a', 'c']}]}

    write_json(queries_file, queries_payload)
    write_json(results_file, results_payload)

    evaluator = RAGRetrievalEvaluator(
        queries_file=queries_file,
        retrieval_results_file=results_file,
        k_values=(1, 2),
    )
    result = evaluator.run_evaluation()

    assert result['total_queries'] == 1
    assert result['precision_at_1'] == 1.0
    assert result['recall_at_2'] == 0.5


def test_authenticity_evaluator_scores(tmp_path: Path):
    eval_file = tmp_path / 'eval.json'
    payload = [
        {
            'persona_id': 'p1',
            'ratings': {
                'authenticity': {'score': 4},
                'style_alignment': {'score': 3},
                'factual_grounding': {'factually_accurate': True},
            },
        },
        {
            'persona_id': 'p1',
            'ratings': {
                'authenticity': {'score': 2},
                'style_alignment': {'score': 4},
                'factual_grounding': {'factually_accurate': False},
            },
        },
    ]
    write_json(eval_file, payload)

    evaluator = AuthenticityEvaluator(evaluations_file=eval_file)
    result = evaluator.run_evaluation()

    assert result['total_evaluations'] == 2
    assert result['persona_scores']['p1']['total_evaluations'] == 2
    assert result['expert_authenticity_score'] == 3.0
    assert result['factual_grounding_score'] == 0.5


def test_word_synonyms_contains_capsule_variants():
    assert WORD_SYNONYMS['cap'] == 'capsule'
    assert WORD_SYNONYMS['caps'] == 'capsule'
    assert WORD_SYNONYMS['capsule'] == 'capsule'
    assert WORD_SYNONYMS['capsules'] == 'capsule'
