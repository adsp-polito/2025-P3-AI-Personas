"""Frontend survey management helper checks."""

import altair as alt

from adsp.fe.components.survey_management import (
    _choice_chart_rows,
    _has_processing_simulations,
    _multiple_choice_pie_chart,
    _rating_chart_rows,
    _rating_bar_chart,
)


def test_has_processing_simulations_detects_processing_status():
    payload = {
        "simulations": [
            {"simulation_id": "sim-1", "status": "completed"},
            {"simulation_id": "sim-2", "status": "processing"},
        ]
    }

    assert _has_processing_simulations(payload) is True


def test_has_processing_simulations_ignores_completed_runs():
    payload = {
        "simulations": [
            {"simulation_id": "sim-1", "status": "completed"},
            {"simulation_id": "sim-2", "status": "failed"},
        ]
    }

    assert _has_processing_simulations(payload) is False


def test_choice_chart_rows_preserve_labels_and_convert_percentages():
    distribution = [
        {"value": "Great taste", "count": 18, "percentage": 0.45},
        {"value": "Affordable price", "count": "12", "percentage": "0.3"},
    ]

    assert _choice_chart_rows(distribution) == [
        {"choice": "Great taste", "responses": 18, "share_pct": 45.0},
        {"choice": "Affordable price", "responses": 12, "share_pct": 30.0},
    ]


def test_rating_chart_rows_sort_numerically():
    distribution = [
        {"value": "5", "count": 7, "percentage": 0.35},
        {"value": "2", "count": 3, "percentage": 0.15},
        {"value": "10", "count": 1, "percentage": 0.05},
    ]

    assert _rating_chart_rows(distribution) == [
        {"rating": "2", "responses": 3, "share_pct": 15.0},
        {"rating": "5", "responses": 7, "share_pct": 35.0},
        {"rating": "10", "responses": 1, "share_pct": 5.0},
    ]


def test_multiple_choice_pie_chart_returns_altair_chart():
    chart = _multiple_choice_pie_chart(
        [{"choice": "Great taste", "responses": 18, "share_pct": 45.0}]
    )

    assert isinstance(chart, alt.Chart)


def test_rating_bar_chart_returns_altair_chart():
    chart = _rating_bar_chart(
        [{"rating": "5", "responses": 7, "share_pct": 35.0}]
    )

    assert isinstance(chart, alt.Chart)
