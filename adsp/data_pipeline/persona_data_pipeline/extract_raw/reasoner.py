"""LLM-based persona reasoning to derive style/value/guardrail fields."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Sequence, Tuple

from loguru import logger

from .alignment_prompts import ALIGNMENT_SYSTEM_PROMPT, ALIGNMENT_USER_TEMPLATE
from .config import PersonaExtractionConfig
from .utils import strip_json_markdown


class PersonaReasoner:
    def __init__(self, config: PersonaExtractionConfig):
        try:
            from openai import OpenAI  # type: ignore
        except ImportError as exc:  # pragma: no cover - import guard
            raise ImportError(
                "openai client is required for persona reasoning. Install with `pip install openai`."
            ) from exc

        self.model = config.reasoning_model or config.vllm_model
        self.base_url = config.reasoning_base_url or config.vllm_base_url
        self.api_key = config.reasoning_api_key or config.vllm_api_key
        self.enabled = bool(config.generate_reasoning_profiles and self.model)
        self.max_concurrent = max(1, getattr(config, "reasoning_max_concurrent", 1))
        self.client = OpenAI(base_url=self.base_url, api_key=self.api_key)
        self.temperature = config.reasoning_temperature
        self.top_p = config.reasoning_top_p
        self.max_tokens = config.reasoning_max_tokens
        self.max_input_chars = config.reasoning_max_input_chars

    def process(
        self,
        personas: Dict[str, Dict[str, Any]],
        output_dir,
        reuse_cache: bool = True,
    ) -> Dict[str, Dict[str, Any]]:
        if not self.enabled:
            logger.info("Reasoning profiles disabled or reasoning model not set; skipping enrichment.")
            return {}

        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(
            f"Enriching {len(personas)} personas via reasoning model {self.model} "
            f"@ {self.base_url} (max_workers={self.max_concurrent})"
        )

        results: Dict[str, Dict[str, Any]] = {}
        with ThreadPoolExecutor(max_workers=self.max_concurrent) as executor:
            future_map = {
                executor.submit(
                    self._process_single_persona,
                    persona_id,
                    persona,
                    output_dir,
                    reuse_cache,
                ): persona_id
                for persona_id, persona in personas.items()
            }
            for future in as_completed(future_map):
                persona_id = future_map[future]
                try:
                    result = future.result()
                    if result:
                        results[persona_id] = result
                except Exception as exc:  # pragma: no cover - defensive
                    logger.warning(f"Failed to enrich persona {persona_id}: {exc}")
        return results

    def _process_single_persona(
        self,
        persona_id: str,
        persona: Dict[str, Any],
        output_dir,
        reuse_cache: bool,
    ) -> Optional[Dict[str, Any]]:
        path = output_dir / f"{persona_id}.json"
        if reuse_cache and path.exists():
            try:
                cached = json.loads(path.read_text(encoding="utf-8"))
                logger.info(f"[Reasoning] Reusing cached profile for persona_id={persona_id}")
                return cached
            except Exception:
                logger.warning(f"[Reasoning] Failed to load cached profile for {persona_id}, regenerating.")

        logger.info(f"[Reasoning] Start persona_id={persona_id}")
        key_indicators = self._collect_key_indicators(persona)
        profile = self._build_profile(persona, key_indicators)
        payload = {
            "persona_id": persona_id,
            "persona_name": persona.get("persona_name"),
            "summary_bio": persona.get("summary_bio"),
            "key_indicators": key_indicators,
        }
        if profile:
            payload.update(profile)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info(
            f"[Reasoning] Done persona_id={persona_id} (salient={len(key_indicators)}) -> {path}"
        )
        return payload

    def _collect_key_indicators(self, persona: Dict[str, Any]) -> List[dict]:
        """
        This method filters through all of a persona's indicators and statements to find only the "salient" ones (where
        salience.is_salient is true). These key indicators are the evidence fed to the reasoning model
        """
        indicators: List[dict] = []
        for indicator in persona.get("indicators") or []:
            if not isinstance(indicator, dict):
                continue
            for stmt in indicator.get("statements") or []:
                if not isinstance(stmt, dict):
                    continue
                salience = stmt.get("salience") or {}
                if not isinstance(salience, dict) or not salience.get("is_salient"):
                    continue
                indicators.append(
                    {
                        "indicator_id": indicator.get("id"),
                        "indicator_label": indicator.get("label"),
                        "indicator_category": indicator.get("category"),
                        "indicator_domain": indicator.get("domain"),
                        "statement_label": stmt.get("label"),
                        "statement_description": stmt.get("description"),
                        "metrics": stmt.get("metrics"),
                        "salience": salience,
                        "influences": stmt.get("influences"),
                        "sources": indicator.get("sources"),
                    }
                )
        return indicators

    def _build_profile(self, persona: Dict[str, Any], key_indicators: List[dict]) -> Dict[str, Any]:
        """
        Orchestrates the reasoning call. It formats the ALIGNMENT_USER_TEMPLATE with the key indicators and calls the LLM via
        the _invoke method. It also handles chunking the indicators if they are too large to fit in a single prompt
        """
        if not key_indicators:
            logger.info(f"No salient indicators for persona {persona.get('persona_id')}; skipping reasoning.")
            return {}

        chunks = self._chunk_key_indicators(key_indicators, self.max_input_chars)
        aggregated: Dict[str, Any] = {}
        for idx, chunk in enumerate(chunks, start=1):
            logger.info(
                f"[Reasoning] persona_id={persona.get('persona_id')} chunk {idx}/{len(chunks)} "
                f"items={len(chunk)}"
            )
            prompt = ALIGNMENT_USER_TEMPLATE.format(
                persona_id=persona.get("persona_id"),
                persona_name=persona.get("persona_name"),
                summary_bio=persona.get("summary_bio", ""),
                key_indicators=json.dumps(chunk, ensure_ascii=False, indent=2),
                partial_profile=json.dumps(aggregated, ensure_ascii=False, indent=2) if aggregated else "{}",
            )
            response = self._invoke(prompt)
            if response:
                aggregated = self._merge_profiles(aggregated, response)
        return aggregated

    def _invoke(self, prompt: str) -> Optional[Dict[str, Any]]:
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": ALIGNMENT_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=self.temperature,
                top_p=self.top_p,
                max_tokens=self.max_tokens,
            )
            raw = completion.choices[0].message.content or ""
            cleaned = strip_json_markdown(raw)
            for candidate in self._candidate_json_strings(cleaned):
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    continue
            raise ValueError("Could not parse reasoning model response as JSON.")
        except Exception as exc:  # pragma: no cover - external call
            logger.warning(f"Reasoning call failed: {exc}")
            return None

    @staticmethod
    def _candidate_json_strings(text: str) -> List[str]:
        candidates = [text]
        if "{" in text and "}" in text:
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                candidates.append(text[start : end + 1])
        if "[" in text and "]" in text:
            start = text.find("[")
            end = text.rfind("]")
            if start != -1 and end != -1 and end > start:
                candidates.append(text[start : end + 1])
        return candidates

    def _chunk_key_indicators(self, items: Sequence[dict], limit: int) -> List[List[dict]]:
        if limit <= 0:
            return [list(items)]
        batches: List[List[dict]] = []
        current: List[dict] = []
        current_len = 0
        for item in items:
            serialized = json.dumps(item, ensure_ascii=False)
            if current and current_len + len(serialized) > limit:
                batches.append(current)
                current = []
                current_len = 0
            current.append(item)
            current_len += len(serialized)
        if current:
            batches.append(current)
        return batches

    def _merge_profiles(self, base: Dict[str, Any], incoming: Dict[str, Any]) -> Dict[str, Any]:
        """
        A specialized deep-merge function to combine reasoning results if the indicators were processed in multiple chunks
        """
        if not base:
            return incoming or {}
        result = json.loads(json.dumps(base))  # deep copy

        def merge_list(field: str, target: Dict[str, Any], source: Dict[str, Any]) -> None:
            if field not in source:
                return
            existing = target.get(field, [])
            if not isinstance(existing, list):
                existing = []
            incoming_list = source.get(field) or []
            merged = []
            seen = set()
            for item in [*existing, *incoming_list]:
                marker = json.dumps(item, sort_keys=True) if not isinstance(item, (str, int, float)) else item
                if marker in seen:
                    continue
                seen.add(marker)
                merged.append(item)
            target[field] = merged

        def merge_scalar(field: str, target: Dict[str, Any], source: Dict[str, Any]) -> None:
            val = source.get(field)
            if val not in (None, "", []):
                if target.get(field) in (None, "", []):
                    target[field] = val

        def merge_section(section: str, fields: List[str], list_fields: List[str]) -> None:
            src_section = incoming.get(section)
            if not isinstance(src_section, dict):
                return
            tgt_section = result.setdefault(section, {})
            for lf in list_fields:
                merge_list(lf, tgt_section, src_section)
            for sf in fields:
                merge_scalar(sf, tgt_section, src_section)

        merge_section(
            "style_profile",
            [
                "formality_level",
                "directness",
                "emotional_flavour",
                "criticality_level",
                "verbosity_preference",
            ],
            ["tone_adjectives", "preferred_structures", "typical_register_examples"],
        )
        merge_section(
            "value_frame",
            [
                "sustainability_orientation",
                "price_sensitivity",
                "novelty_seeking",
                "brand_loyalty",
                "health_concern",
                "description",
            ],
            ["priority_rank"],
        )

        rp_src = incoming.get("reasoning_policies")
        if isinstance(rp_src, dict):
            rp_tgt = result.setdefault("reasoning_policies", {})
            for sub in ("purchase_advice", "product_evaluation", "information_processing"):
                sub_src = rp_src.get(sub)
                if not isinstance(sub_src, dict):
                    continue
                sub_tgt = rp_tgt.setdefault(sub, {})
                for lf in (
                    "default_biases",
                    "tradeoff_rules",
                    "praise_triggers",
                    "criticism_triggers",
                    "must_always_check",
                    "trust_preference",
                    "scepticism_towards",
                ):
                    merge_list(lf, sub_tgt, sub_src)
                merge_scalar("requested_rigor_level", sub_tgt, sub_src)

        cf_src = incoming.get("content_filters")
        if isinstance(cf_src, dict):
            cf_tgt = result.setdefault("content_filters", {})
            merge_list("avoid_styles", cf_tgt, cf_src)
            merge_list("emphasise_disclaimers_on", cf_tgt, cf_src)

        return result
