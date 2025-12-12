# End-to-End Flow (Frontend → Core)

This describes the current in-process execution path for a single chat message.

## Call flow

1. `ChatFrontend.send_message(user, token, persona_id, message)`
2. `AuthService.is_authorized(user, token)`
3. `QAService.ask(persona_id, query)`
4. `Orchestrator.handle_query(persona_id, query)`
   - `InputHandler.normalize(query)`
   - `RAGPipeline.retrieve(persona_id, normalized_query)`
   - `PromptBuilder.build(persona_id, normalized_query, context)`
   - `PersonaRouter.dispatch(persona_id, prompt)`
   - `ConversationMemory.store(persona_id, {"query": ..., "response": ...})`
   - `CacheClient.get/set(cache_key)`

## Minimal usage example

```python
from adsp.app import AuthService, QAService
from adsp.fe import ChatFrontend

auth = AuthService()
auth.register("alice", "token123")

frontend = ChatFrontend(qa_service=QAService(), auth_service=auth)
print(frontend.send_message("alice", "token123", "default", "What do you think about this idea?"))
```

## How to extend (recommended)

- Add `session_id` to `ConversationMemory` so multiple conversations don’t collide under the same persona_id.
- Change `Orchestrator.handle_query()` to return a structured response (answer + citations + explanation) to support transparency.
- Implement “virtual focus group” fan-out:
  - accept `persona_ids: list[str]`
  - run orchestrator per persona and return an aggregated result

