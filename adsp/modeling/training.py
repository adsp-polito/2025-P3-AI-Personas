"""PEFT/LoRA training entrypoints."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class PersonaTrainer:
    """Stub trainer that will later host PEFT fine-tuning logic."""

    dataset_path: Path
    output_dir: Path

    def train(self) -> Path:
        model_path = self.output_dir / "persona_adapter.bin"
        model_path.write_text("adapter-bytes", encoding="utf-8")
        return model_path
