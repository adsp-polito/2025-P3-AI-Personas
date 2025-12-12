"""Persona inference utilities wrapping PEFT adapters and RAG outputs.

This repo supports two runtime modes:
- A local, dependency-free stub generator (default) so the system can run end-to-end
  without an external LLM server.
- An OpenAI-compatible backend (e.g., vLLM) when `ADSP_LLM_BACKEND=openai` is set.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional, Tuple


@dataclass
class PersonaInferenceEngine:
    """Runtime inference engine.

    Configuration (environment variables):
    - `ADSP_LLM_BACKEND`: `stub` (default) or `openai`
    - `ADSP_LLM_BASE_URL`: OpenAI-compatible base URL (for `openai` backend)
    - `ADSP_LLM_MODEL`: model name (for `openai` backend)
    - `ADSP_LLM_API_KEY`: API key (can be dummy for local servers)
    """

    backend: str = field(default_factory=lambda: os.environ.get("ADSP_LLM_BACKEND", "stub"))
    base_url: str = field(
        default_factory=lambda: os.environ.get(
            "ADSP_LLM_BASE_URL", os.environ.get("VLLM_BASE_URL", "")
        )
    )
    model: str = field(
        default_factory=lambda: os.environ.get("ADSP_LLM_MODEL", os.environ.get("VLLM_MODEL", ""))
    )
    api_key: str = field(
        default_factory=lambda: os.environ.get(
            "ADSP_LLM_API_KEY", os.environ.get("VLLM_API_KEY", "EMPTY")
        )
    )
    temperature: float = field(default_factory=lambda: float(os.environ.get("ADSP_LLM_TEMPERATURE", "0.2")))
    max_tokens: int = field(default_factory=lambda: int(os.environ.get("ADSP_LLM_MAX_TOKENS", "512")))
    timeout_s: float = field(default_factory=lambda: float(os.environ.get("ADSP_LLM_TIMEOUT", "60")))

    def generate(self, persona_id: str, prompt: str) -> str:
        backend = (self.backend or "stub").strip().lower()
        if backend == "openai":
            answer = self._generate_openai(prompt)
            if answer:
                return answer
        return self._generate_stub(persona_id=persona_id, prompt=prompt)

    def _generate_openai(self, prompt: str) -> Optional[str]:
        if not (self.base_url and self.model):
            return None
        try:
            from openai import OpenAI  # type: ignore
        except ImportError:
            return None

        client = OpenAI(base_url=self.base_url, api_key=self.api_key)
        try:
            completion = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                timeout=self.timeout_s,
            )
            return completion.choices[0].message.content or ""
        except Exception:
            return None

    @staticmethod
    def _split_prompt(prompt: str) -> Tuple[str, str, str]:
        """Best-effort split of the prompt builder format."""

        system = prompt
        context = ""
        question = ""
        if "\n\nContext:\n" in prompt and "\n\nQuestion:\n" in prompt:
            system, rest = prompt.split("\n\nContext:\n", 1)
            context, question = rest.split("\n\nQuestion:\n", 1)
        return system, context, question

    def _generate_stub(self, persona_id: str, prompt: str) -> str:
        """Local fallback generator (non-LLM).

        This implementation is intentionally conservative:
        - If no retrieved context is available, it answers with a "not enough data" response.
        - If context exists, it quotes the most relevant retrieved blocks rather than inventing facts.
        """

        _system, context, question = self._split_prompt(prompt)
        context = (context or "").strip()
        question = (question or "").strip()

        if not context:
            return "I don't have enough data on this topic."

        blocks = [b.strip() for b in context.split("\n\n---\n\n") if b.strip()]
        evidence_lines = []
        for block in blocks[:3]:
            lines = [line.strip() for line in block.splitlines() if line.strip()]
            if not lines:
                continue
            # Keep the most informative part of the block.
            body = " ".join(lines[1:]) if len(lines) > 1 else lines[0]
            if len(body) > 220:
                body = body[:217] + "..."
            evidence_lines.append(f"- {body}")

        header = "Based on the available data:"
        if question:
            header = f"{header}\n\nQuestion: {question}"

        return "\n".join([header, *evidence_lines]).strip()
