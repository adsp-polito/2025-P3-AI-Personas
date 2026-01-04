# Component Map (Architecture → Code)

This document maps the system architecture in `docs/md/design.md` to the current code layout under `adsp/`.

> Note: Several “services” are currently implemented as in-process Python classes (stubs/placeholders). The docs describe the current interfaces and also call out production-grade upgrades where the architecture expects distributed services.

## Layer map

| Architecture layer | Primary code location | Primary components (code) | Design docs |
|---|---|---|---|
| UI / Frontend | `adsp/fe/` | `ChatFrontend` | `docs/md/design/frontend/chat_frontend.md` |
| Application layer | `adsp/app/` | `AuthService`, `QAService`, `IngestionService`, `ReportService`, `PersonaConfigurationService`, REST API (`api_server.py`) | `docs/md/design/application/` |
| Communication layer | `adsp/communication/` | `RPCClient`, `CacheClient`, `EventBroker` | `docs/md/design/communication/` |
| Core layer | `adsp/core/` | `Orchestrator`, `InputHandler`, `PromptBuilder`, `PersonaRegistry`, `PersonaRouter`, `RAGPipeline`, `ConversationMemory`, `MCPServer` | `docs/md/design/core/` |
| Data pipeline (background) | `adsp/data_pipeline/` | persona extraction + schema + RAG indexing | `docs/md/design/data_pipeline/` |
| Modeling (background + runtime) | `adsp/modeling/` | `PersonaTrainer`, `PersonaInferenceEngine` | `docs/md/design/modeling/` |
| Monitoring & evaluation | `adsp/monitoring/` | `EvaluationSuite`, `MetricsCollector` | `docs/md/design/monitoring/` |
| Storage | `adsp/storage/` | `BusinessDatabase`, `object_store.put/get`, `VectorDatabase` | `docs/md/design/storage/` |

## Key end-to-end runtime flow (current implementation)

1. `ChatFrontend.send_message()` checks `AuthService.is_authorized()`
2. `QAService.ask()` instantiates `core.orchestrator.Orchestrator` and calls `Orchestrator.handle_query()`
3. `Orchestrator.handle_query()`:
   - normalizes input (`InputHandler.normalize`)
   - retrieves context (`RAGPipeline.retrieve`)
   - builds prompt (`PromptBuilder.build`)
   - dispatches to persona inference (`PersonaRouter.dispatch`)
   - stores conversation history (`ConversationMemory.store`)
   - caches response (`CacheClient.set`)

See: `docs/md/design/integration/end_to_end_flow.md`
