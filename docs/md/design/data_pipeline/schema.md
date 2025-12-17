# Data Pipeline: Persona Schema (`PersonaProfileModel`)

**Code**: `adsp/data_pipeline/schema.py`

## Purpose

Defines the canonical typed schema for persona profiles produced by extraction and consumed by prompt construction and retrieval/indexing.

## Responsibilities

- Provide Pydantic models for:
  - page sources, metrics, salience, influences
  - indicators and statements
  - reasoning enrichment traits (style/value/policies/filters)
- Support parsing JSON payloads into typed objects

## Key models

- `PersonaProfileModel`
- `Indicator` → `Statement` → `Metric`
- `Salience`, `Influences`
- Reasoning enrichment:
  - `StyleProfile`
  - `ValueFrame`
  - `ReasoningPolicies` (with `PurchaseAdvice`, `ProductEvaluation`, `InformationProcessing`)
  - `ContentFilters`

## Important schema behaviors

- `extra = "allow"` on all models:
  - The pipeline can accept additional fields without breaking parsing.
  - Good for iterative schema evolution, but can hide unexpected upstream changes; add validation checks in QA reports if strictness is needed.

## Public helper

### `load_persona_profile(path: str | Path) -> PersonaProfileModel`

**Input**
- Path to a persona profile JSON file

**Output**
- Parsed `PersonaProfileModel`

**Failure modes**
- Raises `FileNotFoundError` if file does not exist
- Raises `pydantic.ValidationError` if payload cannot be parsed into the model

## Related documentation

- Human-readable schema description: `docs/md/persona_profile_schema.md`

