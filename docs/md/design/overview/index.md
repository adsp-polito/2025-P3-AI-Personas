# Design Deep Dives

This folder breaks down the high-level architecture in `docs/md/design.md` into per-component design documents.

## How to read these docs

1. Start with `docs/md/design/overview/component_map.md` to understand how architecture layers map to code.
2. Use the layer folders (`frontend/`, `core/`, `data_pipeline/`, etc.) to deep-dive into each component’s logic and interface.
3. Use `docs/md/design/integration/` docs to run workflows end-to-end and understand how components connect.

## Layers

- Frontend: `docs/md/design/frontend/chat_frontend.md`
- Application services: `docs/md/design/application/auth_service.md`, `docs/md/design/application/qa_service.md`, ...
- REST API server: `docs/md/design/application/rest_api_server.md`
- Communication: `docs/md/design/communication/cache_client.md`, `docs/md/design/communication/event_broker.md`, `docs/md/design/communication/rpc_client.md`
- Core: `docs/md/design/core/orchestrator.md` (plus prompt/RAG/router/memory)
- Data pipeline: `docs/md/design/data_pipeline/persona_extraction_pipeline.md` (plus renderer/extractor/merger/reasoner)
- Storage: `docs/md/design/storage/object_store.md`, `docs/md/design/storage/vector_database.md`, `docs/md/design/storage/business_database.md`
- Modeling: `docs/md/design/modeling/persona_inference_engine.md`, `docs/md/design/modeling/persona_trainer.md`
- Monitoring: `docs/md/design/monitoring/evaluation_suite.md`, `docs/md/design/monitoring/metrics_collector.md`
