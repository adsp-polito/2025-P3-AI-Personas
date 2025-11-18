"""CLI wrapper around the PersonaTrainer stub."""

from pathlib import Path

import typer

from adsp.config import MODELS_DIR, PROCESSED_DATA_DIR
from adsp.modeling.training import PersonaTrainer

app = typer.Typer()


@app.command()
def main(
    dataset_path: Path = PROCESSED_DATA_DIR / "persona_dataset.parquet",
    output_dir: Path = MODELS_DIR,
):
    trainer = PersonaTrainer(dataset_path=dataset_path, output_dir=output_dir)
    model_path = trainer.train()
    typer.echo(f"Saved adapter to {model_path}")


if __name__ == "__main__":
    app()
