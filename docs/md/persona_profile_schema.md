# Persona Profile Extraction Schema

This document describes the output shape produced by the persona extraction pipeline. It aligns with the latest prompt (hierarchical Indicator → Statements → Metrics) and the per-page JSON expected from the LLM.

## JSON Envelope

```json
{
  "page_metadata": {
    "title": "string",
    "source": "string",
    "page_number": "integer",
    "related_page_numbers": ["integer"],
    "overall_theme": "string"
  },
  "personas": [
    {
      "persona_name": "string",
      "persona_id": "string",
      "visual_description": "string",
      "summary_bio": "string",
      "indicators": [
        {
          "id": "string",
          "domain": "string",
          "category": "string",
          "label": "string",
          "description": "string",
          "sources": [
            {
              "doc_id": "string",
              "pages": ["integer"]
            }
          ],
          "statements": [
            {
              "label": "string",
              "description": "string",
              "metrics": [
                {
                  "value": "number | string",
                  "unit": "'index' | '%' | 'count' | 'rank' | '€' | 'other'",
                  "description": "string"
                }
              ],
              "salience": {
                "is_salient": "boolean",
                "direction": "string ('high', 'low', 'neutral')",
                "magnitude": "string ('strong', 'medium', 'weak')",
                "rationale": "string"
              },
              "influences": {
                "tone": "boolean",
                "stance": "boolean"
              }
            }
          ]
        }
      ]
    }
  ],
  "general_content": {
    "description": "string",
    "sections": []
  }
}
```

## Field Notes

- **page_metadata**: Captures header/footer info and any cross-page linkage. `related_page_numbers` flags continuity across slides.
- **personas**: One entry per persona on the page. `persona_id` is kebab-case. `visual_description` is a short description of the image/avatar.
- **indicators**: Level 1 grouping by visual section or theme (e.g., Demographics, Coffee Behaviors). `id` should be stable per indicator when available; otherwise use a slug of the label.
- **sources**: `doc_id` is the document name; `pages` lists the pages that support this indicator.
- **statements**: Level 2 insights under an indicator (qualitative or behavioral lines). Salience and influence are inferred from visual emphasis.
- **metrics**: Level 3 numeric or ranked values tied to a statement. Normalize units to the allowed set (`index`, `%`, `count`, `rank`, `€`, `other`) and coerce numeric strings to numbers when possible.
- **salience**: Marks whether a statement is emphasized (highlighted/bolded/above-average or de-emphasized). Use `direction` and `magnitude` to reflect strength; include a short `rationale`.
- **influences**: `tone` indicates how the persona speaks/acts; `stance` flags beliefs or buying priorities.
- **general_content**: Use when the page has non-persona market data; leave `personas` empty in that case.

## Example (abridged)

```json
{
  "page_metadata": {
    "title": "Persona Deep Dive",
    "source": "Lavazza Segmentation 2023",
    "page_number": 5,
    "related_page_numbers": [6],
    "overall_theme": "Persona Comparison"
  },
  "personas": [
    {
      "persona_name": "Mindful Enthusiast",
      "persona_id": "mindful-enthusiast",
      "visual_description": "Young woman holding coffee mug",
      "summary_bio": "Quality-seeker who experiments with new blends and values sustainability.",
      "indicators": [
        {
          "id": "demographics",
          "domain": "profile",
          "category": "Demographics",
          "label": "Demographics",
          "description": "Who they are",
          "sources": [{"doc_id": "2023 03_FR_Consumers Segmentation France.pdf", "pages": [5]}],
          "statements": [
            {
              "label": "Skewing Female",
              "description": "Majority female within this persona",
              "metrics": [{"value": 58, "unit": "%", "description": "of persona"}],
              "salience": {"is_salient": true, "direction": "high", "magnitude": "medium", "rationale": "Highlighted in chart"},
              "influences": {"tone": false, "stance": false}
            }
          ]
        }
      ]
    }
  ],
  "general_content": {
    "description": "",
    "sections": []
  }
}
```
