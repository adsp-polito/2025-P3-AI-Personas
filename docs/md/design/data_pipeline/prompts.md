# Data Pipeline: Prompt Templates

This pipeline uses two prompt families:

1. **Vision extraction prompt** (page → structured JSON)
2. **Alignment/reasoning prompt** (salient evidence → traits)

## Vision extraction prompt

**Code**: `adsp/data_pipeline/persona_data_pipeline/extract_raw/prompts.py` (`SYSTEM_PROMPT`)

Key requirements enforced by the prompt:
- Detect persona vs general market pages
- Separate multiple personas on the same page without cross-contamination
- Emit hierarchical data:
  - Indicator → Statements → Metrics
- Include traceability and cross-page linkage hints
- Output strict JSON (no markdown fences)

## Reasoning/alignment prompts

**Code**: `adsp/data_pipeline/persona_data_pipeline/extract_raw/alignment_prompts.py`

- `ALIGNMENT_SYSTEM_PROMPT`: instructs “use evidence only” and output strict JSON sections.
- `ALIGNMENT_USER_TEMPLATE`: provides:
  - persona identity
  - current partial profile (for chunking)
  - salient `key_indicators` evidence
  - explicit required JSON schema for `style_profile`, `value_frame`, `reasoning_policies`, `content_filters`

## Notes

- Both prompts are designed for determinism and schema compliance. When using non-deterministic decoding, schema violations increase and should be caught by QA validation.

