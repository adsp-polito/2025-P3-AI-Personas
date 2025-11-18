"""Evaluation pipelines for persona quality."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass
class EvaluationSuite:
    """Runs rule-based or LLM-as-judge evaluations."""

    checks: Iterable = ()

    def run(self, response: str) -> dict:
        results = {}
        for check in self.checks:
            results[check.__name__] = check(response)
        return results
