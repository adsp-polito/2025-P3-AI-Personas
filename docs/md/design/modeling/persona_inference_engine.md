# Modeling: `PersonaInferenceEngine`

**Code**: `adsp/modeling/inference.py`

## Purpose

`PersonaInferenceEngine` is the runtime “model serving” abstraction used by the Core `PersonaRouter`.

Today it is a placeholder that echoes the prompt; in production it should be backed by a real LLM serving stack (vLLM/TGI/transformers).

## Responsibilities

- Generate a persona response given `(persona_id, prompt)`
- (Planned) load persona-specific adapters (LoRA) and apply decoding policies

## Public API

### `generate(persona_id: str, prompt: str) -> str`

**Input**
- `persona_id`: used to select adapter/model
- `prompt`: full prompt from `PromptBuilder`

**Output**
- response string

## Current behavior

- Returns `f"[{persona_id}] {prompt[:200]}"`

## Key dependencies / technologies

- Python `dataclasses`

## Notes / production hardening

Recommended features:
- Support OpenAI-compatible chat API calls and/or local `transformers` generation
- Adapter management:
  - persona_id → adapter path
  - hot reload / versioning
- Safety policies and refusal logic (“not enough data”)
- Structured outputs (answer + citations + explanation)

