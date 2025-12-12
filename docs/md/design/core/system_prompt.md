# Core: `persona_to_system_prompt`

**Code**: `adsp/core/prompt_builder/system_prompt.py`

## Purpose

`persona_to_system_prompt()` converts a persona profile (including optional reasoning traits) into an LLM system prompt that steers voice, values, and guardrails.

## Responsibilities

- Generate consistent persona “system” instructions
- Encode:
  - voice/style (`style_profile`)
  - value priorities (`value_frame`)
  - reasoning tradeoffs (`reasoning_policies`)
  - content guardrails (`content_filters`)

## Public API

### `persona_to_system_prompt(persona: PersonaProfileModel) -> str`

**Input**
- `PersonaProfileModel` (see `adsp/data_pipeline/schema.py`)

**Output**
- Multi-section system prompt string

## Sections emitted

- Header: persona label and `summary_bio`
- `Voice:` section (if `style_profile` present)
- `Value frame:` section (if `value_frame` present)
- `Reasoning policies:` section (if `reasoning_policies` present)
- `Content filters:` section (if `content_filters` present)

## Key dependencies / technologies

- `pydantic` models from `adsp/data_pipeline/schema.py`

## Notes

- This function is intentionally strict about missing data: if a trait section is absent, it is omitted from the prompt instead of being fabricated.
- If the reasoning enrichment pipeline is disabled, prompts will contain only the baseline persona header unless other fields are present.

