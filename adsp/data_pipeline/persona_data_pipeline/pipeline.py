"""Persona extraction pipeline using a vision LLM to map PDF pages to persona schema patches."""

from __future__ import annotations

import base64
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

from loguru import logger

from adsp import config

try:
    from adsp.data_pipeline.schema import PersonaProfileModel
    from pydantic import ValidationError
except ImportError as exc:  # pragma: no cover - import guard
    raise ImportError(
        "pydantic is required for the persona extraction pipeline. "
        "Install with `pip install pydantic`."
    ) from exc

SYSTEM_PROMPT = (
    "You extract persona data into the PersonaProfileModel schema. "
    "Top-level keys: persona_id, segment_name, locale, "
    "source_reference{document,pages,extraction_notes}, "
    "core_profile_overview{market_impact{population_share_percentage,value_share_percentage,"
    "spend_at_home_index},identity_summary{demographics,psychographics},"
    "sustainability_attitude{statement,index},"
    "consumption_habits{at_home{volume{average_daily_coffees,index},behavior_description},"
    "out_of_home{volume{average_daily_coffees,index},behavior_description}},"
    "shopping_attitude{statement,index},innovation_interest{summary}}, "
    "demographics{gender_distribution{female{percentage,index},male{percentage,index}},"
    "age_distribution[{range,percentage,index}],average_age,"
    "household_size[{members,percentage,index}],"
    "region_distribution[{region,percentage,index}],"
    "area_of_living[{area,percentage,index}],"
    "income_distribution{low{percentage,index},medium{percentage,index},high{percentage,index},"
    "average_income_eur,average_income_index,income_brackets[{range,percentage,index}]},"
    "education_level[{level,percentage,index}],profession_distribution[{role,percentage,index}],"
    "coffee_purchase_decision{primary_decision_maker{percentage,index},"
    "shared_decision_maker{percentage,index}}}, "
    "values_and_attitudes{lifestyle_statements[{statement,agreement_percentage,index}],"
    "coffee_attitudes[{statement,agreement_percentage,index}]}, "
    "sustainability_attitudes[{statement,agreement_percentage,index}], "
    "coffee_consumption_traits{needstates{at_home[{label,percentage,index}],"
    "out_of_home[{label,percentage,index}]},consumption_moment{at_home_only{percentage,index},"
    "out_of_home_only{percentage,index},combined{percentage,index}},"
    "time_of_consumption{at_home[{moment,percentage,index}],"
    "out_of_home[{moment,percentage,index}]},"
    "coffee_choice_motivations[{reason,total_segment{percentage,index},"
    "bean_users{percentage,index}}],type_of_coffee_used[{type,percentage,index}],"
    "preparation_method[{system,percentage,index}],"
    "consumption_metrics{average_daily_coffees_at_home{value,index},"
    "average_daily_coffees_out_of_home{value,index}},"
    "purchasing_habits{amount_spend_per_purchase[{bracket,percentage,index}],"
    "average_spend{value_eur,index},shopping_frequency[{frequency,percentage,index}],"
    "average_frequency_days{value,index}},"
    "channel_preferences{physical_and_general[{channel,percentage,index}],"
    "online_breakdown[{site_type,percentage,index}]},"
    "brand_landscape{top_competitors_household_penetration[{brand,percentage,index}],"
    "sub_brand_deep_dive{lavazza[{sub_brand,percentage,index}],"
    "carte_noire[{sub_brand,percentage,index}]}}}, "
    "brand_perception{brands[{brand_name,brand_share_percentage,metrics{brand_share_percentage,"
    "buy_regularly_score,trial_score,awareness_score},"
    "conversion_rates{trial_to_buy_regularly,awareness_to_trial},"
    "sub_brand_funnels[{sub_brand_name,metrics{brand_share_percentage,awareness,trial,"
    "buy_regularly},conversion_rates{awareness_to_trial,trial_to_buy_regularly}}]}]}, "
    "machine_ownership_behavior{penetration_methods[{method,percentage,index}],"
    "machine_currently_owned[{machine,percentage,index}],"
    "machine_previously_owned[{machine,percentage,index}],"
    "reasons_for_switching_machineS[{reason,percentage,index}],"
    "capsule_machine_motivations{reasons_for_owning_machine[{reason,percentage,index}],"
    "reasons_for_not_owning_machine[{reason,percentage,index}]},"
    "capsule_machine_brand_ownership[{brand,percentage,index}],"
    "machine_price_sensitivity{"
    "electric_machine_with_beans_investment[{price_bracket,percentage,index}],"
    "electric_machine_with_capsules_investment[{price_bracket,percentage,index}]}}, "
    "innovation{top_concepts[{rank,concept_description,percentage,index}]}, "
    "lifestyle{attitudes[{statement,agreement_percentage,index_vs_coffee_drinkers,"
    "index_vs_all_adults}]}, "
    "sport_and_leisure{outings_and_activities[{activity,percentage,index_vs_coffee,"
    "index_vs_adults}],"
    "hobbies_and_interests[{activity,percentage,index_vs_coffee,index_vs_adults}],"
    "leisure_attitudes[{statement,percentage,index_vs_coffee,index_vs_adults}],"
    "sports{interest_in_sports[{sport,percentage,index_vs_coffee,index_vs_adults}],"
    "active_participation_sports[{sport,percentage,index_vs_coffee,index_vs_adults}],"
    "active_participation_fitness[{activity,percentage,index_vs_coffee,index_vs_adults}]}}, "
    "media{media_penetration_channels[{channel,penetration_percentage,index_vs_coffee_drinkers,"
    "index_vs_all_adults}],technology_attitudes[{statement,agreement_percentage,"
    "index_vs_coffee_drinkers,index_vs_all_adults}],"
    "channel_usage_intensity[{channel,usage_level,percentage,index_vs_coffee_drinkers,"
    "index_vs_all_adults}],content_preferences{television_genres[{genre,percentage,"
    "index_vs_coffee_drinkers,index_vs_all_adults}],film_genres[{genre,percentage,"
    "index_vs_coffee_drinkers,index_vs_all_adults}],podcast_genres[{genre,percentage,"
    "index_vs_coffee_drinkers,index_vs_all_adults}],radio_programmes[{genre,percentage,"
    "index_vs_coffee_drinkers,index_vs_all_adults}],"
    "newspaper_topics[{topic,percentage,index_vs_coffee_drinkers,index_vs_all_adults}]},"
    "internet_consumption_profile{social_media_behavior{time_spent_frequency[{frequency,"
    "percentage,vs_coffee_drinkers}],brands_used[{platform,penetration,index_vs_coffee,"
    "index_vs_adults}]},"
    "online_research_topics[{topic,percentage,description}],"
    "device_usage[{device,penetration,index_vs_coffee,index_vs_adults}],"
    "website_visitation_last_4_weeks[{site,penetration,index_vs_coffee,index_vs_adults}],"
    "online_activities_daily[{activity,penetration,index_vs_coffee}]}}. "
    "Return ONLY JSON with keys persona_id, patch, page, notes. "
    "Respond with a single JSON object only; no prose or markdown. "
    "Use numbers for numeric values. "
    "Never include null/empty keys—omit any field not present on the page. "
    "If no persona data appears, return persona_id null and patch {} (no null fields)."
)


@dataclass
class PersonaExtractionConfig:
    pdf_path: Path = config.DATA_DIR / "raw" / "lavazza" / "customer-segmentation" / (
        "2023 03_FR_Consumers Segmentation France.pdf"
    )
    page_images_dir: Path = (
        config.INTERIM_DATA_DIR / "persona_extraction" / "page_images"
    )
    raw_responses_dir: Path = config.INTERIM_DATA_DIR / "persona_extraction" / "pages"
    merged_output_path: Path = config.PROCESSED_DATA_DIR / "personas" / "personas.json"
    qa_report_path: Path = config.INTERIM_DATA_DIR / "persona_extraction" / "qa_report.json"
    debug: bool = False
    debug_dir: Path = config.INTERIM_DATA_DIR / "persona_extraction" / "debug"

    vllm_base_url: str = field(
        default_factory=lambda: os.environ.get("VLLM_BASE_URL", "http://localhost:8000/v1")
    )
    vllm_model: str = field(default_factory=lambda: os.environ.get("VLLM_MODEL", ""))
    vllm_api_key: str = field(default_factory=lambda: os.environ.get("VLLM_API_KEY", "EMPTY"))
    temperature: float = 0.0
    top_p: float = 0.01
    max_tokens: int = 4000
    response_timeout: float = 300.0
    max_concurrent_requests: int = 1
    max_retries: int = 1
    backoff_seconds: float = 1.5
    dpi: int = 300
    page_range: Optional[tuple[int, int]] = None  # inclusive 1-based page range
    merge_strategy: Dict[str, str] = field(
        default_factory=dict
    )  # dotted path -> fill|overwrite|append


@dataclass
class PageImage:
    page_number: int  # 1-based
    image_path: Path
    width: int
    height: int


@dataclass
class PageExtractionResult:
    page_number: int
    raw_text: str
    parsed: Optional[dict]
    persona_id: Optional[str]
    patch: Dict[str, Any]
    error: Optional[str] = None


def _strip_json_markdown(text: str) -> str:
    """Extract JSON content from possible markdown fences."""
    if "```" not in text:
        return text.strip()
    blocks: List[str] = []
    for part in text.split("```"):
        cleaned = part.strip()
        if not cleaned:
            continue
        if cleaned.startswith("json"):
            cleaned = cleaned[len("json") :].strip()
        blocks.append(cleaned)
    # Prefer the first block that looks like JSON; fallback to longest block.
    for block in blocks:
        if block.startswith("{") or block.startswith("["):
            return block
    if blocks:
        return max(blocks, key=len)
    return text.strip()


def _encode_image_base64(image_path: Path) -> str:
    with image_path.open("rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


class PDFRenderer:
    def __init__(self, dpi: int = 300):
        self.dpi = dpi

    def render(
        self, pdf_path: Path, output_dir: Path, page_range: Optional[tuple[int, int]] = None
    ) -> List[PageImage]:
        output_dir.mkdir(parents=True, exist_ok=True)
        try:
            import fitz  # type: ignore

            return self._render_with_pymupdf(pdf_path, output_dir, page_range)
        except ImportError:
            try:
                return self._render_with_pdf2image(pdf_path, output_dir, page_range)
            except ImportError as exc:
                raise ImportError(
                    "Install `pymupdf` or `pdf2image` to render PDF pages. "
                    "Example: pip install pymupdf pdf2image"
                ) from exc
        except Exception as exc:  # pragma: no cover - rendering fallback
            logger.error(f"Failed to render PDF with PyMuPDF: {exc}")
            raise

    def _render_with_pymupdf(
        self, pdf_path: Path, output_dir: Path, page_range: Optional[tuple[int, int]]
    ) -> List[PageImage]:
        import fitz  # type: ignore

        doc = fitz.open(pdf_path)
        start, end = page_range if page_range else (1, doc.page_count)
        images: List[PageImage] = []

        for page_idx in range(start - 1, end):
            page = doc.load_page(page_idx)
            pix = page.get_pixmap(dpi=self.dpi)
            out_path = output_dir / f"page_{page_idx + 1:04d}.png"
            pix.save(out_path)
            images.append(
                PageImage(
                    page_number=page_idx + 1,
                    image_path=out_path,
                    width=pix.width,
                    height=pix.height,
                )
            )
            logger.debug(f"Rendered page {page_idx + 1} -> {out_path}")
        return images

    def _render_with_pdf2image(
        self, pdf_path: Path, output_dir: Path, page_range: Optional[tuple[int, int]]
    ) -> List[PageImage]:
        from pdf2image import convert_from_path  # type: ignore

        start, end = page_range if page_range else (1, None)
        images = convert_from_path(
            pdf_path,
            dpi=self.dpi,
            first_page=start,
            last_page=end,
        )
        page_images: List[PageImage] = []
        for idx, image in enumerate(images, start=start):
            out_path = output_dir / f"page_{idx:04d}.png"
            image.save(out_path, "PNG")
            page_images.append(
                PageImage(
                    page_number=idx,
                    image_path=out_path,
                    width=image.width,
                    height=image.height,
                )
            )
            logger.debug(f"Rendered page {idx} -> {out_path}")
        return page_images


class VLLMOpenAIExtractor:
    def __init__(self, config: PersonaExtractionConfig):
        try:
            from openai import OpenAI  # type: ignore
        except ImportError as exc:  # pragma: no cover - import guard
            raise ImportError(
                "openai client is required for persona extraction. "
                "Install with `pip install openai`."
            ) from exc

        self.client = OpenAI(base_url=config.vllm_base_url, api_key=config.vllm_api_key)
        self.model = config.vllm_model
        self.temperature = config.temperature
        self.top_p = config.top_p
        self.max_tokens = config.max_tokens
        self.response_timeout = config.response_timeout
        self.max_retries = config.max_retries
        self.backoff_seconds = config.backoff_seconds
        self.max_concurrent = max(1, config.max_concurrent_requests)
        if not self.model:
            raise ValueError(
                "Set VLLM_MODEL to the OpenAI-compatible vision model name (e.g., llava)."
            )

    def extract_pages(self, pages: Sequence[PageImage]) -> List[PageExtractionResult]:
        if not pages:
            return []
        results: List[PageExtractionResult] = []
        with ThreadPoolExecutor(max_workers=self.max_concurrent) as executor:
            future_map = {executor.submit(self._extract_single_page, page): page for page in pages}
            for future in as_completed(future_map):
                results.append(future.result())
        return sorted(results, key=lambda r: r.page_number)

    def _extract_single_page(self, page: PageImage) -> PageExtractionResult:
        encoded_image = _encode_image_base64(page.image_path)
        content = {
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{encoded_image}"},
        }
        last_error: Optional[str] = None
        raw_text = ""
        for attempt in range(1, self.max_retries + 1):  # max_retries + initial try
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "Extract persona patch for this page."},
                                content,
                            ],
                        },
                    ],
                    temperature=self.temperature,
                    top_p=self.top_p,
                    max_tokens=self.max_tokens,
                    timeout=self.response_timeout,
                )
                raw_text = response.choices[0].message.content or ""
                parsed = self._parse_raw_response(raw_text)
                if parsed is None:
                    raise ValueError("Model returned unparsable JSON.")
                persona_id = parsed.get("persona_id")
                patch = parsed.get("patch") or {}
                return PageExtractionResult(
                    page_number=page.page_number,
                    raw_text=raw_text,
                    parsed=parsed,
                    persona_id=persona_id,
                    patch=patch,
                    error=None,
                )
            except Exception as exc:  # pragma: no cover - external call
                last_error = str(exc)
                logger.warning(
                    (
                        f"Extraction failed for page {page.page_number} "
                        f"(attempt {attempt}/{self.max_retries}): {exc}"
                    )
                )
                if attempt > self.max_retries:
                    break
                time.sleep(self.backoff_seconds * attempt)

        return PageExtractionResult(
            page_number=page.page_number,
            raw_text=raw_text,
            parsed=None,
            persona_id=None,
            patch={},
            error=last_error,
        )

    @staticmethod
    def _parse_raw_response(raw_text: str) -> Optional[dict]:
        cleaned = _strip_json_markdown(raw_text)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return None


class PersonaMerger:
    def __init__(self, document_name: str, merge_strategy: Optional[Dict[str, str]] = None):
        self.document_name = document_name
        self.merge_strategy = merge_strategy or {}
        self.personas: Dict[str, Dict[str, Any]] = {}
        self.parse_failures: List[dict] = []

    def apply_page_result(self, result: PageExtractionResult) -> None:
        if result.error:
            self.parse_failures.append(
                {"page": result.page_number, "error": result.error, "raw": result.raw_text}
            )
            return
        if not result.persona_id:
            return
        persona = self.personas.setdefault(
            result.persona_id,
            {
                "persona_id": result.persona_id,
                "source_reference": {
                    "document": self.document_name,
                    "pages": [],
                    "extraction_notes": "",
                },
            },
        )
        source_refs = persona.setdefault("source_reference", {})
        pages = source_refs.setdefault("pages", [])
        if result.page_number not in pages:
            pages.append(result.page_number)
        if result.parsed and result.parsed.get("notes"):
            note = result.parsed["notes"]
            existing = source_refs.get("extraction_notes") or ""
            source_refs["extraction_notes"] = (
                f"{existing}\nPage {result.page_number}: {note}"
            ).strip()
        self._deep_merge(persona, result.patch, parent_path="")

    def _deep_merge(
        self, target: Dict[str, Any], incoming: Dict[str, Any], parent_path: str
    ) -> None:
        for key, value in incoming.items():
            path = f"{parent_path}.{key}" if parent_path else key
            if isinstance(value, dict):
                target.setdefault(key, {})
                if isinstance(target[key], dict):
                    self._deep_merge(target[key], value, path)
                else:
                    target[key] = value
            elif isinstance(value, list):
                strategy = self.merge_strategy.get(path, "append")
                target.setdefault(key, [])
                if strategy == "overwrite":
                    target[key] = value
                else:
                    existing = target.get(key, [])
                    merged = existing + value
                    # Deduplicate while preserving order
                    seen = set()
                    deduped = []
                    for item in merged:
                        marker = (
                            json.dumps(item, sort_keys=True) if isinstance(item, dict) else item
                        )
                        if marker in seen:
                            continue
                        seen.add(marker)
                        deduped.append(item)
                    target[key] = deduped
            else:
                strategy = self.merge_strategy.get(path, "fill")
                if strategy == "overwrite" or target.get(key) in (None, "", [], {}):
                    target[key] = value

    def validate(self) -> Dict[str, List[str]]:
        invalid: Dict[str, List[str]] = {}
        for persona_id, payload in self.personas.items():
            try:
                PersonaProfileModel(**payload)
            except ValidationError as exc:
                invalid[persona_id] = [e.get("msg", str(e)) for e in exc.errors()]
        return invalid

    def write_outputs(
        self,
        output_path: Path,
        qa_report_path: Path,
        page_results: Sequence[PageExtractionResult],
    ) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        qa_report_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("w", encoding="utf-8") as f:
            json.dump(list(self.personas.values()), f, indent=2, ensure_ascii=False)
        qa_report = {
            "personas": list(self.personas.keys()),
            "validation_errors": self.validate(),
            "parse_failures": self.parse_failures,
            "pages_processed": [r.page_number for r in page_results],
            "pages_with_persona": [r.page_number for r in page_results if r.persona_id],
        }
        with qa_report_path.open("w", encoding="utf-8") as f:
            json.dump(qa_report, f, indent=2, ensure_ascii=False)
        logger.info(f"Wrote merged personas to {output_path}")
        logger.info(f"Wrote QA report to {qa_report_path}")


class PersonaExtractionPipeline:
    def __init__(self, config: Optional[PersonaExtractionConfig] = None):
        self.config = config or PersonaExtractionConfig()
        self.renderer = PDFRenderer(dpi=self.config.dpi)
        self.extractor = VLLMOpenAIExtractor(self.config)
        self.merger = PersonaMerger(
            document_name=self.config.pdf_path.name,
            merge_strategy=self.config.merge_strategy,
        )

    def run(self) -> Dict[str, Any]:
        if not self.config.pdf_path.exists():
            raise FileNotFoundError(f"PDF not found at {self.config.pdf_path}")
        pages = self.renderer.render(
            self.config.pdf_path, self.config.page_images_dir, self.config.page_range
        )
        logger.info(f"Rendered {len(pages)} pages from {self.config.pdf_path}")

        page_results = self.extractor.extract_pages(pages)
        self._persist_page_results(page_results)
        for result in page_results:
            self.merger.apply_page_result(result)

        self.merger.write_outputs(
            self.config.merged_output_path, self.config.qa_report_path, page_results
        )
        return {"personas": self.merger.personas, "page_results": page_results}

    def _persist_page_results(self, results: Iterable[PageExtractionResult]) -> None:
        self.config.raw_responses_dir.mkdir(parents=True, exist_ok=True)
        if self.config.debug:
            self.config.debug_dir.mkdir(parents=True, exist_ok=True)
        for result in results:
            out_path = self.config.raw_responses_dir / f"page_{result.page_number:04d}.json"
            payload = {
                "page": result.page_number,
                "persona_id": result.persona_id,
                "parsed": result.parsed,
                "error": result.error,
                "raw_text": result.raw_text,
            }
            with out_path.open("w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
            logger.debug(f"Wrote raw response for page {result.page_number} -> {out_path}")
            if self.config.debug:
                debug_path = self.config.debug_dir / f"page_{result.page_number:04d}.txt"
                debug_payload = result.raw_text or ""
                with debug_path.open("w", encoding="utf-8") as f:
                    f.write(debug_payload)
                logger.debug(f"Wrote debug raw text for page {result.page_number} -> {debug_path}")


def run_persona_extraction_pipeline(
    config: Optional[PersonaExtractionConfig] = None,
) -> Dict[str, Any]:
    pipeline = PersonaExtractionPipeline(config)
    return pipeline.run()
