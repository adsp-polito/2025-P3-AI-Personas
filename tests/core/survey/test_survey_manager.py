"""Survey manager unit tests."""

from pathlib import Path

from adsp.core.survey import SurveyManager


def _survey_payload() -> dict:
    return {
        "title": "Coffee Behavior Survey",
        "description": "Segment-level coffee habits",
        "questions": [
            {
                "question_id": "q1",
                "text": "How often do you drink coffee?",
                "type": "multiple_choice",
                "options": ["Daily", "Weekly", "Rarely"],
            },
            {
                "question_id": "q2",
                "text": "What matters most when purchasing coffee?",
                "type": "open_ended",
            },
        ],
    }


def test_create_get_and_list_survey(tmp_path: Path):
    manager = SurveyManager(base_dir=tmp_path / "surveys")

    created = manager.create_survey(_survey_payload())

    loaded = manager.get_survey(created.survey_id)
    listed = manager.list_surveys()

    assert loaded.survey_id == created.survey_id
    assert loaded.title == "Coffee Behavior Survey"
    assert len(listed) == 1
    assert listed[0].survey_id == created.survey_id


def test_validate_survey_rejects_invalid_schema(tmp_path: Path):
    manager = SurveyManager(base_dir=tmp_path / "surveys")

    payload = {
        "title": "Broken Survey",
        "questions": [
            {
                "question_id": "q1",
                "text": "Pick one",
                "type": "multiple_choice",
                "options": [],
            }
        ],
    }

    assert manager.validate_survey(payload) is False
