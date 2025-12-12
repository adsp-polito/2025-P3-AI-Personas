# Communication: `EventBroker`

**Code**: `adsp/communication/event_broker.py`

## Purpose

`EventBroker` models the event-driven part of the architecture (`docs/md/design.md`) where ingestion and background jobs communicate asynchronously.

## Responsibilities

- Allow subscribers to register callbacks for a topic
- Publish a payload to all subscribers for a topic

## Public API

### `subscribe(topic: str, handler: Callable) -> None`

Registers a handler to be called when `topic` receives a message.

### `publish(topic: str, payload: dict) -> None`

Invokes all registered handlers for `topic` with `payload`.

## Data model

- `_subscribers: DefaultDict[str, List[Callable]]` (in-memory)

## Key dependencies / technologies

- Python `dataclasses`
- `collections.defaultdict`

## Notes / production hardening

The architecture suggests RabbitMQ/Kafka. A production broker should provide:
- Durable queues/topics
- Retries, dead-letter queues
- Consumer groups / backpressure
- Observability (lag, throughput, failure counts)

Typical events in this system:
- `file_ingested` (object store key + metadata)
- `persona_extraction_requested` / `persona_extraction_completed`
- `rag_indexing_requested` / `rag_indexing_completed`

