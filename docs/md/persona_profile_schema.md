# Persona Profile Schema

This schema reflects the JSON produced by the extraction pipeline and used by downstream persona consumers.

## Shape

```json
PersonaProfile {
  persona_id: string,
  persona_name: string,
  visual_description: string,
  summary_bio: string,
  indicators: Indicator[],
  source_pages: int[],
  document: string,
  key_indicators: object[],          // salient statements, present when reasoning runs
  style_profile: StyleProfile | null,
  value_frame: ValueFrame | null,
  reasoning_policies: ReasoningPolicies | null,
  content_filters: ContentFilters | null
}
```

### Indicator
```json
{
  "id": "string",
  "domain": "string",
  "category": "string",
  "label": "string",
  "description": "string",
  "sources": [{ "doc_id": "string", "pages": [int] }],
  "statements": Statement[]
}
```

### Statement
```json
{
  "label": "string",
  "description": "string",
  "metrics": [{ "value": number|string, "unit": "index|%|count|rank|€|other", "description": "string" }],
  "salience": { "is_salient": bool, "direction": "high|low|neutral", "magnitude": "strong|medium|weak", "rationale": "string" },
  "influences": { "tone": bool, "stance": bool }
}
```

### Reasoning 
When the reasoning step runs, personas may include:

- `key_indicators`: salient statements harvested for reasoning (retains sources/metrics/salience).
- `style_profile`: tone and delivery hints (adjectives, formality, directness, emotional flavour, verbosity, preferred structures, register examples).
- `value_frame`: what they prioritize (priority_rank plus sustainability, price, novelty, loyalty, health flags, description).
- `reasoning_policies`: purchase_advice, product_evaluation, information_processing.
- `content_filters`: avoid_styles, emphasise_disclaimers_on.

## Usage Notes
- `persona_id` is kebab-case; `document` holds the originating PDF name; `source_pages` shows where the persona was observed.
- Metrics should be numeric when possible; units normalize to the allowed set.
- Salience drives reasoning inputs; only `salience.is_salient == true` statements populate `key_indicators`.
- Sources are preserved and propagated into reasoning payloads so traceability is retained.

