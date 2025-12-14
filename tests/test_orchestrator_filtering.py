from dataclasses import dataclass

from adsp.core.context_filter import ConversationContextFilter
from adsp.core.memory import ConversationMemory
from adsp.core.orchestrator import Orchestrator
from adsp.core.types import ChatRequest, Citation, RetrievedContext


class CapturingPromptBuilder:
    def __init__(self) -> None:
        self.last_context: str | None = None
        self.last_history: list[dict] | None = None

    def build(self, persona_id: str, query: str, context: str, history: list[dict] | None = None) -> str:
        self.last_context = context
        self.last_history = history or []
        return "PROMPT"


@dataclass
class FakeRetriever:
    retrieved: RetrievedContext

    def retrieve_with_metadata(self, persona_id: str, query: str, *, k: int = 5) -> RetrievedContext:  # noqa: ARG002
        return self.retrieved


class FakeRouter:
    def dispatch(self, persona_id: str, prompt: str) -> str:  # noqa: ARG002
        return "ANSWER"


def test_orchestrator_filters_history_and_context():
    memory = ConversationMemory()
    memory.store(
        persona_id="p1",
        session_id="s1",
        message={"query": "Where is it located?", "response": "Near the city center."},
    )
    memory.store(
        persona_id="p1",
        session_id="s1",
        message={"query": "What about price?", "response": "Cheap and good value."},
    )

    context = "\n\n---\n\n".join(
        [
            "Persona: X | Indicator: Price\nPrice range is low.",
            "Persona: X | Indicator: Location\nLocated near the city center.",
        ]
    )
    retrieved = RetrievedContext(
        context=context,
        citations=[
            Citation(indicator_id="price"),
            Citation(indicator_id="location"),
        ],
        raw={"documents": [{"id": "price"}, {"id": "location"}]},
    )

    prompt_builder = CapturingPromptBuilder()
    orchestrator = Orchestrator(
        prompt_builder=prompt_builder,  # type: ignore[arg-type]
        retriever=FakeRetriever(retrieved=retrieved),  # type: ignore[arg-type]
        router=FakeRouter(),  # type: ignore[arg-type]
        memory=memory,
        context_filter=ConversationContextFilter(),
    )

    response = orchestrator.handle(
        ChatRequest(persona_id="p1", query="price range", session_id="s1", top_k=5)
    )

    assert prompt_builder.last_history is not None
    assert len(prompt_builder.last_history) == 1
    assert "price" in (prompt_builder.last_history[0].get("query") or "").lower()

    assert prompt_builder.last_context is not None
    assert "Price range is low." in prompt_builder.last_context
    assert "Located near the city center." not in prompt_builder.last_context

    assert response.context == prompt_builder.last_context
    assert len(response.citations) == 1
    assert response.citations[0].indicator_id == "price"
