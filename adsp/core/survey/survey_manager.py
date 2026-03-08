"""Survey definition CRUD operations."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Mapping

from loguru import logger

from adsp.config import PROCESSED_DATA_DIR

from .models import Survey
from .utils import ensure_dir, load_json, make_identifier, model_dump, save_json, utc_now
from .validators import validate_survey_definition


class SurveyManager:
    """Manages survey definitions persisted as JSON files."""

    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = Path(base_dir or (PROCESSED_DATA_DIR / "surveys"))
        self.definitions_dir = ensure_dir(self.base_dir / "definitions")

    def create_survey(self, survey_definition: Mapping[str, Any]) -> Survey:
        payload: Dict[str, Any] = dict(survey_definition)
        payload.setdefault("survey_id", make_identifier("survey"))
        payload.setdefault("created_at", utc_now())

        survey = validate_survey_definition(payload)
        self._write_survey(survey)
        return survey

    def get_survey(self, survey_id: str) -> Survey:
        path = self._survey_path(survey_id)
        if not path.exists():
            raise KeyError(f"Survey '{survey_id}' not found")

        payload = load_json(path)
        return validate_survey_definition(payload)

    def list_surveys(self) -> List[Survey]:
        surveys: List[Survey] = []
        for path in sorted(self.definitions_dir.glob("*.json")):
            try:
                payload = load_json(path)
                surveys.append(validate_survey_definition(payload))
            except Exception as exc:
                logger.warning("Skipping invalid survey file {}: {}", path, exc)
        return surveys

    def validate_survey(self, survey_definition: Mapping[str, Any]) -> bool:
        try:
            validate_survey_definition(survey_definition)
            return True
        except Exception:
            return False

    def _write_survey(self, survey: Survey) -> None:
        path = self._survey_path(survey.survey_id)
        save_json(path, model_dump(survey))

    def _survey_path(self, survey_id: str) -> Path:
        return self.definitions_dir / f"{survey_id}.json"
