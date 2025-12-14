"""Filter conversation history and retrieved context for relevance."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
import re
from typing import Any, Dict, List, Optional, Sequence, Tuple

from adsp.core.types import RetrievedContext

_CONTEXT_SEPARATOR = "\n\n---\n\n"

_WORD_RE = re.compile(r"[a-zA-Z0-9]+(?:[-_][a-zA-Z0-9]+)?")
_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "can",
    "could",
    "do",
    "does",
    "for",
    "from",
    "have",
    "how",
    "i",
    "in",
    "is",
    "it",
    "its",
    "me",
    "my",
    "of",
    "on",
    "or",
    "our",
    "please",
    "so",
    "that",
    "the",
    "their",
    "them",
    "then",
    "there",
    "these",
    "they",
    "this",
    "to",
    "us",
    "was",
    "we",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "with",
    "you",
    "your",
}


def _env_flag(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        value = int(raw)
        return value if value > 0 else default
    except Exception:
        return default


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except Exception:
        return default


def _tokenize(text: str) -> List[str]:
    return [token.lower() for token in _WORD_RE.findall(text or "")]


def _meaningful_tokens(text: str) -> List[str]:
    return [t for t in _tokenize(text) if t not in _STOPWORDS]


def _token_coverage(query_tokens: Sequence[str], candidate_text: str) -> float:
    if not query_tokens:
        return 0.0
    query_set = set(query_tokens)
    cand_set = set(_meaningful_tokens(candidate_text))
    if not cand_set:
        return 0.0
    return len(query_set.intersection(cand_set)) / max(1, len(query_set))


def _looks_like_follow_up(query: str) -> bool:
    q = (query or "").strip().lower()
    if not q:
        return False
    if q.startswith(("and ", "also ", "so ", "then ", "what about", "how about")):
        return True
    raw_tokens = _tokenize(q)
    if any(token in {"it", "that", "this", "these", "those", "they", "them"} for token in raw_tokens):
        return True
    tokens = _meaningful_tokens(q)
    if not tokens:
        return True
    if len(tokens) == 1 and len(raw_tokens) <= 3:
        return True
    return False


def _split_context_blocks(context: str) -> List[str]:
    blocks = [b.strip() for b in (context or "").split(_CONTEXT_SEPARATOR)]
    return [b for b in blocks if b]


def _join_context_blocks(blocks: Sequence[str]) -> str:
    return _CONTEXT_SEPARATOR.join(b for b in blocks if b)


def _extract_json(text: str) -> Optional[str]:
    cleaned = (text or "").strip()
    if not cleaned:
        return None
    if "```" in cleaned:
        parts = [part.strip() for part in cleaned.split("```") if part.strip()]
        for part in parts:
            candidate = part
            if candidate.startswith("json"):
                candidate = candidate[len("json") :].strip()
            if candidate.startswith("{") and candidate.endswith("}"):
                return candidate
    if cleaned.startswith("{") and cleaned.endswith("}"):
        return cleaned
    match = re.search(r"(\{.*\})", cleaned, flags=re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


@dataclass
class ConversationContextFilter:
    """Filters memory + RAG context down to question-relevant snippets.

    Configuration (environment variables):
    - `ADSP_CONTEXT_FILTER_BACKEND`: `heuristic` (default) or `openai`
    - `ADSP_CONTEXT_FILTER_MAX_HISTORY`: max history turns passed to the prompt (default: 4)
    - `ADSP_CONTEXT_FILTER_MAX_BLOCKS`: max context blocks passed to the prompt (default: 3)
    - `ADSP_CONTEXT_FILTER_MIN_COVERAGE`: minimum token coverage score (default: 0.2)

    OpenAI backend (optional):
    - `ADSP_CONTEXT_FILTER_BASE_URL` (defaults to `ADSP_LLM_BASE_URL` / `VLLM_BASE_URL`)
    - `ADSP_CONTEXT_FILTER_MODEL` (defaults to `ADSP_LLM_MODEL` / `VLLM_MODEL`)
    - `ADSP_CONTEXT_FILTER_API_KEY` (defaults to `ADSP_LLM_API_KEY` / `VLLM_API_KEY`)
    """

    backend: str = field(
        default_factory=lambda: os.environ.get("ADSP_CONTEXT_FILTER_BACKEND", "heuristic")
    )
    max_history_items: int = field(default_factory=lambda: _env_int("ADSP_CONTEXT_FILTER_MAX_HISTORY", 10))
    max_context_blocks: int = field(default_factory=lambda: _env_int("ADSP_CONTEXT_FILTER_MAX_BLOCKS", 10))
    min_coverage: float = field(default_factory=lambda: _env_float("ADSP_CONTEXT_FILTER_MIN_COVERAGE", 0.2))

    base_url: str = field(
        default_factory=lambda: os.environ.get(
            "ADSP_CONTEXT_FILTER_BASE_URL",
            os.environ.get("ADSP_LLM_BASE_URL", os.environ.get("VLLM_BASE_URL", "")),
        )
    )
    model: str = field(
        default_factory=lambda: os.environ.get(
            "ADSP_CONTEXT_FILTER_MODEL",
            os.environ.get("ADSP_LLM_MODEL", os.environ.get("VLLM_MODEL", "")),
        )
    )
    api_key: str = field(
        default_factory=lambda: os.environ.get(
            "ADSP_CONTEXT_FILTER_API_KEY",
            os.environ.get("ADSP_LLM_API_KEY", os.environ.get("VLLM_API_KEY", "EMPTY")),
        )
    )
    timeout_s: float = field(default_factory=lambda: _env_float("ADSP_CONTEXT_FILTER_TIMEOUT", 30.0))
    enabled: bool = field(default_factory=lambda: _env_flag("ADSP_CONTEXT_FILTER_ENABLED", True))

    def filter_history(self, history: List[dict] | None, query: str) -> List[dict]:
        if not self.enabled or not history:
            return history or []

        if (self.backend or "").strip().lower() == "openai":
            selected = self._select_history_with_openai(query=query, history=history)
            if selected is not None:
                return [history[idx] for idx in selected if isinstance(history[idx], dict)]

        query_tokens = _meaningful_tokens(query)
        if _looks_like_follow_up(query) or not query_tokens:
            return [item for item in history[-2:] if isinstance(item, dict)]

        candidates = []
        for idx, item in enumerate(history):
            if not isinstance(item, dict):
                continue
            text = " ".join(str(item.get(key, "")) for key in ("query", "response") if item.get(key))
            score = _token_coverage(query_tokens, text)
            candidates.append((idx, score))

        candidates.sort(key=lambda pair: pair[1], reverse=True)
        keep = [idx for idx, score in candidates if score >= self.min_coverage][: self.max_history_items]
        keep.sort()
        return [history[idx] for idx in keep if isinstance(history[idx], dict)]

    def filter_retrieved(self, retrieved: RetrievedContext, query: str) -> RetrievedContext:
        if not self.enabled:
            return retrieved

        context = (retrieved.context or "").strip()
        if not context:
            return retrieved

        blocks = _split_context_blocks(context)
        if not blocks:
            return RetrievedContext(context="", citations=[], raw=retrieved.raw or {})

        context_keep: Optional[List[int]] = None
        if (self.backend or "").strip().lower() == "openai":
            context_keep = self._select_context_with_openai(query=query, context_blocks=blocks)

        if context_keep is None:
            context_keep = self._select_context_blocks_heuristic(query=query, context_blocks=blocks)

        kept_blocks = [blocks[i] for i in context_keep if 0 <= i < len(blocks)]
        filtered_context = _join_context_blocks(kept_blocks)

        citations = list(retrieved.citations or [])
        filtered_citations = [citations[i] for i in context_keep if 0 <= i < len(citations)]

        raw: Dict[str, Any] = dict(retrieved.raw or {})
        raw_docs = raw.get("documents")
        if isinstance(raw_docs, list):
            raw["documents"] = [raw_docs[i] for i in context_keep if 0 <= i < len(raw_docs)]

        raw["context_keep"] = context_keep

        return RetrievedContext(context=filtered_context, citations=filtered_citations, raw=raw)

    def _select_context_blocks_heuristic(self, query: str, context_blocks: Sequence[str]) -> List[int]:
        if _looks_like_follow_up(query):
            return list(range(min(self.max_context_blocks, len(context_blocks))))

        query_tokens = _meaningful_tokens(query)
        if not query_tokens:
            return []

        scored: List[Tuple[int, float]] = []
        for idx, block in enumerate(context_blocks):
            scored.append((idx, _token_coverage(query_tokens, block)))
        scored.sort(key=lambda pair: pair[1], reverse=True)

        keep = [idx for idx, score in scored if score >= self.min_coverage][: self.max_context_blocks]
        keep.sort()
        return keep

    def _select_history_with_openai(
        self,
        *,
        query: str,
        history: Sequence[dict],
    ) -> Optional[List[int]]:
        if not (self.base_url and self.model):
            return None
        try:
            from openai import OpenAI  # type: ignore
        except ImportError:
            return None

        client = OpenAI(base_url=self.base_url, api_key=self.api_key)
        items = []
        for idx, item in enumerate(history):
            if not isinstance(item, dict):
                continue
            q = str(item.get("query", "")).strip()
            a = str(item.get("response", "")).strip()
            combined = f"User: {q}\nPersona: {a}".strip()
            if len(combined) > 400:
                combined = combined[:397] + "..."
            items.append(f"[{idx}]\n{combined}")

        system = (
            "You select ONLY the conversation history turns needed to answer the user's question.\n"
            "Return JSON only with key keep_history: array of integer indices.\n"
            f"Choose at most {self.max_history_items} indices.\n"
            "If none are needed, return an empty array.\n"
        )
        user = "\n".join(
            [
                f"Question: {query.strip()}",
                "",
                "Conversation history (oldest to newest):",
                *items,
            ]
        ).strip()

        try:
            completion = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=0.0,
                max_tokens=200,
                timeout=self.timeout_s,
            )
            content = completion.choices[0].message.content or ""
        except Exception:
            return None

        payload = _extract_json(content)
        if not payload:
            return None
        try:
            data = json.loads(payload)
        except Exception:
            return None

        keep_history = data.get("keep_history")
        if not isinstance(keep_history, list):
            return None
        indices: List[int] = []
        for value in keep_history:
            try:
                idx = int(value)
            except Exception:
                continue
            if 0 <= idx < len(history):
                indices.append(idx)
        return sorted(set(indices))[: self.max_history_items]

    def _select_context_with_openai(
        self,
        *,
        query: str,
        context_blocks: Sequence[str],
    ) -> Optional[List[int]]:
        if not (self.base_url and self.model):
            return None
        try:
            from openai import OpenAI  # type: ignore
        except ImportError:
            return None

        client = OpenAI(base_url=self.base_url, api_key=self.api_key)
        block_summaries = []
        for idx, block in enumerate(context_blocks):
            snippet = " ".join(line.strip() for line in block.splitlines() if line.strip())
            if len(snippet) > 500:
                snippet = snippet[:497] + "..."
            block_summaries.append(f"[{idx}] {snippet}")

        system = (
            "You select ONLY the context blocks needed to answer the user's question.\n"
            "Return JSON only, with keys:\n"
            "- keep_context: array of integer indices\n"
            "Rules:\n"
            f"- Choose at most {self.max_context_blocks} indices.\n"
            "- If none are helpful, return an empty array.\n"
        )
        user = "\n".join(
            [
                f"Question: {query.strip()}",
                "",
                "Context blocks:",
                *block_summaries,
            ]
        ).strip()

        try:
            completion = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=0.0,
                max_tokens=200,
                timeout=self.timeout_s,
            )
            content = completion.choices[0].message.content or ""
        except Exception:
            return None

        payload = _extract_json(content)
        if not payload:
            return None
        try:
            data = json.loads(payload)
        except Exception:
            return None

        keep_context = data.get("keep_context")
        if not isinstance(keep_context, list):
            return None
        indices: List[int] = []
        for value in keep_context:
            try:
                idx = int(value)
            except Exception:
                continue
            if 0 <= idx < len(context_blocks):
                indices.append(idx)
        indices = sorted(set(indices))[: self.max_context_blocks]
        return indices


__all__ = ["ConversationContextFilter"]
