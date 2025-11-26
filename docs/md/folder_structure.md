# Repository Folder Structure

This document mirrors the layout described in `README.md` and expands on how each directory supports the Lavazza AI Personas system design.

## High-Level Layout

```text
root/
├── LICENSE
├── Makefile
├── pyproject.toml
├── requirements.txt
├── setup.cfg
├── README.md
├── data/
│   ├── raw/
│   ├── interim/
│   ├── processed/
│   └── external/
├── docs/
│   ├── design.md
│   ├── folder_structure.md
│   ├── images/
│   └── docs/ (MkDocs sources)
├── models/
├── notebooks/
├── references/
├── reports/
│   └── figures/
├── tests/
└── adsp/
    ├── config.py
    ├── fe/
    ├── app/
    ├── communication/
    ├── core/
    │   ├── input_handler/
    │   ├── memory/
    │   ├── orchestrator/
    │   ├── persona_registry/
    │   ├── ai_persona_router/
    │   ├── prompt_builder/
    │   ├── rag/
    │   └── mcp_server/
    │       └── tools/
    ├── data_pipeline/
    ├── modeling/
    ├── monitoring/
    ├── storage/
    └── utils/
```

## Directory Details

### Root-Level Assets
- `README.md` – quickstart for contributors; tree above stays in sync with that section.
- `pyproject.toml`, `requirements.txt`, `setup.cfg` – dependency and tooling configuration.
- `Makefile` – automation hooks for ingestion, training, and evaluation workflows.
- `LICENSE` – legal terms for redistribution.

### Data & Knowledge Repositories
- `data/` – canonical datasets following the Cookiecutter Data Science immutability rules (`raw/` is read-only, `processed/` feeds modeling/RAG, etc.).
- `references/` – persona briefs, dictionaries, and qualitative research artifacts.
- `docs/` – architecture materials, including `design.md` and this structure guide. The nested `docs/` directory contains MkDocs pages for publishing to a documentation site.
- `reports/` – generated deliverables; `reports/figures/` stores reusable charts.

### Source Code (`adsp/`)
- `fe/` – Frontend prototypes (e.g., chat client) that orchestrate authentication plus Q&A calls, reflecting the UI entry point from the system design.
- `app/` – Application layer services invoked by UI clients. Each module mirrors the services called out in the design: persona configuration, ingestion orchestration, report generation, Q&A routing, and authentication.
- `communication/` – RPC, cache, and message broker connectors that model the Communication layer of the architecture.
- `core/` – Home of the Orchestrator, prompt construction, memory, persona registry/router, and the MCP Server package that manages tool access via Model Context Protocol.
- `data_pipeline/` – ETL/RAG ingestion helpers that load PDFs/images, normalize them, and populate the vector store via a consistent schema.
- `modeling/` – Training/inference code for PEFT adapters (`training.py`, `train.py` CLI) and runtime persona inference (`inference.py`, `predict.py`).
- `monitoring/` – Evaluation suites plus lightweight metrics collection matching the Monitoring & Evaluation layer.
- `storage/` – Connectors for business databases, object storage, and the vector database abstraction.
- `utils/` – Cross-cutting helpers like logging configuration and custom exceptions.

### Testing
- `tests/` – Central place for automated regression and contract tests. As new modules go live, add suites here to cover their behavior.
