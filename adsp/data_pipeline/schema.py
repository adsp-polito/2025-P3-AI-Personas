"""Typed persona profile schema with nested structures up to three levels."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class PercentageIndex(BaseModel):
    percentage: Optional[float] = None
    index: Optional[float] = None

    class Config:
        extra = "allow"


class ValueIndex(BaseModel):
    value: Optional[float] = None
    index: Optional[float] = None

    class Config:
        extra = "allow"


class ValueIndexWithCurrency(BaseModel):
    value_eur: Optional[float] = None
    index: Optional[float] = None

    class Config:
        extra = "allow"


class SourceReference(BaseModel):
    document: Optional[str] = None
    pages: List[int] = Field(default_factory=list)
    extraction_notes: Optional[str] = None

    class Config:
        extra = "allow"


class MarketImpact(BaseModel):
    population_share_percentage: Optional[float] = None
    value_share_percentage: Optional[float] = None
    spend_at_home_index: Optional[float] = None

    class Config:
        extra = "allow"


class IdentitySummary(BaseModel):
    demographics: Optional[str] = None
    psychographics: Optional[str] = None

    class Config:
        extra = "allow"


class ConsumptionVolume(BaseModel):
    average_daily_coffees: Optional[float] = None
    index: Optional[float] = None

    class Config:
        extra = "allow"


class ConsumptionHabit(BaseModel):
    volume: Optional[ConsumptionVolume] = None
    behavior_description: Optional[str] = None

    class Config:
        extra = "allow"


class ConsumptionHabits(BaseModel):
    at_home: Optional[ConsumptionHabit] = None
    out_of_home: Optional[ConsumptionHabit] = None

    class Config:
        extra = "allow"


class SustainabilityAttitudeSingle(BaseModel):
    statement: Optional[str] = None
    index: Optional[float] = None

    class Config:
        extra = "allow"


class ShoppingAttitude(BaseModel):
    statement: Optional[str] = None
    index: Optional[float] = None

    class Config:
        extra = "allow"


class InnovationInterest(BaseModel):
    summary: Optional[str] = None

    class Config:
        extra = "allow"


class CoreProfileOverview(BaseModel):
    market_impact: Optional[MarketImpact] = None
    identity_summary: Optional[IdentitySummary] = None
    sustainability_attitude: Optional[SustainabilityAttitudeSingle] = None
    consumption_habits: Optional[ConsumptionHabits] = None
    shopping_attitude: Optional[ShoppingAttitude] = None
    innovation_interest: Optional[InnovationInterest] = None

    class Config:
        extra = "allow"


class GenderDistribution(BaseModel):
    female: Optional[PercentageIndex] = None
    male: Optional[PercentageIndex] = None

    class Config:
        extra = "allow"


class AgeDistributionEntry(BaseModel):
    range: Optional[str] = None
    percentage: Optional[float] = None
    index: Optional[float] = None

    class Config:
        extra = "allow"


class HouseholdSizeEntry(BaseModel):
    members: Optional[str] = None
    percentage: Optional[float] = None
    index: Optional[float] = None

    class Config:
        extra = "allow"


class RegionDistributionEntry(BaseModel):
    region: Optional[str] = None
    percentage: Optional[float] = None
    index: Optional[float] = None

    class Config:
        extra = "allow"


class AreaOfLivingEntry(BaseModel):
    area: Optional[str] = None
    percentage: Optional[float] = None
    index: Optional[float] = None

    class Config:
        extra = "allow"


class IncomeBracket(BaseModel):
    range: Optional[str] = None
    percentage: Optional[float] = None
    index: Optional[float] = None

    class Config:
        extra = "allow"


class IncomeDistribution(BaseModel):
    low: Optional[PercentageIndex] = None
    medium: Optional[PercentageIndex] = None
    high: Optional[PercentageIndex] = None
    average_income_eur: Optional[float] = None
    average_income_index: Optional[float] = None
    income_brackets: List[IncomeBracket] = Field(default_factory=list)

    class Config:
        extra = "allow"


class EducationLevelEntry(BaseModel):
    level: Optional[str] = None
    percentage: Optional[float] = None
    index: Optional[float] = None

    class Config:
        extra = "allow"


class ProfessionDistributionEntry(BaseModel):
    role: Optional[str] = None
    percentage: Optional[float] = None
    index: Optional[float] = None

    class Config:
        extra = "allow"


class CoffeePurchaseDecision(BaseModel):
    primary_decision_maker: Optional[PercentageIndex] = None
    shared_decision_maker: Optional[PercentageIndex] = None

    class Config:
        extra = "allow"


class Demographics(BaseModel):
    gender_distribution: Optional[GenderDistribution] = None
    age_distribution: List[AgeDistributionEntry] = Field(default_factory=list)
    average_age: Optional[float] = None
    household_size: List[HouseholdSizeEntry] = Field(default_factory=list)
    region_distribution: List[RegionDistributionEntry] = Field(default_factory=list)
    area_of_living: List[AreaOfLivingEntry] = Field(default_factory=list)
    income_distribution: Optional[IncomeDistribution] = None
    education_level: List[EducationLevelEntry] = Field(default_factory=list)
    profession_distribution: List[ProfessionDistributionEntry] = Field(default_factory=list)
    coffee_purchase_decision: Optional[CoffeePurchaseDecision] = None

    class Config:
        extra = "allow"


class StatementIndex(BaseModel):
    statement: Optional[str] = None
    agreement_percentage: Optional[float] = None
    index: Optional[float] = None

    class Config:
        extra = "allow"


class ValuesAndAttitudes(BaseModel):
    lifestyle_statements: List[StatementIndex] = Field(default_factory=list)
    coffee_attitudes: List[StatementIndex] = Field(default_factory=list)

    class Config:
        extra = "allow"


class SustainabilityAttitudeEntry(BaseModel):
    statement: Optional[str] = None
    agreement_percentage: Optional[float] = None
    index: Optional[float] = None

    class Config:
        extra = "allow"


class NeedState(BaseModel):
    label: Optional[str] = None
    percentage: Optional[float] = None
    index: Optional[float] = None

    class Config:
        extra = "allow"


class NeedStates(BaseModel):
    at_home: List[NeedState] = Field(default_factory=list)
    out_of_home: List[NeedState] = Field(default_factory=list)

    class Config:
        extra = "allow"


class TimeOfConsumptionEntry(BaseModel):
    moment: Optional[str] = None
    percentage: Optional[float] = None
    index: Optional[float] = None

    class Config:
        extra = "allow"


class TimeOfConsumption(BaseModel):
    at_home: List[TimeOfConsumptionEntry] = Field(default_factory=list)
    out_of_home: List[TimeOfConsumptionEntry] = Field(default_factory=list)

    class Config:
        extra = "allow"


class AudienceIndex(BaseModel):
    percentage: Optional[float] = None
    index: Optional[float] = None

    class Config:
        extra = "allow"


class CoffeeChoiceMotivation(BaseModel):
    reason: Optional[str] = None
    total_segment: Optional[AudienceIndex] = None
    bean_users: Optional[AudienceIndex] = None

    class Config:
        extra = "allow"


class CoffeeTypeEntry(BaseModel):
    type: Optional[str] = None
    percentage: Optional[float] = None
    index: Optional[float] = None

    class Config:
        extra = "allow"


class PreparationMethodEntry(BaseModel):
    system: Optional[str] = None
    percentage: Optional[float] = None
    index: Optional[float] = None

    class Config:
        extra = "allow"


class ConsumptionMetrics(BaseModel):
    average_daily_coffees_at_home: Optional[ValueIndex] = None
    average_daily_coffees_out_of_home: Optional[ValueIndex] = None

    class Config:
        extra = "allow"


class AmountSpendEntry(BaseModel):
    bracket: Optional[str] = None
    percentage: Optional[float] = None
    index: Optional[float] = None

    class Config:
        extra = "allow"


class ShoppingFrequencyEntry(BaseModel):
    frequency: Optional[str] = None
    percentage: Optional[float] = None
    index: Optional[float] = None

    class Config:
        extra = "allow"


class PurchasingHabits(BaseModel):
    amount_spend_per_purchase: List[AmountSpendEntry] = Field(default_factory=list)
    average_spend: Optional[ValueIndexWithCurrency] = None
    shopping_frequency: List[ShoppingFrequencyEntry] = Field(default_factory=list)
    average_frequency_days: Optional[ValueIndex] = None

    class Config:
        extra = "allow"


class ChannelEntry(BaseModel):
    channel: Optional[str] = None
    percentage: Optional[float] = None
    index: Optional[float] = None

    class Config:
        extra = "allow"


class OnlineChannelEntry(BaseModel):
    site_type: Optional[str] = None
    percentage: Optional[float] = None
    index: Optional[float] = None

    class Config:
        extra = "allow"


class ChannelPreferences(BaseModel):
    physical_and_general: List[ChannelEntry] = Field(default_factory=list)
    online_breakdown: List[OnlineChannelEntry] = Field(default_factory=list)

    class Config:
        extra = "allow"


class BrandHouseholdPenetration(BaseModel):
    brand: Optional[str] = None
    percentage: Optional[float] = None
    index: Optional[float] = None

    class Config:
        extra = "allow"


class SubBrandEntry(BaseModel):
    sub_brand: Optional[str] = None
    percentage: Optional[float] = None
    index: Optional[float] = None

    class Config:
        extra = "allow"


class SubBrandDeepDive(BaseModel):
    lavazza: List[SubBrandEntry] = Field(default_factory=list)
    carte_noire: List[SubBrandEntry] = Field(default_factory=list)

    class Config:
        extra = "allow"


class BrandLandscape(BaseModel):
    top_competitors_household_penetration: List[BrandHouseholdPenetration] = Field(
        default_factory=list
    )
    sub_brand_deep_dive: Optional[SubBrandDeepDive] = None

    class Config:
        extra = "allow"


class CoffeeConsumptionTraits(BaseModel):
    needstates: Optional[NeedStates] = None
    consumption_moment: Optional[dict] = None
    time_of_consumption: Optional[TimeOfConsumption] = None
    coffee_choice_motivations: List[CoffeeChoiceMotivation] = Field(default_factory=list)
    type_of_coffee_used: List[CoffeeTypeEntry] = Field(default_factory=list)
    preparation_method: List[PreparationMethodEntry] = Field(default_factory=list)
    consumption_metrics: Optional[ConsumptionMetrics] = None
    purchasing_habits: Optional[PurchasingHabits] = None
    channel_preferences: Optional[ChannelPreferences] = None
    brand_landscape: Optional[BrandLandscape] = None
    drinks_consumed: Optional[List[dict]] = None
    location_preferences: Optional[List[dict]] = None
    location_choice_drivers: Optional[List[dict]] = None
    preferred_bar_type: Optional[List[dict]] = None
    global_coffee_chains_attitude: Optional[dict] = None

    class Config:
        extra = "allow"


class BrandMetrics(BaseModel):
    brand_share_percentage: Optional[float] = None
    buy_regularly_score: Optional[float] = None
    trial_score: Optional[float] = None
    awareness_score: Optional[float] = None

    class Config:
        extra = "allow"


class ConversionRates(BaseModel):
    trial_to_buy_regularly: Optional[float] = None
    awareness_to_trial: Optional[float] = None

    class Config:
        extra = "allow"


class SubBrandFunnel(BaseModel):
    sub_brand_name: Optional[str] = None
    metrics: Optional[BrandMetrics] = None
    conversion_rates: Optional[ConversionRates] = None

    class Config:
        extra = "allow"


class BrandPerceptionEntry(BaseModel):
    brand_name: Optional[str] = None
    brand_share_percentage: Optional[float] = None
    metrics: Optional[BrandMetrics] = None
    conversion_rates: Optional[ConversionRates] = None
    sub_brand_funnels: List[SubBrandFunnel] = Field(default_factory=list)

    class Config:
        extra = "allow"


class BrandPerception(BaseModel):
    brands: List[BrandPerceptionEntry] = Field(default_factory=list)

    class Config:
        extra = "allow"


class MachineOwnershipEntry(BaseModel):
    method: Optional[str] = None
    percentage: Optional[float] = None
    index: Optional[float] = None

    class Config:
        extra = "allow"


class MachineOwnershipBehavior(BaseModel):
    penetration_methods: List[MachineOwnershipEntry] = Field(default_factory=list)
    machine_currently_owned: List[dict] = Field(default_factory=list)
    machine_previously_owned: List[dict] = Field(default_factory=list)
    reasons_for_switching_machineS: List[dict] = Field(default_factory=list)
    capsule_machine_motivations: Optional[dict] = None
    capsule_machine_brand_ownership: List[dict] = Field(default_factory=list)
    machine_price_sensitivity: Optional[dict] = None

    class Config:
        extra = "allow"


class InnovationConcept(BaseModel):
    rank: Optional[int] = None
    concept_description: Optional[str] = None
    percentage: Optional[float] = None
    index: Optional[float] = None

    class Config:
        extra = "allow"


class Innovation(BaseModel):
    top_concepts: List[InnovationConcept] = Field(default_factory=list)

    class Config:
        extra = "allow"


class LifestyleAttitude(BaseModel):
    statement: Optional[str] = None
    agreement_percentage: Optional[float] = None
    index_vs_coffee_drinkers: Optional[float] = None
    index_vs_all_adults: Optional[float] = None

    class Config:
        extra = "allow"


class Lifestyle(BaseModel):
    attitudes: List[LifestyleAttitude] = Field(default_factory=list)

    class Config:
        extra = "allow"


class ActivityIndex(BaseModel):
    activity: Optional[str] = None
    percentage: Optional[float] = None
    index_vs_coffee: Optional[float] = None
    index_vs_adults: Optional[float] = None

    class Config:
        extra = "allow"


class LeisureAttitude(BaseModel):
    statement: Optional[str] = None
    percentage: Optional[float] = None
    index_vs_coffee: Optional[float] = None
    index_vs_adults: Optional[float] = None

    class Config:
        extra = "allow"


class SportIndex(BaseModel):
    sport: Optional[str] = None
    percentage: Optional[float] = None
    index_vs_coffee: Optional[float] = None
    index_vs_adults: Optional[float] = None

    class Config:
        extra = "allow"


class FitnessIndex(BaseModel):
    activity: Optional[str] = None
    percentage: Optional[float] = None
    index_vs_coffee: Optional[float] = None
    index_vs_adults: Optional[float] = None

    class Config:
        extra = "allow"


class Sports(BaseModel):
    interest_in_sports: List[SportIndex] = Field(default_factory=list)
    active_participation_sports: List[SportIndex] = Field(default_factory=list)
    active_participation_fitness: List[FitnessIndex] = Field(default_factory=list)

    class Config:
        extra = "allow"


class SportAndLeisure(BaseModel):
    outings_and_activities: List[ActivityIndex] = Field(default_factory=list)
    hobbies_and_interests: List[ActivityIndex] = Field(default_factory=list)
    leisure_attitudes: List[LeisureAttitude] = Field(default_factory=list)
    sports: Optional[Sports] = None

    class Config:
        extra = "allow"


class MediaChannelPenetration(BaseModel):
    channel: Optional[str] = None
    penetration_percentage: Optional[float] = None
    index_vs_coffee_drinkers: Optional[float] = None
    index_vs_all_adults: Optional[float] = None

    class Config:
        extra = "allow"


class TechnologyAttitude(BaseModel):
    statement: Optional[str] = None
    agreement_percentage: Optional[float] = None
    index_vs_coffee_drinkers: Optional[float] = None
    index_vs_all_adults: Optional[float] = None

    class Config:
        extra = "allow"


class ChannelUsageIntensity(BaseModel):
    channel: Optional[str] = None
    usage_level: Optional[str] = None
    percentage: Optional[float] = None
    index_vs_coffee_drinkers: Optional[float] = None
    index_vs_all_adults: Optional[float] = None

    class Config:
        extra = "allow"


class ContentPreferenceEntry(BaseModel):
    genre: Optional[str] = None
    topic: Optional[str] = None
    percentage: Optional[float] = None
    index_vs_coffee_drinkers: Optional[float] = None
    index_vs_all_adults: Optional[float] = None

    class Config:
        extra = "allow"


class ContentPreferences(BaseModel):
    television_genres: List[ContentPreferenceEntry] = Field(default_factory=list)
    film_genres: List[ContentPreferenceEntry] = Field(default_factory=list)
    podcast_genres: List[ContentPreferenceEntry] = Field(default_factory=list)
    radio_programmes: List[ContentPreferenceEntry] = Field(default_factory=list)
    newspaper_topics: List[ContentPreferenceEntry] = Field(default_factory=list)

    class Config:
        extra = "allow"


class TimeFrequencyEntry(BaseModel):
    frequency: Optional[str] = None
    percentage: Optional[float] = None
    vs_coffee_drinkers: Optional[str] = None

    class Config:
        extra = "allow"


class SocialMediaBrandEntry(BaseModel):
    platform: Optional[str] = None
    penetration: Optional[float] = None
    index_vs_coffee: Optional[float] = None
    index_vs_adults: Optional[float] = None

    class Config:
        extra = "allow"


class SocialMediaBehavior(BaseModel):
    time_spent_frequency: List[TimeFrequencyEntry] = Field(default_factory=list)
    brands_used: List[SocialMediaBrandEntry] = Field(default_factory=list)

    class Config:
        extra = "allow"


class OnlineResearchTopic(BaseModel):
    topic: Optional[str] = None
    percentage: Optional[float] = None
    description: Optional[str] = None

    class Config:
        extra = "allow"


class DeviceUsageEntry(BaseModel):
    device: Optional[str] = None
    penetration: Optional[float] = None
    index_vs_coffee: Optional[float] = None
    index_vs_adults: Optional[float] = None

    class Config:
        extra = "allow"


class WebsiteVisitationEntry(BaseModel):
    site: Optional[str] = None
    penetration: Optional[float] = None
    index_vs_coffee: Optional[float] = None
    index_vs_adults: Optional[float] = None

    class Config:
        extra = "allow"


class OnlineActivityEntry(BaseModel):
    activity: Optional[str] = None
    penetration: Optional[float] = None
    index_vs_coffee: Optional[float] = None

    class Config:
        extra = "allow"


class InternetConsumptionProfile(BaseModel):
    social_media_behavior: Optional[SocialMediaBehavior] = None
    online_research_topics: List[OnlineResearchTopic] = Field(default_factory=list)
    device_usage: List[DeviceUsageEntry] = Field(default_factory=list)
    website_visitation_last_4_weeks: List[WebsiteVisitationEntry] = Field(
        default_factory=list
    )
    online_activities_daily: List[OnlineActivityEntry] = Field(default_factory=list)

    class Config:
        extra = "allow"


class Media(BaseModel):
    media_penetration_channels: List[MediaChannelPenetration] = Field(default_factory=list)
    technology_attitudes: List[TechnologyAttitude] = Field(default_factory=list)
    channel_usage_intensity: List[ChannelUsageIntensity] = Field(default_factory=list)
    content_preferences: Optional[ContentPreferences] = None
    internet_consumption_profile: Optional[InternetConsumptionProfile] = None

    class Config:
        extra = "allow"


class PersonaProfileModel(BaseModel):
    persona_id: Optional[str] = None
    segment_name: Optional[str] = None
    locale: Optional[str] = None
    source_reference: Optional[SourceReference] = None
    core_profile_overview: Optional[CoreProfileOverview] = None
    demographics: Optional[Demographics] = None
    values_and_attitudes: Optional[ValuesAndAttitudes] = None
    sustainability_attitudes: List[SustainabilityAttitudeEntry] = Field(default_factory=list)
    coffee_consumption_traits: Optional[CoffeeConsumptionTraits] = None
    brand_perception: Optional[BrandPerception] = None
    machine_ownership_behavior: Optional[MachineOwnershipBehavior] = None
    innovation: Optional[Innovation] = None
    lifestyle: Optional[Lifestyle] = None
    sport_and_leisure: Optional[SportAndLeisure] = None
    media: Optional[Media] = None

    class Config:
        extra = "allow"


# Backward-compatible alias
PersonaProfile = PersonaProfileModel
__all__ = ["PersonaProfile", "PersonaProfileModel"]
