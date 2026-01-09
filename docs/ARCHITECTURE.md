# System Architecture

Overview of the AI Personas platform design and data flow.

## High-Level Design

```
┌─────────────┐
│  Frontend   │  Streamlit UI / REST API
└──────┬──────┘
       │
┌──────▼──────┐
│ Application │  QA / Auth / Ingestion / Reports
└──────┬──────┘
       │
┌──────▼──────────┐
│  Orchestrator   │  Core coordination logic
│  ┌───────────┐  │
│  │ Memory    │  │  Conversation history
│  │ RAG       │  │  Knowledge retrieval
│  │ Filter    │  │  Context selection
│  │ Builder   │  │  Prompt construction
│  │ Router    │  │  Model dispatch
│  └───────────┘  │
└──────┬──────────┘
       │
┌──────▼──────┐
│   Storage   │  Vector DB / Business DB
└─────────────┘
```

## Request Flow

When a user sends a chat message:

1. **Input normalization** - Clean and standardize the query
2. **History retrieval** - Fetch previous conversation turns from memory
3. **RAG retrieval** - Search for relevant context in persona + fact indexes
4. **Context filtering** - Keep only the most relevant history and documents
5. **Prompt building** - Combine query, context, and history into a full prompt
6. **Model routing** - Send prompt to the appropriate LLM endpoint
7. **Memory storage** - Save the exchange for future context
8. **Response** - Return answer with citations

## Key Components

### Orchestrator
The central coordinator. Wires together all components and manages the request lifecycle.

### RAG Pipeline
Retrieves relevant knowledge from two sources:
- **Persona index**: Consumer segment characteristics and preferences
- **Fact data index**: Product info and business data

### Context Filter
Intelligently selects which history turns and documents to include in the prompt. Uses keyword matching or optional LLM-based selection.

### Persona Router
Maps persona IDs to specific model endpoints or PEFT adapters. Allows different consumer segments to use different fine-tuned models.

### Memory
Stores recent conversation history per persona and session. Implements a simple sliding window (default: last 10 turns).

## Data Pipeline

Raw data flows through several stages:

```
Raw documents → Extraction → Chunking → Embedding → Index
```

Two parallel pipelines:
1. **Persona pipeline**: Extracts consumer personas from research documents
2. **Fact data pipeline**: Processes product catalogs and business info

## Storage Layer

- **Vector DB**: Embeddings for semantic search (RAG)
- **Business DB**: Persona configs, user auth, metadata
- **Object Store**: File uploads and generated reports

## Environment Configuration

Key settings (via environment variables):

- `ADSP_LLM_BACKEND`: Model inference backend
- `ADSP_LLM_BASE_URL`: LLM API endpoint
- `ADSP_CONTEXT_FILTER_ENABLED`: Toggle context filtering
- `ADSP_CONTEXT_FILTER_BACKEND`: Use heuristic or openai filter

See `.env.example` for the full list.

## Extension Points

The system is designed to be modular. You can swap out:

- **Inference engine**: Use any OpenAI-compatible API
- **Vector DB**: Replace the in-memory stub with Qdrant, Pinecone, etc.
- **Context filter**: Implement custom selection logic
- **Prompt builder**: Customize how prompts are constructed
