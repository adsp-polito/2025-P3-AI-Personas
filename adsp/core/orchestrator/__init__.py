"""Main coordination engine for persona responses."""

from __future__ import annotations

from dataclasses import dataclass, field
import time
from typing import Optional, TYPE_CHECKING

from loguru import logger

from adsp.communication.cache import CacheClient
from adsp.core.ai_persona_router import PersonaRouter
from adsp.core.context_filter import ConversationContextFilter
from adsp.core.input_handler import InputHandler
from adsp.core.memory import ConversationMemory
from adsp.core.prompt_builder import PromptBuilder
from adsp.core.rag import RAGPipeline
from adsp.core.types import ChatRequest, ChatResponse, RetrievedContext
from adsp.data_pipeline.schema import PersonaProfileModel

if TYPE_CHECKING:  # pragma: no cover
    from adsp.core.rag.fact_data_index import FactDataRAGIndex

_CONTEXT_SEPARATOR = "\n\n---\n\n"


def _split_context_blocks(context: str) -> list[str]:
    return [b.strip() for b in (context or "").split(_CONTEXT_SEPARATOR) if b.strip()]


def _join_context_blocks(blocks: list[str]) -> str:
    return _CONTEXT_SEPARATOR.join(block for block in blocks if block)


def _merge_retrieved_contexts(
    primary: RetrievedContext,
    secondary: RetrievedContext,
) -> RetrievedContext:
    primary_blocks = _split_context_blocks(primary.context)
    secondary_blocks = _split_context_blocks(secondary.context)

    merged_blocks = [*primary_blocks, *secondary_blocks]
    merged_citations = [*(primary.citations or []), *(secondary.citations or [])]

    primary_docs = (primary.raw or {}).get("documents")
    secondary_docs = (secondary.raw or {}).get("documents")
    merged_docs = []
    if isinstance(primary_docs, list):
        merged_docs.extend(primary_docs)
    if isinstance(secondary_docs, list):
        merged_docs.extend(secondary_docs)

    return RetrievedContext(
        context=_join_context_blocks(merged_blocks),
        citations=merged_citations,
        raw={"documents": merged_docs},
    )


@dataclass
class Orchestrator:
    """Wires together preprocessing, retrieval, routing, and memory."""

    input_handler: InputHandler = field(default_factory=InputHandler)
    context_filter: ConversationContextFilter = field(default_factory=ConversationContextFilter)
    prompt_builder: PromptBuilder = field(default_factory=PromptBuilder)
    retriever: RAGPipeline = field(default_factory=RAGPipeline)
    fact_data_index: Optional["FactDataRAGIndex"] = None
    router: PersonaRouter = field(default_factory=PersonaRouter)
    memory: ConversationMemory = field(default_factory=ConversationMemory)
    cache: CacheClient = field(default_factory=CacheClient)

    def _build_fact_data_query(self, *, persona_id: str, query: str) -> str:
        persona_name = None
        persona_summary = None
        try:
            persona = self.prompt_builder.registry.get(persona_id)
        except Exception:
            persona = None

        if isinstance(persona, PersonaProfileModel):
            persona_name = persona.persona_name
            persona_summary = persona.summary_bio
        elif isinstance(persona, dict):
            persona_name = persona.get("persona_name") if isinstance(persona.get("persona_name"), str) else None

        segment = (persona_name or persona_id or "").strip()
        if segment and segment != "default":
            summary = (persona_summary or "").strip()
            if len(summary) > 160:
                summary = summary[:157] + "..."
            parts = [f"Segment: {segment}", query]
            if summary:
                parts.insert(1, f"Persona summary: {summary}")
            return "\n".join(parts).strip()

        return query.strip()

    def handle(self, request: ChatRequest) -> ChatResponse:
        """Process a chat request end-to-end using the configured components."""

        start_total = time.perf_counter()

        # cache_key = f"{request.persona_id}:{request.session_id or 'default'}:{request.query}"
        # cached = self.cache.get(cache_key)
        # if isinstance(cached, ChatResponse):
        #     return cached
        # if isinstance(cached, str) and cached:
        #     return ChatResponse(persona_id=request.persona_id, answer=cached)

        start_step = time.perf_counter()
        normalized = self.input_handler.normalize(request.query)
        logger.debug(
            "orchestrator.normalize persona_id={} ms={:.2f}",
            request.persona_id,
            (time.perf_counter() - start_step) * 1000.0,
        )

        start_step = time.perf_counter()
        history = self.memory.get_history(persona_id=request.persona_id, session_id=request.session_id)
        logger.debug(
            "orchestrator.get_history persona_id={} session_id={} items={} ms={:.2f}",
            request.persona_id,
            request.session_id,
            len(history or []),
            (time.perf_counter() - start_step) * 1000.0,
        )

        start_step = time.perf_counter()
        persona_retrieved = self.retriever.retrieve_with_metadata(
            persona_id=request.persona_id, query=normalized, k=request.top_k
        )
        logger.debug(
            "orchestrator.retrieve_persona persona_id={} k={} context_chars={} citations={} ms={:.2f}",
            request.persona_id,
            request.top_k,
            len(persona_retrieved.context or ""),
            len(persona_retrieved.citations or []),
            (time.perf_counter() - start_step) * 1000.0,
        )
        merged_retrieved = persona_retrieved

        fact_retrieved: RetrievedContext | None = None

        if self.fact_data_index is not None:
            start_step = time.perf_counter()
            fact_query = self._build_fact_data_query(persona_id=request.persona_id, query=normalized)
            logger.debug(
                "orchestrator.build_fact_query persona_id={} k={} query_chars={} ms={:.2f}",
                request.persona_id,
                request.top_k,
                len(fact_query),
                (time.perf_counter() - start_step) * 1000.0,
            )
            try:
                start_step = time.perf_counter()
                fact_retrieved = self.fact_data_index.retrieve(fact_query, k=request.top_k)
                logger.debug(
                    "orchestrator.retrieve_fact_data persona_id={} k={} context_chars={} citations={} ms={:.2f}",
                    request.persona_id,
                    request.top_k,
                    len((fact_retrieved.context or "").strip()),
                    len(fact_retrieved.citations or []),
                    (time.perf_counter() - start_step) * 1000.0,
                )
            except Exception as exc:  # pragma: no cover - defensive retrieval
                logger.warning("Fact data retrieval failed: {}", exc)
                fact_retrieved = None

            if fact_retrieved and (fact_retrieved.context or "").strip():
                start_step = time.perf_counter()
                merged_retrieved = _merge_retrieved_contexts(persona_retrieved, fact_retrieved)
                logger.debug(
                    "orchestrator.merge_context persona_id={} merged_chars={} merged_citations={} ms={:.2f}",
                    request.persona_id,
                    len(merged_retrieved.context or ""),
                    len(merged_retrieved.citations or []),
                    (time.perf_counter() - start_step) * 1000.0,
                )

        start_step = time.perf_counter()
        filtered_history = self.context_filter.filter_history(history, normalized)
        logger.debug(
            "orchestrator.filter_history persona_id={} kept_items={} ms={:.2f}",
            request.persona_id,
            len(filtered_history or []),
            (time.perf_counter() - start_step) * 1000.0,
        )

        start_step = time.perf_counter()
        filtered_retrieved = self.context_filter.filter_retrieved(merged_retrieved, normalized)
        logger.debug(
            "orchestrator.filter_retrieved persona_id={} context_chars={} citations={} ms={:.2f}",
            request.persona_id,
            len(filtered_retrieved.context or ""),
            len(filtered_retrieved.citations or []),
            (time.perf_counter() - start_step) * 1000.0,
        )

        start_step = time.perf_counter()
        prompt = self.prompt_builder.build(
            persona_id=request.persona_id,
            query=normalized,
            context=filtered_retrieved.context,
            history=filtered_history,
            display_name=request.persona_display_name,
        )
        logger.debug(
            "orchestrator.build_prompt persona_id={} prompt_chars={} ms={:.2f}",
            request.persona_id,
            len(prompt),
            (time.perf_counter() - start_step) * 1000.0,
        )

        start_step = time.perf_counter()
        answer = self.router.dispatch(persona_id=request.persona_id, prompt=prompt)
        logger.debug(
            "orchestrator.dispatch persona_id={} answer_chars={} ms={:.2f}",
            request.persona_id,
            len(answer or ""),
            (time.perf_counter() - start_step) * 1000.0,
        )

        start_step = time.perf_counter()
        self.memory.store(
            persona_id=request.persona_id,
            session_id=request.session_id,
            message={"query": request.query, "response": answer},
        )
        logger.debug(
            "orchestrator.memory_store persona_id={} session_id={} ms={:.2f}",
            request.persona_id,
            request.session_id,
            (time.perf_counter() - start_step) * 1000.0,
        )
        response = ChatResponse(
            persona_id=request.persona_id,
            answer=answer,
            context=filtered_retrieved.context,
            citations=filtered_retrieved.citations,
        )
        logger.debug(
            "orchestrator.total persona_id={} ms={:.2f}",
            request.persona_id,
            (time.perf_counter() - start_total) * 1000.0,
        )
        # self.cache.set(cache_key, response)
        return response

    def handle_query(self, persona_id: str, query: str) -> str:
        """Backwards-compatible string-only entrypoint."""

        return self.handle(ChatRequest(persona_id=persona_id, query=query)).answer
