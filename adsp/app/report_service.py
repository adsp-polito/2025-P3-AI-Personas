"""Generates structured reports from processed persona insights."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class ReportService:
    """Coordinates pulling insights and writing them to human-friendly formats."""

    output_dir: Path

    def generate(self, persona_id: str, insights: dict) -> Path:
        """Persist the supplied insights in a markdown stub for stakeholders."""

        report_path = self.output_dir / f"{persona_id}_report.md"
        report_path.write_text(f"# Insights for {persona_id}\n\n{insights}\n", encoding="utf-8")
        return report_path
