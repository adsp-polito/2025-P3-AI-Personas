"""Local CLI to run the end-to-end chat flow."""

from __future__ import annotations

import sys
from typing import Optional

import typer

from adsp.app import QAService

app = typer.Typer(add_completion=False)


def _print_citations(response) -> None:
    if not response.citations:
        return
    typer.echo("\nCitations:")
    for idx, citation in enumerate(response.citations[:5], start=1):
        doc_id = citation.doc_id or "unknown"
        pages = ",".join(str(p) for p in (citation.pages or [])) or "-"
        indicator = citation.indicator_label or citation.indicator_id or "-"
        typer.echo(f"- [{idx}] {doc_id} pages={pages} indicator={indicator}")


@app.command()
def list_personas() -> None:
    """List available personas loaded from processed data."""

    qa = QAService()
    registry = qa.orchestrator.prompt_builder.registry
    for persona_id in registry.list_personas():
        persona = registry.get(persona_id)
        name = getattr(persona, "persona_name", None) or getattr(persona, "persona_id", None) or ""
        typer.echo(f"{persona_id}\t{name}")


@app.command()
def ask(
    query: str = typer.Argument(..., help="User question"),
    persona_id: str = typer.Option("default", "--persona-id", help="Persona id"),
    session_id: Optional[str] = typer.Option(None, "--session-id", help="Conversation/session id"),
    top_k: int = typer.Option(5, "--top-k", help="Top-k retrieved context blocks"),
    show_context: bool = typer.Option(False, "--show-context", help="Print retrieved context"),
) -> None:
    """Ask a single question and print the persona response."""

    qa = QAService()
    response = qa.ask_with_metadata(
        persona_id=persona_id,
        query=query,
        session_id=session_id,
        top_k=top_k,
    )
    typer.echo(response.answer)
    _print_citations(response)
    if show_context:
        typer.echo("\nContext:\n" + response.context)


@app.command()
def chat(
    persona_id: str = typer.Option("default", "--persona-id", help="Persona id"),
    session_id: Optional[str] = typer.Option("local", "--session-id", help="Conversation/session id"),
    top_k: int = typer.Option(5, "--top-k", help="Top-k retrieved context blocks"),
    show_context: bool = typer.Option(False, "--show-context", help="Print retrieved context"),
) -> None:
    """Interactive chat loop (type 'exit' to quit)."""

    qa = QAService()
    typer.echo(f"Persona: {persona_id} (session_id={session_id})")
    typer.echo("Type 'exit' to quit.\n")

    while True:
        try:
            user_text = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            typer.echo("\nBye.")
            return
        if not user_text:
            continue
        if user_text.lower() in {"exit", "quit"}:
            typer.echo("Bye.")
            return

        response = qa.ask_with_metadata(
            persona_id=persona_id,
            query=user_text,
            session_id=session_id,
            top_k=top_k,
        )
        typer.echo("\n" + response.answer)
        _print_citations(response)
        if show_context:
            typer.echo("\nContext:\n" + response.context)
        typer.echo("")


def main() -> None:
    app()


if __name__ == "__main__":
    sys.exit(main())

