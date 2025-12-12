# Core: `PersonaRouter`

**Code**: `adsp/core/ai_persona_router/__init__.py`

## Purpose

`PersonaRouter` selects the appropriate model or adapter for a given persona and dispatches the prompt to the inference engine.

## Responsibilities

- Choose an inference path per `persona_id`
- Send prompt to the runtime inference engine

## Public API

### `dispatch(persona_id: str, prompt: str) -> str`

**Inputs**
- `persona_id`: used to select adapter/model
- `prompt`: prompt string produced by `PromptBuilder`

**Output**
- persona response string

## Internal logic (current)

- Delegates to `PersonaInferenceEngine.generate(persona_id, prompt)`

## Key dependencies / technologies

- `adsp/modeling/inference.py` (`PersonaInferenceEngine`)

## Notes / production hardening

In production, this component typically:
- maps `persona_id` → adapter checkpoint (LoRA) or fine-tuned model endpoint
- supports multiple backends (local `transformers`, vLLM, TGI, etc.)
- applies safety and decoding policies consistently

