"""Prompt templates for persona alignment and reasoning enrichment."""

ALIGNMENT_SYSTEM_PROMPT = """You are an expert persona strategist. Given salient indicator evidence for a persona, infer how this persona communicates and what they value.

Return strict JSON with keys: style_profile, value_frame, reasoning_policies, content_filters.
- Use only the provided evidence. Do not invent metrics.
- Keep lists concise but expressive; 3-7 bullets are enough.
- If you are unsure, leave the field empty or pick "medium"/"balanced"/"varies_by_question".
"""

ALIGNMENT_USER_TEMPLATE = """
Persona:
- persona_id: {persona_id}
- persona_name: {persona_name}
- summary_bio: {summary_bio}

Existing partial profile (may be empty):
{partial_profile}

Salient key_indicators (statements where salience.is_salient=true):
{key_indicators}

Required JSON schema:
{{
  "style_profile": {{
    "tone_adjectives": [ "string" ],
    "formality_level": "low|medium|high",
    "directness": "very_direct|balanced|hedged",
    "emotional_flavour": "neutral|enthusiastic|cool_detached|warm_reflective",
    "criticality_level": "high|medium|low",
    "verbosity_preference": "concise|detailed|varies_by_question",
    "preferred_structures": [ "string" ],
    "typical_register_examples": [ "string" ]
  }},
  "value_frame": {{
    "priority_rank": [ "string" ],
    "sustainability_orientation": "high|medium|low",
    "price_sensitivity": "high|medium|low",
    "novelty_seeking": "high|medium|low",
    "brand_loyalty": "high|medium|low",
    "health_concern": "high|medium|low",
    "description": "string"
  }},
  "reasoning_policies": {{
    "purchase_advice": {{
      "default_biases": [ "string" ],
      "tradeoff_rules": [ "string" ]
    }},
    "product_evaluation": {{
      "praise_triggers": [ "string" ],
      "criticism_triggers": [ "string" ],
      "must_always_check": [ "string" ]
    }},
    "information_processing": {{
      "trust_preference": [ "string" ],
      "scepticism_towards": [ "string" ],
      "requested_rigor_level": "high|medium|low"
    }}
  }},
  "content_filters": {{
    "avoid_styles": [ "string" ],
    "emphasise_disclaimers_on": [ "string" ]
  }}
}}

Return only valid JSON for this persona.
"""
