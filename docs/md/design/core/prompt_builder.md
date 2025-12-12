# Core: `PromptBuilder`

**Code**: `adsp/core/prompt_builder/__init__.py`, `adsp/core/prompt_builder/system_prompt.py`

## Purpose

`PromptBuilder` constructs the final prompt sent to a persona model by combining:
- persona rules/traits
- retrieved grounding context
- user question

## Responsibilities

- Retrieve persona metadata from `PersonaRegistry`
- Convert persona profiles into a system prompt (including reasoning traits when present)
- Assemble a single string prompt for the model

## Public API

### `build(persona_id: str, query: str, context: str) -> str`

**Inputs**
- `persona_id`: persona to load from the registry
- `query`: normalized user question
- `context`: retrieval grounding text (already formatted)

**Output**
- String prompt:
  - system prompt + `Context:` + `Question:`

## Internal logic (current)

1. `persona = PersonaRegistry.get(persona_id)`
2. `system_prompt = _system_prompt_for_persona(persona)`
3. Returns:
   - `{system_prompt}\n\nContext:\n{context}\n\nQuestion:\n{query}`

## Persona profile handling

`_system_prompt_for_persona()` supports:
- `PersonaProfileModel` (Pydantic) → `persona_to_system_prompt(profile)`
- `dict`:
  - if it looks like a profile with reasoning traits, attempt to validate as `PersonaProfileModel`
  - else fallback to `persona["preamble"]` or `"You are an AI persona."`

## Key dependencies / technologies

- `pydantic` (`ValidationError`)
- `adsp/data_pipeline/schema.py` (`PersonaProfileModel`)
- `PersonaRegistry` (`adsp/core/persona_registry/__init__.py`)

## Notes / production hardening

- Return structured prompt objects (`{system, user, context}`) rather than concatenated strings to better support chat-based LLM APIs.
- Add citation formatting to ensure explainability requirements are met (page refs + doc ids).

