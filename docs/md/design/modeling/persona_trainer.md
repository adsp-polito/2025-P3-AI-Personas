# Modeling: `PersonaTrainer`

**Code**: `adsp/modeling/training.py`

## Purpose

`PersonaTrainer` is the entrypoint for training persona adapters (PEFT/LoRA) so each persona can have a distinct voice and reasoning style.

Today it is a stub that writes a placeholder file.

## Responsibilities

- Load a persona training dataset
- Train and export an adapter artifact to an output directory

## Public API

### `train() -> pathlib.Path`

**Inputs**
- `dataset_path`: path to the training dataset
- `output_dir`: directory where the adapter is written

**Output**
- Path to the saved adapter artifact

## Current behavior

- Writes `persona_adapter.bin` with placeholder content and returns its path.

## Key dependencies / technologies

- Python `dataclasses`
- `pathlib.Path` file IO

## Notes / production hardening

To implement actual PEFT training, typical stack:
- `transformers` + `peft` + `datasets`
- Base model checkpoint (e.g., Llama/Mistral family)
- Training data derived from:
  - persona profile `summary_bio`, salient indicators, style_profile/value_frame
  - curated dialogue examples
- Evaluation suite gating before promotion (see `docs/md/design/monitoring/evaluation_suite.md`)

