# Application: `ReportService`

**Code**: `adsp/app/report_service.py`

## Purpose

`ReportService` generates stakeholder-friendly reports from computed persona insights.

## Responsibilities

- Accept structured “insights” payloads
- Write report artifacts (currently markdown) to an output directory

## Public API

### `generate(persona_id: str, insights: dict) -> pathlib.Path`

**Inputs**
- `persona_id`: identifier used to name the report file
- `insights`: arbitrary dictionary to embed in the report body

**Output**
- Returns the filesystem path where the report was written:
  - `{output_dir}/{persona_id}_report.md`

## Internal logic (current)

1. Constructs `report_path`
2. Writes a markdown stub containing the `insights` dict (stringified)
3. Returns `report_path`

## Key dependencies / technologies

- Python `dataclasses`
- `pathlib.Path` file IO

## Notes / production hardening

- Define a report schema (sections, citations, charts).
- Export to PDF/HTML and store in object storage.
- Add provenance: include evidence snippets and page citations from persona indicators.

