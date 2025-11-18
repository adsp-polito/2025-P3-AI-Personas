"""CLI for running persona inference stub."""

from pathlib import Path

import typer

from adsp.config import MODELS_DIR
from adsp.modeling.inference import PersonaInferenceEngine

app = typer.Typer()


@app.command()
def main(
    persona_id: str = "default",
    prompt_path: Path = Path("prompt.txt"),
    model_dir: Path = MODELS_DIR,
):
    _ = model_dir  # Placeholder until a real loader is implemented
    engine = PersonaInferenceEngine()
    prompt = prompt_path.read_text(encoding="utf-8") if prompt_path.exists() else ""
    typer.echo(engine.generate(persona_id=persona_id, prompt=prompt))


if __name__ == "__main__":
    app()
