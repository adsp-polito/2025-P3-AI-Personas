# Glossary

## Core persona terms

- **Persona**: A synthetic agent representing a consumer segment, grounded in proprietary segmentation evidence.
- **Persona profile**: JSON object describing the persona (identity + indicators + optional reasoning traits).
- **Indicator**: A bucketed theme (e.g., “Demographics”, “Coffee behavior”) containing multiple statements.
- **Statement**: A single insight line item within an indicator; can include metrics and salience.
- **Metric**: A normalized value for a statement (e.g., `58 %`, `120 index`).
- **Salience**: Whether a statement is visually/semantically emphasized and should strongly influence reasoning.
- **Influences**: Flags indicating whether the statement shapes the persona’s *tone* and/or *stance*.

## LLM system terms

- **RAG (Retrieval-Augmented Generation)**: Retrieve relevant evidence at query time and inject it into the prompt to reduce hallucination and increase traceability.
- **Vector DB**: Stores embeddings and supports similarity search for RAG.
- **PEFT / LoRA**: Parameter-Efficient Fine-Tuning methods to instill persona voice and reasoning style without retraining an entire LLM.
- **vLLM (OpenAI-compatible)**: A local/private model server that can expose OpenAI-style `/v1` APIs (used for extraction/reasoning in this repo via the `openai` Python client).
- **MCP (Model Context Protocol)**: A standard interface for “tools” (web search, DB queries, calculators) that can provide extra context to an LLM.

