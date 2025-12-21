# Software Requirements Specification (SRS)
## Lavazza AI Personas System

**Version:** 1.0  
**Date:** December 2025  
**Project:** Lavazza AI Personas - Dynamic Conversational Consumer Insights Platform

---

## 1. Introduction

### 1.1 Purpose
This Software Requirements Specification (SRS) document provides a comprehensive description of the Lavazza AI Personas system. It details the functional requirements, system architecture, and operational workflows with a specific focus on the data pipeline processing and orchestrator mechanisms that form the core intelligence of the system.

### 1.2 Scope
The Lavazza AI Personas system transforms static customer segmentation studies into dynamic, conversational AI agents. These AI personas authentically represent Lavazza's customer segments, serving as an advanced consumer insights platform for market research, concept validation, and strategic decision-making.

### 1.3 Document Conventions
- **Persona**: A synthetic AI agent representing a specific customer segment with defined demographics, behaviors, and communication styles
- **Indicator**: A data structure grouping related insights about a persona (domain/category/label) with measurable statements
- **RAG**: Retrieval-Augmented Generation - a technique to ground AI responses in factual data
- **PEFT**: Parameter-Efficient Fine-Tuning - a method to customize LLMs with specific persona characteristics
- **Orchestrator**: The central coordination engine that manages the entire request processing pipeline

### 1.4 References
- Project Documentation: `/docs/md/design.md`
- Persona Extraction Pipeline: `/docs/md/persona_extraction_pipeline.md`
- Persona Profile Schema: `/docs/md/persona_profile_schema.md`
- Folder Structure: `/docs/md/folder_structure.md`

---

## 2. Overall Description

### 2.1 Product Perspective
The system is a bespoke, self-contained AI platform built from scratch to ensure:
- **Transparency**: Full visibility into model reasoning and data sources
- **Reduced Bias**: Prioritization of proprietary Lavazza data over generic pre-trained knowledge
- **Factual Accuracy**: Minimization of AI hallucinations through RAG-based grounding
- **Authentic Personality**: Natural, segment-specific communication styles through PEFT

### 2.2 Product Functions
The system provides the following high-level capabilities:

1. **Data Extraction & Processing**
   - PDF-to-persona data extraction using vision-language models
   - Quantitative fact data extraction and indexing
   - Multi-source data fusion into unified persona profiles

2. **Conversational Interaction**
   - Natural language Q&A with persona-specific AI agents
   - Context-aware responses with conversation memory

3. **Virtual Focus Groups**
   - Simultaneous interaction with multiple personas

4. **Transparency & Explainability**
   - Citation of source documents and page numbers
   - Traceability from response to original data

### 2.3 User Classes and Characteristics

**Primary Users: Marketing Teams & Researchers**
- Need rapid consumer insights for campaign validation
- Require authentic segment perspectives
- Value transparency in AI reasoning
- Non-technical users expecting intuitive chat interface

**Secondary Users: Product Strategists**
- Use personas for concept testing
- Need critical, honest feedback from segments
- Require access to underlying data sources

### 2.4 Operating Environment
- **Backend**: Python-based services (FastAPI)
- **Deployment**: Local/private cloud infrastructure
- **LLM Backend**: Open-source models (Gemma 3, Mistral) 3 with vLLM or OpenAI-compatible API
- **Data Storage**: JSON files, vector databases
- **Frontend**: Web-based chat interface

---

## 3. System Architecture

### 3.1 Architecture Overview

The system follows a layered architecture with six principal layers:

![](../images/ai%20persona%20-%20System%20Architecture%20Overview.png)

### 3.2 Core Components

#### 3.2.1 Frontend (FE)
- Web-based chat interface
- Persona selection and configuration UI
- File upload capabilities (PDF, images)
- Response visualization with citations

#### 3.2.2 Application Layer
- **Persona Configuration Service**: Manages persona selection and customization
- **Ingestion Service**: Handles raw data uploads and storage to S3
- **Report Service**: Generates structured analysis reports
- **Q&A Service**:  Manages interactive question-and-answer exchanges with the AI.
- **Auth Service**: Manages authentication and authorization

#### 3.2.3 Communication Layer
- **RPC Server**: Synchronous service-to-service communication
- **Cache (Redis-compatible)**: High-speed storage for frequently accessed data
- **Event Broker (RabbitMQ/Kafka)**: Asynchronous message passing for background tasks

#### 3.2.4 Core Layer (Detailed in Section 4)
The intelligence engine containing:
- **Orchestrator**: Central coordination hub
- **Input Handler**: Query normalization and preprocessing
- **Memory**: Conversation history management
- **RAG Pipeline**: Context retrieval from persona and fact data
- **Prompt Builder**: Dynamic prompt construction
- **AI Persona Router**: Model selection and inference
- **MCP Server**: External tool integration

#### 3.2.5 Monitoring Layer
- **Evaluation Tools**: Response quality assessment
- **Metrics Collection**: Latency, token usage, error rates
- **Alerting**: System health monitoring

#### 3.2.6 Storage Layer
- **Business Database**: User profiles, personas, configurations
- **Vector Database**: Embedded persona indicators and fact data
- **Object Storage (S3)**: Raw PDFs, images, processed artifacts

---

## 4. Core Processing Systems

### 4.1 The Orchestrator: Central Intelligence Hub

The **Orchestrator**  is the system's brain, coordinating all components to transform a user query into a contextually-grounded, persona-specific response.

#### 4.1.1 Orchestrator Architecture

**Component Composition:**
```python
@dataclass
class Orchestrator:
    input_handler: InputHandler          # Query normalization
    retriever: RAGPipeline              # Persona context retrieval
    fact_data_index: FactDataRAGIndex   # Quantitative data retrieval
    context_filter: ConversationContextFilter  # Context pruning
    prompt_builder: PromptBuilder        # Prompt assembly
    router: PersonaRouter               # Model inference
    memory: ConversationMemory          # History management
    cache: CacheClient                  # Response caching
```

#### 4.1.2 Request Processing Flow

The orchestrator processes each request through a carefully orchestrated pipeline:

**Step 1: Input Normalization**
```
Input: ChatRequest(persona_id, query, session_id, top_k)
↓
Normalization: Trim whitespace, basic text cleaning
Output: normalized_query
```

**Step 2: Conversation Memory Retrieval**
```
Fetch: Previous interactions for (persona_id, session_id)
Purpose: Maintain conversation continuity
Output: history = List[{query, response}]
```

**Step 3: Dual RAG Retrieval**

The system performs parallel retrieval from two knowledge sources:

**3a. Persona Context Retrieval**
```
Query: normalized_query
Source: Persona indicators (demographics, behaviors, preferences)
Method: Semantic similarity search in persona vector index
Parameters: k=top_k (e.g. 5,10,20)
Output: RetrievedContext(
    context: str,           # Concatenated relevant indicators
    citations: List[Citation],  # Source tracking
    raw: dict               # Original documents
)
```

**3b. Fact Data Retrieval**
```
Query Construction:
  - If persona has name/summary:
    "Segment: {persona_name}\nPersona summary: {summary}\n{query}"
  - Else: original query

Source: Extracted quantitative market data (demographics, purchase patterns)
Method: Semantic search in fact data vector index
Parameters: k=top_k (e.g. 5,10,20)
Output: fact_retrieved: RetrievedContext

Merging Strategy:
  merged_context = [persona_blocks] + [fact_data_blocks]
  merged_citations = [persona_citations] + [fact_citations]
```

**Step 4: Context Filtering**
```
History Filtering:
  - Apply relevance filter to conversation history
  - Keep only contextually relevant past exchanges

Retrieved Context Filtering:
  - Prune less relevant retrieved documents
  - Optimize token budget for LLM input
```

**Step 5: Prompt Construction**
```
Assembly:
  system_prompt = Generate from persona profile
                  (style, values, policies, filters)
  
  history_block = Format last 10 relevant exchanges
  
  context_block = Filtered retrieved contexts
  
  Full Prompt:
    SYSTEM PROMPT: {system_prompt}
    ------------
    HISTORY: {history_block}
    ------------
    CONTEXT: {context_block}
    ------------
    QUESTION: {normalized_query}
```

**Step 6: Persona Routing & Generation**
```
Router Selection:
  - Identify appropriate PEFT adapter for persona_id
  - Or fallback to base model with persona instructions

Generation:
  prompt → PersonaInferenceEngine → answer
  
Output: Persona-specific response (style, tone, critical thinking)
```

**Step 7: Memory Storage**
```
Store:
  message = {query: original_query, response: answer}
  
Storage Key: (persona_id, session_id)
Memory Management: Keep max 10 recent items per session
```

**Step 8: Response Assembly**
```
Output: ChatResponse(
    persona_id: str,
    answer: str,              # Generated response
    context: str,             # Contexts used
    citations: List[Citation] # Traceability
)
```


### 4.2 Data Pipeline Processing

The system has two parallel data extraction pipelines that transform raw PDFs into machine-readable, searchable knowledge bases.

#### 4.2.1 Persona Data Pipeline

**Purpose:** Extract rich, qualitative persona profiles from customer segmentation study PDFs.

**Location:** `adsp/data_pipeline/persona_data_pipeline/`

**Pipeline Stages:**

**Stage 1: Ingest & Render**
```
Input: PDF document (customer segmentation study)
Process:
  1. Load PDF using PDFRenderer
  2. Convert specified pages to high-resolution images (default 300 DPI)
  3. Cache rendered images to disk for reuse
  
Output: List[PageImage(page_number, image_path)]

```

**Stage 2: VLLM Page Extraction**
```
Input: Rendered page images + context window
Process:
  1. For each target page:
     a. Construct vision-language prompt with persona extraction instructions
     b. Include neighboring pages as context (configurable window)
     c. Send to vision-language model (e.g., Gemma 3, Mistral 3)
     d. Parse structured JSON response
  
  2. Concurrent processing (configurable max_concurrent_requests)


Output: List[PageExtractionResult(
    page_number: int,
    personas: List[Persona],
    general_content: str,
    raw_response: str,
    parsed_json: dict
)]

Extraction Output Structure:
  Persona {
    persona_id: str,
    persona_name: str,
    visual_description: str,
    summary_bio: str,
    indicators: List[Indicator]
  }
  
  Indicator {
    id: str,
    domain: str,        # "demographics", "coffee_behaviour", "media"
    category: str,      # "age_band", "format", "machine_ownership"
    label: str,         # Human-readable title
    description: str,
    sources: List[{doc_id, pages}],
    statements: List[Statement]
  }
  
  Statement {
    label: str,
    description: str,
    metrics: List[{value, unit, description}],
    salience: {
      is_salient: bool,
      direction: "high|low|neutral",
      magnitude: "strong|medium|weak",
      rationale: str
    },
    influences: {
      tone: bool,    # Affects how persona speaks
      stance: bool   # Affects what persona prioritizes
    }
  }
```

**Stage 3: Aggregate & Persist**
```
Input: All PageExtractionResults
Process:
  1. Merge personas across pages:
     - Combine indicators with same persona_id
     - Preserve page sources for traceability
     - Track salience flags
  
  2. Write structured outputs

Merge Strategy:
  - Group by persona_id
  - Merge indicators by domain/category/label
  - Combine statements, preserving duplicates with different metrics
  - Union all source references
```

**Stage 4: Reasoning (Trait Extraction)**
```
Input: Salient statements from persona profiles
Process:
  1. Filter statements where salience.is_salient == true
  
  2. Construct reasoning prompt:
     "Given these key indicators about the persona,
      derive their style_profile, value_frame,
      reasoning_policies, and content_filters"
  
  3. Send to text-based LLM
  
  4. Parse structured JSON response

Output: Per-persona reasoning traits saved to common_traits/{persona_id}.json

Reasoning Artifacts:
  style_profile {
    tone_adjectives: ["curious", "confident"],
    formality_level: "medium|high|low",
    directness: "very_direct|balanced|hedged",
    emotional_flavour: "neutral|enthusiastic|...",
    criticality_level: "high|medium|low",
    verbosity_preference: "concise|detailed|varies_by_question",
    preferred_structures: ["bullet_points", "pros_cons"],
    typical_register_examples: ["phrase1", "phrase2"]
  }
  
  value_frame {
    priority_rank: ["quality", "convenience", "sustainability"],
    sustainability_orientation: "high|medium|low",
    price_sensitivity: "high|medium|low",
    novelty_seeking: "high|medium|low",
    brand_loyalty: "high|medium|low",
    health_concern: "high|medium|low",
    description: "Natural language summary"
  }
  
  reasoning_policies {
    purchase_advice: {
      default_biases: ["prefer quality over price"],
      tradeoff_rules: ["sacrifice price before quality"]
    },
    product_evaluation: {
      praise_triggers: ["sustainable packaging"],
      criticism_triggers: ["vague marketing claims"],
      must_always_check: ["origin", "sustainability"]
    },
    information_processing: {
      trust_preference: ["data + evidence"],
      scepticism_towards: ["unverified health claims"],
      requested_rigor_level: "high|medium|low"
    }
  }
  
  content_filters {
    avoid_styles: ["overly emotional hype"],
    emphasise_disclaimers_on: ["health claims"]
  }
```

**Pipeline Orchestration:**
```
PersonaExtractionPipeline uses LangChain Runnable protocol:

Chain Definition:
  RenderPages 
  | PrepareExtractionPlan 
  | ExtractPages 
  | MergeOutputs 
  | Reasoner

```


#### 4.2.2 Fact Data Pipeline

**Purpose:** Extract quantitative market data and statistics from research PDFs for RAG retrieval.

**Location:** `adsp/data_pipeline/fact_data_pipeline/`

**Pipeline Stages:**

**Stage 1: Ingest & Render**
```
Identical to Persona Pipeline Stage 1
Output: List[PageImage]
```

**Stage 2: VLLM Page Extraction**
```
Input: Rendered page images
Process:
  1. For each page:
     a. Construct fact extraction prompt
        (extract: segments, demographics, market stats, trends)
     b. Send to VLLM
     c. Parse structured response
  
  2. Concurrent processing with caching

Output: Per-page JSON with extracted facts:
  PageExtractionResult {
    page_number: int,
    segment: str,
    section: str,
    template: str,
    facts: List[{
      label: str,
      value: str,
      context: str,
      metrics: List[{value, unit}]
    }],
    raw_response: str
  }
```

**Stage 3: Write Page Outputs**
```
Process:
  1. Write each page to raw_responses/page_{N}.json
  2. Generate page-level metadata

Output: Individual page JSON files
```

**Stage 4: JSON to Markdown Conversion** (Enabling RAG)
```
Input: raw_responses/page_*.json
Process:
  For each page JSON:
    1. Parse structured facts
    2. Convert to markdown format:
       - Segment header
       - Section subheader  
       - Fact list with metrics
       - Source attribution
    
    3. Embed metadata in frontmatter

Output: fact_data/pages/page_*.md

Example Markdown:
  ---
  page: 42
  segment: Traditional Consumers
  section: Demographics
  template: Age & Gender
  source_file: 2023_Market_Study.pdf
  ---
  
  # Traditional Consumers
  
  ## Demographics - Age & Gender
  
  - **Skewing Female**: 58% of segment, index 120 vs population
  - **Age Band 45-65**: Dominant age group (42%)
  - **Household Size**: Average 2.3 people
  
  Source: 2023_Market_Study.pdf, page 42
```

**Stage 5: Vector Indexing** 
```
At system startup (adsp/core/runtime.py):

Process:
  1. Scan fact_data/pages/ for page_*.md files
  
  2. For each markdown file:
     a. Parse frontmatter metadata
     b. Split content into chunks 
     c. Generate embeddings using semantic embedding model
        - Default: sentence-transformers/all-mpnet-base-v2
        - Captures semantic meaning of text chunks
        - Enables semantic similarity search
     d. Store in FactDataIndicatorRAG vector index
  
  3. Build in-memory vector store

Index Structure:
  FactDataRAGIndex {
    embeddings: Embeddings,
    rag: FactDataIndicatorRAG,
    indexed_chunk_ids: List[str]
  }

Retrieval Method:
  index.retrieve(query, k=10) → RetrievedContext(
    context: str,        # Concatenated relevant chunks
    citations: List[Citation],  # Source pages
    raw: dict            # Original documents
  )
```

**Pipeline Orchestration:**
```
FactDataExtractionPipeline:

Chain:
  RenderPages 
  | PrepareExtractionPlan 
  | ExtractPages 
  | WritePageOutputs

```


---

#### 4.2.3 Data Pipeline Comparison

| Aspect | Persona Pipeline | Fact Data Pipeline                               |
|--------|------------------|--------------------------------------------------|
| **Input** | Customer segmentation PDFs | Customer segmentation PDFs, Market research PDFs |
| **Output** | Persona profiles with indicators | Quantitative facts and statistics                |
| **Extraction Target** | Qualitative insights (behaviors, preferences) | Quantitative data (demographics, metrics)        |
| **Post-Processing** | Reasoning trait derivation | Markdown conversion for RAG                      |
| **Storage Format** | JSON (individual + traits) | Markdown + JSON                                  |


### 4.3 RAG (Retrieval-Augmented Generation) System

#### 4.3.1 Dual RAG Architecture

The system implements a **Dual RAG Strategy** to combine qualitative persona knowledge with quantitative market facts:

**RAG Pipeline Component:**
```python
@dataclass
class RAGPipeline:
    vector_db: VectorDatabase           # Fallback string store
    persona_index: PersonaRAGIndex      # Persona indicator vectors
    
    def retrieve_with_metadata(
        persona_id: str, 
        query: str, 
        k: int = 5
    ) -> RetrievedContext
```

**Retrieval Process:**

**1. Persona Context Retrieval**
```
Index: PersonaRAGIndex
  - One vector store per persona_id
  - Indexed documents = persona indicators converted to text
  
Indexing Process:
  For each Indicator in persona.indicators:
    document_text = f"{indicator.label}: {indicator.description}"
    for statement in indicator.statements:
      document_text += f"\n- {statement.description}"
      if statement.metrics:
        document_text += f" ({format_metrics(metrics)})"
    
    metadata = {
      persona_id, 
      domain, 
      category, 
      sources
    }
    
    vector_store.add_document(document_text, metadata)

Query Process:
  1. Embed query using HashEmbeddings (or external embedder)
  2. Similarity search in persona's vector store (k=5)
  3. Retrieve top-k most relevant indicator documents
  4. Format as context prompt with citations

Output:
  RetrievedContext(
    context: "Formatted indicator statements",
    citations: [Citation(doc_id, pages, domain, category, label)],
    raw: {documents: [...]}
  )
```

**2. Fact Data Retrieval**
```
Index: FactDataRAGIndex
  - Single unified vector store across all fact data
  - Indexed documents = markdown chunks with metadata
  
Indexing Process:
  For each page_*.md:
    1. Parse markdown and frontmatter
    2. Split into semantic chunks (~500 tokens)
    3. Embed chunks
    4. Store with metadata: {
         source_file, 
         page_number, 
         segment, 
         section, 
         template
       }

Enhanced Query Process:
  1. Build enriched query:
     If persona has name/bio:
       query = f"Segment: {persona_name}\n
                Persona summary: {summary}\n
                {original_query}"
     Else:
       query = original_query
  
  2. Embed enhanced query
  3. Similarity search across all fact data (k=10)
  4. Retrieve relevant chunks
  5. Format with citations

Output:
  RetrievedContext(
    context: "Formatted fact chunks",
    citations: [Citation(source_file, pages, segment, section)],
    raw: {documents: [...]}
  )
```

**3. Context Merging**
```
Orchestrator merges both retrieval results:

def _merge_retrieved_contexts(
    persona: RetrievedContext,
    fact: RetrievedContext
) -> RetrievedContext:
    
    # Split contexts by separator
    persona_blocks = split(persona.context)
    fact_blocks = split(fact.context)
    
    # Concatenate
    merged_blocks = persona_blocks + fact_blocks
    merged_citations = persona.citations + fact.citations
    
    return RetrievedContext(
        context=join(merged_blocks),
        citations=merged_citations,
        raw={documents: merged_docs}
    )
```

#### 4.3.2 Embedding Strategy


**Primary: Semantic Embedding Models (for converting text into vector representations)**

Uses pre-trained transformer-based models to capture deep semantic meaning:

```python
from sentence_transformers import SentenceTransformer

# Load pre-trained embedding model
embedding_model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')

# Generate embeddings
text_chunks = [
    "Traditional consumers prefer whole bean coffee for quality",
    "Age distribution skews 45-65 years old",
    "High sustainability orientation with 85% environmental concern"
]

embeddings = embedding_model.encode(text_chunks)
# Output: numpy array of shape (3, 768) - 768-dimensional dense vectors
```

**Model Characteristics:**
- **Model**: `sentence-transformers/all-mpnet-base-v2`
- **Architecture**: MPNet (Masked and Permuted Pre-training)
- **Dimensions**: 768 (dense vectors)
- **Training**: Fine-tuned on 1B+ sentence pairs for semantic similarity
- **Performance**: State-of-the-art on semantic textual similarity benchmarks
- **Use Case**: Captures nuanced semantic meaning, synonyms, paraphrases

**Benefits:**
- Superior semantic understanding compared to keyword matching
- Handles paraphrases and synonyms effectively
- Pre-trained on diverse domains, generalizes well
- Standard in production RAG systems

**Alternative Models:**
- `sentence-transformers/all-MiniLM-L6-v2`: Faster, smaller (384-dim), good for resource-constrained environments
- `intfloat/e5-large-v2`: Higher quality (1024-dim), better performance on complex queries
- OpenAI `text-embedding-3-small`: Cloud-based, 1536-dim, excellent quality


### 4.4 Prompt Construction System

#### 4.4.1 Dynamic Prompt Assembly

The **PromptBuilder** (`adsp/core/prompt_builder/__init__.py`) constructs context-rich prompts by combining multiple information sources.

**Prompt Template Structure:**
```
SYSTEM PROMPT:
{persona_system_instructions}
------------
[HISTORY:
{conversation_history}
------------]
CONTEXT:
{retrieved_contexts}
-------------

QUESTION:
{user_query}
```

#### 4.4.2 System Prompt Generation

**From Persona Profile with Reasoning Traits:**
```python
def persona_to_system_prompt(persona: PersonaProfileModel) -> str:
    """Generate comprehensive system instructions from persona."""
    
    sections = [
        # Core identity
        f"You are {persona.persona_name}",
        persona.summary_bio,
        persona.visual_description,
        
        # Style guidance (from reasoning traits)
        style_instructions(persona.style_profile),
        
        # Value priorities (from reasoning traits)
        value_instructions(persona.value_frame),
        
        # Behavioral rules (from reasoning traits)
        reasoning_instructions(persona.reasoning_policies),
        
        # Safety guardrails (from reasoning traits)
        filter_instructions(persona.content_filters),
        
        # Key facts
        salient_indicators(persona.key_indicators)
    ]
    
    return "\n\n".join(sections)
```

**Style Instructions Example:**
```
Communication Style:
- Tone: curious, confident, quality-focused, pragmatic
- Formality: medium
- Directness: balanced (neither overly blunt nor hedged)
- Emotional flavor: warm_reflective
- Critical thinking: high (provide honest, critical feedback)
- Verbosity: detailed when explaining tradeoffs

Preferred structures:
- Use bullet points for clarity
- Present clear tradeoffs in decisions
- Employ pros/cons format when evaluating options

Example register: 
"I appreciate the focus on sustainability, but I'd want to see 
 concrete evidence of impact rather than vague claims."
```

**Value Instructions Example:**
```
Core Values (Priority Ranking):
1. Quality
2. Sustainability
3. Convenience
4. Price

Orientation Flags:
- Sustainability: HIGH - always consider environmental impact
- Price sensitivity: MEDIUM - will pay more for quality
- Novelty seeking: LOW - prefer proven, reliable options
- Brand loyalty: HIGH - strong preference for trusted brands
- Health concern: MEDIUM - aware but not obsessive

When advising or evaluating products, prioritize these values in order.
```

**Reasoning Policy Instructions Example:**
```
Purchase Advice Rules:
- Default bias: Prefer quality even at higher price points
- Tradeoff rule: If forced to choose, sacrifice price before quality
- Tradeoff rule: Flag environmental impact of packaging when relevant

Product Evaluation Guidelines:
- Praise when: Sustainable sourcing, ethical production, premium quality
- Criticize when: Vague marketing claims, greenwashing, unclear origin
- Must always check: Country of origin, sustainability certifications

Information Processing:
- Trust: Data-backed claims, expert sources, real-world usage evidence
- Be skeptical of: Vague marketing language, unverified health promises
- Rigor level: HIGH - demand concrete evidence
```

#### 4.4.3 Context Block Construction

**Retrieved Context Formatting:**
```
Format: concatenated indicator blocks separated by "---"

Example:
Demographics - Age Band:
- Majority aged 45-65 (42% of segment, index 135 vs population)
- Higher representation in 55+ bracket
Source: 2023_Consumer_Segmentation.pdf, pages 12, 15

---

Coffee Consumption - Purchase Frequency:
- Weekly coffee buyers (78% purchase weekly, index 120)
- Average 3.2 purchases per week
- Prefer morning consumption (87%)
Source: 2023_Consumer_Segmentation.pdf, page 24

---

Sustainability Attitudes - Environmental Concern:
- High concern for environmental impact (85% strongly agree)
- Willing to pay premium for sustainable packaging (+15-20%)
Source: 2023_Market_Study.pdf, page 31
```

#### 4.4.4 History Block Construction

**Format:**
```
Conversation history (reference only; most recent last):
- User: What coffee formats do I prefer?
- Persona: You show a strong preference for whole bean coffee 
           (65% of purchases), valuing freshness and quality. 
           You occasionally purchase ground coffee for convenience.
- User: How do I feel about single-serve pods?
- Persona: You're skeptical of single-serve pods due to 
           environmental concerns (plastic waste). While you 
           appreciate the convenience, sustainability is a 
           higher priority for you.
```

**Memory Management:**
- Keep maximum last 10 exchanges per (persona_id, session_id)
- Filter for relevance to current query
- Include in prompt to maintain conversation continuity

---

### 4.5 AI Persona Router & Inference

#### 4.5.1 Persona Router

**Component:** `adsp/core/ai_persona_router/`

**Function:** Routes prompts to persona-specific model endpoints (PEFT adapters).

```python
@dataclass
class PersonaRouter:
    inference_engine: PersonaInferenceEngine
    
    def dispatch(self, persona_id: str, prompt: str) -> str:
        return self.inference_engine.generate(
            persona_id=persona_id,
            prompt=prompt
        )
```

#### 4.5.2 Inference Engine

**PersonaInferenceEngine** (`adsp/modeling/inference.py`):
- Manages connections to LLM backends (vLLM, OpenAI-compatible APIs)
- Routes to persona-specific PEFT adapters when available
- Falls back to base model with enhanced prompts
- Handles generation parameters (temperature, max_tokens)

**Inference Flow:**
```
1. Receive (persona_id, prompt)
2. Check if PEFT adapter exists for persona_id
3. If adapter exists:
   - Load adapter
   - Generate with persona-tuned model
4. Else:
   - Use base model
   - Rely on prompt engineering
5. Post-process response
6. Return answer string
```

---

### 4.6 Memory & Context Management

#### 4.6.1 Conversation Memory

**ConversationMemory** (`adsp/core/memory/`):
```python
@dataclass
class ConversationMemory:
    max_items: int = 10
    _messages: Dict[Tuple[persona_id, session_id], List[dict]]
    
    def store(self, persona_id, session_id, message: dict):
        history = self._messages[(persona_id, session_id)]
        history.append(message)
        if len(history) > max_items:
            history.pop(0)
    
    def get_history(self, persona_id, session_id) -> List[dict]:
        return self._messages[(persona_id, session_id)]
```

**Storage Format:**
```json
{
  ("basic-traditional", "user123_session1"): [
    {"query": "What coffee do I like?", "response": "You prefer..."},
    {"query": "How about pods?", "response": "You're skeptical..."}
  ]
}
```

#### 4.6.2 Context Filter

**ConversationContextFilter** (`adsp/core/context_filter.py`):
- Prunes less relevant history items
- Filters retrieved contexts to fit token budget
- Prioritizes recent and relevant information
- Ensures prompt stays within model context window

---

### 4.7 System Startup & Initialization

**Runtime Builder** (`adsp/core/runtime.py`):

**Initialization Sequence:**
```python
def build_default_orchestrator() -> Orchestrator:
    # 1. Load persona profiles
    individual_dir = "data/processed/personas/individual"
    traits_dir = "data/processed/personas/common_traits"
    personas = load_personas_from_disk(individual_dir, traits_dir)
    
    # 2. Build persona registry
    registry = PersonaRegistry()
    for persona in personas:
        registry.upsert(persona.persona_id, persona)
    
    # 3. Build persona RAG index
    persona_index = PersonaRAGIndex()
    persona_index.index_personas(personas)
    
    # 4. Build fact data RAG index (optional)
    fact_data_index = build_fact_data_index()
    
    # 5. Assemble orchestrator
    return Orchestrator(
        prompt_builder=PromptBuilder(registry=registry),
        retriever=RAGPipeline(persona_index=persona_index),
        fact_data_index=fact_data_index
    )
```

**Fact Data Index Initialization:**
```python
def build_fact_data_index() -> FactDataRAGIndex:
    markdown_dir = "data/processed/fact_data/pages"
    
    # Check if markdown files exist
    if markdown_exists(markdown_dir):
        index = FactDataRAGIndex()
        count = index.index_markdown_directory(
            markdown_dir, 
            pattern="page_*.md"
        )
        logger.info(f"Indexed {count} fact data chunks")
        return index
    
    # Attempt JSON to markdown conversion
    json_dir = "data/interim/fact_data/raw_responses"
    if json_exists(json_dir):
        run_json_to_markdown_conversion(json_dir, markdown_dir)
        index = FactDataRAGIndex()
        index.index_markdown_directory(markdown_dir)
        return index
    
    # Optionally run extraction pipeline
    if env_flag("ADSP_FACTDATA_RUN_EXTRACTION"):
        run_fact_data_extraction_pipeline()
        run_json_to_markdown_conversion(...)
        return build_index(...)
    
    return None
```

---


## 5. Interface

### 5.1 REST API Endpoints

**Chat Endpoint:**
```
POST /api/v1/chat
Request:
{
  "persona_id": "basic-traditional",
  "query": "What coffee formats do I prefer?",
  "session_id": "user123_session1",
  "top_k": 5
}

Response:
{
  "persona_id": "basic-traditional",
  "answer": "You show a strong preference for...",
  "context": "Demographics - Age Band:\n- Majority aged...",
  "citations": [
    {
      "doc_id": "2023_Consumer_Segmentation.pdf",
      "pages": [12, 15],
      "domain": "demographics",
      "category": "age_band",
      "indicator_label": "Age Distribution"
    }
  ]
}
```

**List Personas Endpoint:**
```
GET /api/v1/personas

Response:
{
  "personas": [
    {
      "persona_id": "basic-traditional",
      "persona_name": "Traditional Consumer",
      "summary_bio": "Quality-focused, loyal to trusted brands..."
    }
  ]
}
```

### 5.2 Command-Line Interface

**Chat Script:**
```bash
python scripts/run_chat.py chat \
  --persona-id basic-traditional \
  --query "What coffee do I like?"
```

**List Personas:**
```bash
python scripts/run_chat.py list-personas
```

**Run Extraction Pipeline:**
```bash
python scripts/extract_personas.py \
  --pdf data/raw/segmentation_study.pdf \
  --output data/processed/personas
```

---

## 6. System Operation

### 6.1 Typical Request Flow (End-to-End)

**User Action:** User asks "What coffee formats do I prefer?" to "Basic Traditional" persona

**System Processing:**

```
1. Frontend (FE)
   └─> POST /api/v1/chat
       {persona_id: "basic-traditional", query: "What coffee..."}

2. Application Layer: Q&A Service
   └─> Validate request
   └─> Route to Orchestrator

3. Core Layer: Orchestrator.handle(request)
   
   3.1. InputHandler.normalize("What coffee formats do I prefer?")
        → "What coffee formats do I prefer?"  
   
   3.2. Memory.get_history("basic-traditional", "session123")
        → [previous 2 exchanges]  
   
   3.3. RAGPipeline.retrieve_with_metadata(
            persona_id="basic-traditional",
            query="What coffee formats do I prefer?",
            k=5
        )
        3.3.1. PersonaRAGIndex.search()
               → Find indicators about coffee formats
               → Top 5 documents:
                 1. "Coffee Consumption - Format Preference"
                 2. "Purchase Behavior - Product Types"
                 3. "Quality Perception - Whole Bean vs Ground"  
        
        3.3.2. Return RetrievedContext with citations
   
   3.4. FactDataRAGIndex.retrieve(
            query="Segment: Traditional Consumer\n
                   Persona summary: Quality-focused...\n
                   What coffee formats do I prefer?",
            k=5
        )
        → Find quantitative data about format preferences
        → Top 5 chunks:
          1. "65% purchase whole bean coffee (index 145)"
          2. "Format distribution: 65% whole bean, 25% ground..."
   
   3.5. Merge persona + fact contexts
        → Combined context (1200 characters)
   
   3.6. ContextFilter.filter_history(history, query)
        → Keep relevant past exchanges
   
   3.7. ContextFilter.filter_retrieved(merged_context, query)
        → Prune to fit token budget
   
   3.8. PromptBuilder.build(
            persona_id="basic-traditional",
            query=normalized,
            context=filtered_context,
            history=filtered_history
        )
        → Construct full prompt:
           SYSTEM PROMPT: You are Traditional Consumer...
           Style: confident, quality-focused...
           Values: quality > convenience > price...
           HISTORY: [previous exchanges]
           CONTEXT: [filtered indicators + facts]
           QUESTION: What coffee formats do I prefer?
   
   3.9. PersonaRouter.dispatch("basic-traditional", prompt)
        → Send to PersonaInferenceEngine
        → Call LLM backend (vLLM/OpenAI)
        → Generate response matching style/values
        
        Generated Answer:
        "You show a strong preference for whole bean coffee,
         which represents 65% of your purchases. You value
         the freshness and quality that whole beans provide.
         While you occasionally buy ground coffee for
         convenience (25% of purchases), quality is your
         top priority, so you're willing to invest the
         extra effort in grinding beans yourself."
   
   3.10. Memory.store(
             persona_id="basic-traditional",
             session_id="session123",
             message={
               query: "What coffee formats do I prefer?",
               response: "You show a strong preference..."
             }
         )
   
   3.11. Assemble ChatResponse
         → Include answer, context, citations

4. Application Layer: Q&A Service
   └─> Return response to Frontend

5. Frontend (FE)
   └─> Display answer to user
   └─> Show citations with source links

```

##  Appendices

### Appendix A: Key File Locations

**Core System:**
- `adsp/core/orchestrator/__init__.py` - Main orchestration logic
- `adsp/core/runtime.py` - System initialization
- `adsp/core/rag/__init__.py` - RAG pipeline
- `adsp/core/prompt_builder/__init__.py` - Prompt construction
- `adsp/core/ai_persona_router/__init__.py` - Model routing

**Data Pipelines:**
- `adsp/data_pipeline/persona_data_pipeline/extract_raw/pipeline.py`
- `adsp/data_pipeline/fact_data_pipeline/extract_raw/pipeline.py`
- `adsp/data_pipeline/schema.py` - Persona profile schema

**Indexes:**
- `adsp/core/rag/persona_index.py` - Persona RAG index
- `adsp/core/rag/fact_data_index.py` - Fact data RAG index

**Scripts:**
- `scripts/run_chat.py` - CLI chat interface
- `scripts/run_api.py` - FastAPI server

### Appendix B: Configuration Reference

**Environment Variables:**
```
# LLM Backend
ADSP_LLM_BACKEND=openai
ADSP_LLM_BASE_URL=http://localhost:8000/v1
ADSP_LLM_MODEL=mistralai/mistral-medium-3-instruct
ADSP_LLM_API_KEY=EMPTY

# Fact Data RAG
ADSP_FACTDATA_RAG_ENABLED=true
ADSP_FACTDATA_MARKDOWN_DIR=data/processed/fact_data/pages
ADSP_FACTDATA_JSON_DIR=data/interim/fact_data/raw_responses
ADSP_FACTDATA_RUN_EXTRACTION=false

# Personas
ADSP_PERSONAS_DIR=data/processed/personas/individual
ADSP_PERSONA_TRAITS_DIR=data/processed/personas/common_traits

# Embedding Model
ADSP_EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2  # Production
# ADSP_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2  # Lightweight
# ADSP_EMBEDDING_MODEL=intfloat/e5-large-v2                   # High performance
# ADSP_EMBEDDING_MODEL=hash                                   # Development only
ADSP_EMBEDDING_DEVICE=cuda  # or 'cpu' for CPU-only deployment

# Vision Model (for extraction)
VLLM_MODEL=llava-v1.6-vicuna-13b
VLLM_API_BASE=http://localhost:8000/v1
VLLM_API_KEY=EMPTY
```


### Appendix C: Glossary

- **Citation**: Reference to source document and page numbers
- **Context**: Retrieved information provided to LLM as grounding
- **Dense Vector**: High-dimensional numeric representation of text capturing semantic meaning
- **Embedding**: Vector representation of text for similarity search; modern systems use transformer-based models like sentence-transformers to encode semantic meaning into dense vectors (typically 384-1024 dimensions)
- **Indicator**: Structured grouping of persona insights (domain/category/label)
- **Orchestrator**: Central coordination engine for query processing
- **PEFT**: Parameter-Efficient Fine-Tuning (LoRA, adapters)
- **RAG**: Retrieval-Augmented Generation
- **Salience**: Measure of statement importance (visual emphasis in source)
- **Semantic Similarity**: Measure of meaning similarity between texts, computed using cosine similarity of embedding vectors
- **Sentence Transformers**: Family of pre-trained models optimized for generating semantically meaningful sentence embeddings
- **Statement**: Individual insight within an indicator
- **VLLM**: Vision-Language Model for PDF extraction

---

**Document End**
