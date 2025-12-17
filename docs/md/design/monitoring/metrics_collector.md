# Monitoring: `MetricsCollector`

**Code**: `adsp/monitoring/metrics.py`

## Purpose

`MetricsCollector` is a minimal metrics sink for counters/gauges in-process. It corresponds to the observability layer in `docs/md/design.md`.

## Responsibilities

- Increment counters (`incr`)
- Set gauges (`write`)
- Read current values (`read`)

## Public API

### `incr(name: str, value: float = 1.0) -> None`

Adds `value` to the metric `name`.

### `write(name: str, value: float = 1.0) -> float`

Sets the metric `name` to `value` and returns the stored value.

### `read(name: str) -> float`

Returns current value for `name`, defaulting to `0.0`.

## Data model

- `_metrics: Dict[str, float]` (in-memory)

## Key dependencies / technologies

- Python `dataclasses`
- In-memory storage (`dict`)

## Notes / production hardening

Replace with:
- Prometheus metrics (client library + scrape endpoint)
- OpenTelemetry traces and logs correlation
- Structured metrics for:
  - request latency (p50/p95/p99)
  - retrieval hits/misses
  - cache hit ratio
  - model token usage

