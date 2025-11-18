"""Collects runtime metrics for observability."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class MetricsCollector:
    """Stores counters/gauges as a quick placeholder."""

    _metrics: Dict[str, float] = field(default_factory=dict)

    def incr(self, name: str, value: float = 1.0) -> None:
        self._metrics[name] = self._metrics.get(name, 0.0) + value
    def write(self, name: str, value: float = 1.0) -> float:
        self._metrics[name] = value
        return self._metrics.get(name)
    def read(self, name: str) -> float:
        return self._metrics.get(name, 0.0)
