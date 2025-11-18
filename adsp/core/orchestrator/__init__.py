"""Main coordination engine for persona responses."""

from __future__ import annotations

from dataclasses import dataclass, field

from adsp.communication.cache import CacheClient

from adsp.core.input_handler import InputHandler
from adsp.core.prompt_builder import PromptBuilder
from adsp.core.rag import RAGPipeline
from adsp.core.ai_persona_router import PersonaRouter
from adsp.core.memory import ConversationMemory


@dataclass
class Orchestrator:
    """Wires together preprocessing, retrieval, routing, and memory."""

    input_handler: InputHandler = field(default_factory=InputHandler)
    prompt_builder: PromptBuilder = field(default_factory=PromptBuilder)
    retriever: RAGPipeline = field(default_factory=RAGPipeline)
    router: PersonaRouter = field(default_factory=PersonaRouter)
    memory: ConversationMemory = field(default_factory=ConversationMemory)
    cache: CacheClient = field(default_factory=CacheClient)

    def handle_query(self, persona_id: str, query: str) -> str:
        """Process a query end-to-end using the configured components."""

        cache_key = f"{persona_id}:{query}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        normalized = self.input_handler.normalize(query)
        context = self.retriever.retrieve(persona_id=persona_id, query=normalized)
        prompt = self.prompt_builder.build(persona_id=persona_id, query=normalized, context=context)
        response = self.router.dispatch(persona_id=persona_id, prompt=prompt)
        self.memory.store(persona_id=persona_id, message={"query": query, "response": response})
        self.cache.set(cache_key, response)
        return response
