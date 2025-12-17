"""Main coordination engine for persona responses."""

from __future__ import annotations

from dataclasses import dataclass, field

from adsp.communication.cache import CacheClient
from adsp.core.ai_persona_router import PersonaRouter
from adsp.core.context_filter import ConversationContextFilter
from adsp.core.input_handler import InputHandler
from adsp.core.memory import ConversationMemory
from adsp.core.prompt_builder import PromptBuilder
from adsp.core.rag import RAGPipeline
from adsp.core.types import ChatRequest, ChatResponse


@dataclass
class Orchestrator:
    """Wires together preprocessing, retrieval, routing, and memory."""

    input_handler: InputHandler = field(default_factory=InputHandler)
    context_filter: ConversationContextFilter = field(default_factory=ConversationContextFilter)
    prompt_builder: PromptBuilder = field(default_factory=PromptBuilder)
    retriever: RAGPipeline = field(default_factory=RAGPipeline)
    router: PersonaRouter = field(default_factory=PersonaRouter)
    memory: ConversationMemory = field(default_factory=ConversationMemory)
    cache: CacheClient = field(default_factory=CacheClient)

    def handle(self, request: ChatRequest) -> ChatResponse:
        """Process a chat request end-to-end using the configured components."""

        # cache_key = f"{request.persona_id}:{request.session_id or 'default'}:{request.query}"
        # cached = self.cache.get(cache_key)
        # if isinstance(cached, ChatResponse):
        #     return cached
        # if isinstance(cached, str) and cached:
        #     return ChatResponse(persona_id=request.persona_id, answer=cached)

        normalized = self.input_handler.normalize(request.query)
        history = self.memory.get_history(persona_id=request.persona_id, session_id=request.session_id)
        retrieved = self.retriever.retrieve_with_metadata(
            persona_id=request.persona_id, query=normalized, k=request.top_k
        )
        filtered_history = self.context_filter.filter_history(history, normalized)
        filtered_retrieved = self.context_filter.filter_retrieved(retrieved, normalized)
        prompt = self.prompt_builder.build(
            persona_id=request.persona_id,
            query=normalized,
            context=filtered_retrieved.context,
            history=filtered_history,
        )
        answer = self.router.dispatch(persona_id=request.persona_id, prompt=prompt)
        self.memory.store(
            persona_id=request.persona_id,
            session_id=request.session_id,
            message={"query": request.query, "response": answer},
        )
        response = ChatResponse(
            persona_id=request.persona_id,
            answer=answer,
            context=filtered_retrieved.context,
            citations=filtered_retrieved.citations,
        )
        # self.cache.set(cache_key, response)
        return response

    def handle_query(self, persona_id: str, query: str) -> str:
        """Backwards-compatible string-only entrypoint."""

        return self.handle(ChatRequest(persona_id=persona_id, query=query)).answer
