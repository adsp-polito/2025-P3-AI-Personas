# Persona Extraction Pipeline

High-level overview of how a PDF becomes persona data and derived reasoning artifacts.

## Processing Stages
1) **Ingest & Render**  
   - Load the PDF and render pages to images (reuse cached renders when enabled).

2) **Plan & Fetch**  
   - Determine which pages need extraction, skipping those with cached raw responses when caching is on.

3) **VLLM Page Extraction**  
   - Send each target page (plus optional context) to the vision model with the indicator-centric persona prompt. The prompt is generalized to pull persona indicators from any document type (not tied to fixed templates).  
   - Persist raw responses and parsed JSON per page; optionally write debug text.

4) **Aggregate & Persist**  
   - Merge page-level personas, general content, and metadata into:  
     - Merged personas bundle (`personas.json`)  
     - Per-persona files (`individual/{persona_id}.json`)  
     - QA report and structured per-page dump

5) **Reasoning**  
   - Collect salient statements and run a text model to derive persona traits (style/value/guardrails).  
   - Chunk inputs if large; reuse cached results when present.  
   - Write per-persona reasoning artifacts to `common_traits/{persona_id}.json`.

### Indicators (VLLM extraction output)
- `indicators`: top-level buckets (domain/category/label) grouping related statements.
- `statements`: individual insights within an indicator; each carries metrics, salience, and influences.
- `metrics`: normalized numeric/text measures with units (`index`, `%`, `count`, `rank`, `€`, `other`) plus optional description/context.
- `salience`: marks whether a statement is visually emphasized (`is_salient`) with direction (`high|low|neutral`) and magnitude (`strong|medium|weak`), and a short rationale.
- `influences`: flags whether a statement shapes tone or stance.
- `sources`: document/page references for traceability.

Example indicator shape (with field meanings):
```json
Indicator {
  id: "string",
  domain: "string",          // broad area, e.g., "demographics", "coffee_behaviour", "media"
  category: "string",        // finer grouping, e.g., "age_band", "format", "machine_ownership"
  label: "string",           // human-readable title of the indicator
  description: "string",     // optional extra context/definition

  sources: [
    {
      "doc_id": "2023_03_FR_Consumers_Segmentation_France", // document identifier/name
      "pages": [10, 12]                                     // page references for traceability
    }
  ],

  statements: [
    {
      "label": "Skewing Female",                             // short handle for the insight
      "description": "Majority female within this persona", // fuller text/quote
      "metrics": [
        {
          "value": 58,                                      // numeric value (or string if needed)
          "unit": "%",                                      // normalized unit: %, index, rank, count, €, other
          "description": "of persona"                       // optional context for the metric
        },
        {
          "value": 120,
          "unit": "index",
          "description": "vs population"
        }
      ],
      "salience": {
        "is_salient": true,                                  // highlighted/important?
        "direction": "high",                                 // high | low | neutral
        "magnitude": "strong",                               // strong | medium | weak
        "rationale": "Highlighted and index 120"             // why it's salient
      },
      "influences": {
        "tone": false,          // Should this statement shape how the LLM talks?
        "stance": true          // Should this statement shape what the LLM prioritises?
      }
    }
  ]
}
```

### Traits (reasoning output)
- `style_profile`: how the persona would speak (tone adjectives, formality, directness, emotional flavour, criticality, verbosity, preferred structures, example phrases).
- `value_frame`: what they prioritize (priority_rank plus sustainability, price sensitivity, novelty seeking, brand loyalty, health concern, and a summary description).
- `reasoning_policies`:
  - `purchase_advice`: default biases and tradeoff rules to apply when recommending.
  - `product_evaluation`: what earns praise, what triggers criticism, and must-always-check items.
  - `information_processing`: trust preferences, skepticism targets, and requested rigor level.
- `content_filters`: styles to avoid and topics needing emphasized disclaimers (e.g., health claims).

Canonical shapes for reasoning traits:
```json
// How the model should "speak"
style_profile: {
  tone_adjectives: string[],        // ["curious", "confident", "quality-focused", "pragmatic", ...]
  formality_level: "low" | "medium" | "high",
  directness: "very_direct" | "balanced" | "hedged",
  emotional_flavour: "neutral" | "enthusiastic" | "cool_detached" | "warm_reflective",
  criticality_level: "high" | "medium" | "low",
  verbosity_preference: "concise" | "detailed" | "varies_by_question",
  preferred_structures: string[],   // ["bullet_points", "clear_tradeoffs", "pros_cons", "step_by_step"]
  typical_register_examples: string[] // short example phrases in-target style
},

// What they care about – used to bias recommendations / reasoning
value_frame: {
  priority_rank: string[],         // e.g. ["quality", "convenience", "sustainability", "price"]
  sustainability_orientation: "high" | "medium" | "low",
  price_sensitivity: "high" | "medium" | "low",
  novelty_seeking: "high" | "medium" | "low",
  brand_loyalty: "high" | "medium" | "low",
  health_concern: "high" | "medium" | "low",
  description: string              // natural language summary
},

// Concrete behavioural rules for the model: "given a question, lean this way"
reasoning_policies: {
  purchase_advice: {
    default_biases: string[],      // e.g. ["prefer quality even at higher price", "avoid cheap but low-quality options"]
    tradeoff_rules: string[],      // e.g. ["if forced to choose, sacrifice price before quality", "flag environmental impact of packaging when relevant"]
  },
  product_evaluation: {
    praise_triggers: string[],     // conditions that justify positive language
    criticism_triggers: string[],  // conditions to be sceptical / critical
    must_always_check: string[]    // things the model must always comment on (e.g. origin, sustainability)
  },
  information_processing: {
    trust_preference: string[],    // ["data + evidence", "real-world usage", "expert sources"]
    scepticism_towards: string[],  // ["vague marketing claims", "unverified health promises"]
    requested_rigor_level: "high" | "medium" | "low"
  }
},

// Guardrails aligned with persona (in addition to global safety policies)
content_filters: {
  avoid_styles: string[],         // e.g. ["overly emotional hype", "blind brand loyalty"]
  emphasise_disclaimers_on: string[] // ["health claims", "environmental certifications"]
}
```
