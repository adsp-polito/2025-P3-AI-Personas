# Modeling: CLI `predict`

**Code**: `adsp/modeling/predict.py`

## Purpose

CLI utility to run persona inference from a prompt file using `PersonaInferenceEngine`.

## Usage

```bash
python -m adsp.modeling.predict --persona-id default --prompt-path prompt.txt
```

## Interface

Arguments:
- `persona_id` (default `"default"`)
- `prompt_path` (default `prompt.txt`)
- `model_dir` (default `models/` via `adsp.config.MODELS_DIR`; currently unused placeholder)

## Key dependencies / technologies

- `typer` CLI
- `pathlib.Path`

