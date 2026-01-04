# Local Dev Configuration

## Project paths

`adsp/config.py` defines canonical paths relative to the repo root:
- `DATA_DIR`, `RAW_DATA_DIR`, `INTERIM_DATA_DIR`, `PROCESSED_DATA_DIR`
- `MODELS_DIR`
- `REPORTS_DIR`, `FIGURES_DIR`

These defaults are used by:
- persona extraction pipeline config (`PersonaExtractionConfig`)
- modeling CLIs (`train`, `predict`)

## Environment variables

`.env` is loaded at import time via `python-dotenv` in `adsp/config.py`.

Create it from the provided template:
- `cp .env.example .env`

Common variables:
- `VLLM_BASE_URL`, `VLLM_MODEL`, `VLLM_API_KEY`
- `REASONING_BASE_URL`, `REASONING_MODEL`, `REASONING_API_KEY`
- Runtime chat backend:
  - `ADSP_LLM_BACKEND` (`stub` or `openai`)
  - `ADSP_LLM_BASE_URL`, `ADSP_LLM_MODEL`, `ADSP_LLM_API_KEY`
- Persona data paths:
  - `ADSP_PERSONAS_DIR`
  - `ADSP_PERSONA_TRAITS_DIR`

## Useful commands

- Install deps: `make install`
- Lint: `make lint`
- Format: `make format`
- Run chat: `make chat` or `python scripts/run_chat.py chat --persona-id basic-traditional`

## Notes on current repo state

- Several components are stubs (in-memory storage, placeholder inference/training). The design docs call out recommended production replacements.
