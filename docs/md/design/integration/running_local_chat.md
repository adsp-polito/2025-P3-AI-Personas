# Running Local Chat

This repo includes a runnable local chat loop that exercises the full FE → App → Core flow using:
- extracted persona profiles under `data/processed/personas/`
- local RAG over persona indicators (no external embedding model downloads)
- a stub generator by default (optional OpenAI-compatible backend)

## Prerequisites

- Install deps: `make install`
- (Optional) create a `.env`: `cp .env.example .env`

## List personas

```bash
python scripts/run_chat.py list-personas
```

## Interactive chat

```bash
python scripts/run_chat.py chat --persona-id basic-traditional
```

## One-shot ask

```bash
python scripts/run_chat.py ask "What do you value most?" --persona-id basic-traditional --top-k 5
```

## Using an OpenAI-compatible backend (optional)

If you have a local server (e.g., vLLM) exposing `/v1`:

```bash
export ADSP_LLM_BACKEND=openai
export ADSP_LLM_BASE_URL=http://localhost:8000/v1
export ADSP_LLM_MODEL=<your-model>
export ADSP_LLM_API_KEY=EMPTY
python scripts/run_chat.py chat --persona-id basic-traditional
```

## Notes

- Persona files are loaded from `ADSP_PERSONAS_DIR` (default: `data/processed/personas/individual`).
- Reasoning traits are loaded from `ADSP_PERSONA_TRAITS_DIR` (default: `data/processed/personas/common_traits`).

