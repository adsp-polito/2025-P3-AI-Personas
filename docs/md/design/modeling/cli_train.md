# Modeling: CLI `train`

**Code**: `adsp/modeling/train.py`

## Purpose

CLI wrapper around `PersonaTrainer`.

## Usage

```bash
python -m adsp.modeling.train --dataset-path data/processed/persona_dataset.parquet --output-dir models/
```

## Interface

Arguments:
- `dataset_path` (defaults to `data/processed/persona_dataset.parquet`)
- `output_dir` (defaults to `models/`)

## Key dependencies / technologies

- `typer` CLI
- `pathlib.Path`

