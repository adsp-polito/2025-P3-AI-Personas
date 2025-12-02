"""Lightweight schema reflecting the current persona extraction output."""

from __future__ import annotations

from typing import List, Optional, Union

from pydantic import BaseModel, Field


class Source(BaseModel):
    doc_id: Optional[str] = None
    pages: List[int] = Field(default_factory=list)

    class Config:
        extra = "allow"


class Metric(BaseModel):
    value: Optional[Union[float, str]] = None
    unit: Optional[str] = None  # 'index' | '%' | 'count' | 'rank' | '€' | 'other'
    description: Optional[str] = None

    class Config:
        extra = "allow"


class Salience(BaseModel):
    is_salient: Optional[bool] = None
    direction: Optional[str] = None  # 'high' | 'low' | 'neutral'
    magnitude: Optional[str] = None  # 'strong' | 'medium' | 'weak'
    rationale: Optional[str] = None

    class Config:
        extra = "allow"


class Influences(BaseModel):
    tone: Optional[bool] = None
    stance: Optional[bool] = None

    class Config:
        extra = "allow"


class Statement(BaseModel):
    label: Optional[str] = None
    description: Optional[str] = None
    metrics: List[Metric] = Field(default_factory=list)
    salience: Optional[Salience] = None
    influences: Optional[Influences] = None

    class Config:
        extra = "allow"


class Indicator(BaseModel):
    id: Optional[str] = None
    domain: Optional[str] = None
    category: Optional[str] = None
    label: Optional[str] = None
    description: Optional[str] = None
    sources: List[Source] = Field(default_factory=list)
    statements: List[Statement] = Field(default_factory=list)

    class Config:
        extra = "allow"


class StyleProfile(BaseModel):
    tone_adjectives: List[str] = Field(default_factory=list)
    formality_level: Optional[str] = None
    directness: Optional[str] = None
    emotional_flavour: Optional[str] = None
    criticality_level: Optional[str] = None
    verbosity_preference: Optional[str] = None
    preferred_structures: List[str] = Field(default_factory=list)
    typical_register_examples: List[str] = Field(default_factory=list)

    class Config:
        extra = "allow"


class ValueFrame(BaseModel):
    priority_rank: List[str] = Field(default_factory=list)
    sustainability_orientation: Optional[str] = None
    price_sensitivity: Optional[str] = None
    novelty_seeking: Optional[str] = None
    brand_loyalty: Optional[str] = None
    health_concern: Optional[str] = None
    description: Optional[str] = None

    class Config:
        extra = "allow"


class PurchaseAdvice(BaseModel):
    default_biases: List[str] = Field(default_factory=list)
    tradeoff_rules: List[str] = Field(default_factory=list)

    class Config:
        extra = "allow"


class ProductEvaluation(BaseModel):
    praise_triggers: List[str] = Field(default_factory=list)
    criticism_triggers: List[str] = Field(default_factory=list)
    must_always_check: List[str] = Field(default_factory=list)

    class Config:
        extra = "allow"


class InformationProcessing(BaseModel):
    trust_preference: List[str] = Field(default_factory=list)
    scepticism_towards: List[str] = Field(default_factory=list)
    requested_rigor_level: Optional[str] = None

    class Config:
        extra = "allow"


class ReasoningPolicies(BaseModel):
    purchase_advice: Optional[PurchaseAdvice] = None
    product_evaluation: Optional[ProductEvaluation] = None
    information_processing: Optional[InformationProcessing] = None

    class Config:
        extra = "allow"


class ContentFilters(BaseModel):
    avoid_styles: List[str] = Field(default_factory=list)
    emphasise_disclaimers_on: List[str] = Field(default_factory=list)

    class Config:
        extra = "allow"


class PersonaProfileModel(BaseModel):
    persona_id: Optional[str] = None
    persona_name: Optional[str] = None
    visual_description: Optional[str] = None
    summary_bio: Optional[str] = None
    indicators: List[Indicator] = Field(default_factory=list)
    source_pages: List[int] = Field(default_factory=list)
    document: Optional[str] = None
    # Optional reasoning enrichment
    key_indicators: List[dict] = Field(default_factory=list)
    style_profile: Optional[StyleProfile] = None
    value_frame: Optional[ValueFrame] = None
    reasoning_policies: Optional[ReasoningPolicies] = None
    content_filters: Optional[ContentFilters] = None

    class Config:
        extra = "allow"


PersonaProfile = PersonaProfileModel

__all__ = ["PersonaProfile", "PersonaProfileModel"]
