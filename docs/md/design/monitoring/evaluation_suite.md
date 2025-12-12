# Monitoring: `EvaluationSuite`

**Code**: `adsp/monitoring/evaluation.py`

## Purpose

`EvaluationSuite` runs a list of checks against persona responses (rule-based, unit tests, or “LLM-as-judge” functions).

## Responsibilities

- Execute a configured set of `checks` on a response string
- Aggregate results into a dict keyed by check name

## Public API

### `run(response: str) -> dict`

**Input**
- `response`: model output text

**Output**
- `dict` mapping `check.__name__` → `check(response)` result

## Data model

- `checks: Iterable` of callables

## Key dependencies / technologies

- Python `dataclasses`
- Callable checks (can be pure Python, LLM calls, etc.)

## Recommended checks for this project

Aligned to `docs/md/design.md` requirements:
- Non-hallucination / “no evidence” fallback behavior
- Persona voice consistency (style_profile adherence)
- Citation/traceability presence (when using RAG)
- Toxicity/safety constraints
- Latency/token budget checks

