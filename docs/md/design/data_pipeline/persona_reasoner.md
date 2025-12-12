# Data Pipeline: `PersonaReasoner`

**Code**: `adsp/data_pipeline/persona_data_pipeline/extract_raw/reasoner.py`

## Purpose

`PersonaReasoner` enriches extracted persona profiles with reasoning traits:
- how the persona speaks (`style_profile`)
- what the persona values (`value_frame`)
- decision rules (`reasoning_policies`)
- guardrails (`content_filters`)

This supports the “authenticity + critical thinking” requirements in `docs/md/design.md`.

## Responsibilities

- Collect salient evidence (`salience.is_salient == true`) from persona indicators
- Build a prompt to a reasoning-capable text model (OpenAI-compatible)
- Parse JSON output into trait sections
- Chunk large evidence sets and merge partial trait outputs
- Cache results per persona on disk

## Public API

### `process(personas: dict[str, dict], output_dir: Path, reuse_cache: bool = True) -> dict[str, dict]`

**Inputs**
- `personas`: persona_id → extracted persona profile dict (from the merger)
- `output_dir`: directory where `{persona_id}.json` trait files are written
- `reuse_cache`: reuse existing `{persona_id}.json` results if present

**Output**
- Map of persona_id → reasoning payload written

## Internal logic (current)

For each persona (concurrently via thread pool):
1. If cached traits exist and reuse enabled, load and return them
2. Build `key_indicators[]` by filtering statements with `salience.is_salient`
3. Chunk indicators by `reasoning_max_input_chars`
4. For each chunk:
   - Fill `ALIGNMENT_USER_TEMPLATE` (see prompts doc)
   - Call the model via `openai` client
   - Parse JSON and merge into the aggregated profile
5. Write `{persona_id}.json` to disk

## Key dependencies / technologies

- `openai` Python client (OpenAI-compatible endpoint)
- `concurrent.futures.ThreadPoolExecutor`
- `loguru` logging

## Failure modes

- If reasoning is disabled (`generate_reasoning_profiles=False`) → returns `{}` and skips.
- If there are no salient indicators → returns `{}` (no enrichment).
- If model output is not valid JSON → the chunk is skipped and the profile may be partial.

