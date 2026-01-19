# 2025-P3-AI-Personas - Team 1

<a target="_blank" href="https://cookiecutter-data-science.drivendata.org/">
    <img src="https://img.shields.io/badge/CCDS-Project%20template-328F97?logo=cookiecutter" />
</a>

Applied Data Science Project

## Description

The **Lavazza AI Personas** project transforms static customer segmentation studies into dynamic, conversational AI agents that authentically represent Lavazza's customer segments. This system serves as a next-generation consumer insights platform for market research, idea validation, and strategic decision-making.

### Key Features

- **Authentic Personality**: AI personas that embody specific customer segments with consistent tone, style, and values
- **Factual Grounding**: RAG-based system that prevents hallucinations by grounding responses in Lavazza's proprietary data
- **Critical Thinking**: Personas provide honest, critical feedback rather than generic positive responses
- **Transparency**: Clear source attribution showing whether information comes from internal documentation or external sources
- **Multimodal Support**: Process text, images, and PDF documents (e.g., packaging designs, concept notes)
- **Virtual Focus Groups**: Interact with multiple personas simultaneously for comprehensive feedback

## Getting Started

### Installation

```bash
make install
```

### Data Extraction Pipelines

#### 1. Persona Extraction Pipeline

Extract persona indicators (demographics, behaviors, values) from PDF segmentation studies:

```bash
python scripts/run_persona_extraction.py \
  --pdf-path data/raw/segmentation_study.pdf \
  --page-range 1,50 \
  --vllm-base-url http://localhost:8000/v1 \
  --vllm-model mistralai/mistral-medium-3-instruct \
  --generate-reasoning-profiles
```

Key options:
- `--pdf-path`: Path to segmentation study PDF
- `--page-range`: Pages to process (1-based, inclusive)
- `--vllm-base-url`: OpenAI-compatible API endpoint
- `--vllm-model`: Vision model for extraction
- `--generate-reasoning-profiles`: Generate style/value/guardrail profiles
- `--no-cache`: Force re-extraction (ignore cached responses)

Outputs:
- `data/interim/personas/personas.json`: Merged persona data
- `data/interim/personas/individual/{persona_id}.json`: Individual persona files
- `data/interim/personas/common_traits/{persona_id}.json`: Reasoning profiles

#### 2. Fact Extraction Pipeline

Convert PDF pages to structured markdown for RAG indexing:

```bash
python scripts/run_fact_data_extraction.py \
  --pdf-path data/raw/segmentation_study.pdf \
  --page-range 1,100 \
  --vllm-base-url http://localhost:8000/v1 \
  --vllm-model mistralai/mistral-large-3-675b-instruct-2512
```

Key options:
- `--pdf-path`: Path to source PDF
- `--page-range`: Pages to extract (1-based, inclusive)
- `--context-window`: Adjacent pages for context (default: 0)

Outputs:
- `data/interim/fact_data/{doc_id}/pages/`: Per-page markdown files
- `data/interim/fact_data/{doc_id}/qa_report.txt`: Quality assurance report

#### 3. Index Fact Data for RAG

Index extracted facts into the vector database:

```bash
python scripts/index_fact_data.py \
  --fact-data-dir data/interim/fact_data/segmentation_study \
  --vector-db-path data/processed/vector_store
```

### Running the Application

#### Backend API

Start the FastAPI backend server:

```bash
python scripts/run_api.py
```

- Swagger UI: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

Advanced options:

```bash
# Uvicorn with auto-reload
python scripts/run_api.py --mode uvicorn --reload

# Direct mode for debugging
python scripts/run_api.py --mode direct --debug
```

Environment variables:
- `ADSP_API_RUN_MODE`: `uvicorn` (default) or `direct`
- `ADSP_API_HOST`, `ADSP_API_PORT`: Host and port configuration
- `ADSP_API_RELOAD`: `true`/`false` (uvicorn mode only)
- `ADSP_API_DEBUG`: `true`/`false`
- `ADSP_API_LOG_LEVEL`: `info`, `debug`, etc.

#### Frontend UI

Launch the Streamlit frontend:

```bash
python scripts/run_frontend.py
```

The frontend will be available at `http://localhost:8501`

#### LLM Backend Configuration

To use an OpenAI-compatible LLM backend (e.g., vLLM):

```bash
export ADSP_LLM_BACKEND=openai
export ADSP_LLM_BASE_URL=http://localhost:8000/v1
export ADSP_LLM_MODEL=mistralai/mistral-small-24b-instruct
export ADSP_LLM_API_KEY=EMPTY
```

### Quickstart Demo (CLI)

Test personas via command line:

```bash
python scripts/run_chat.py list-personas
python scripts/run_chat.py chat --persona-id basic-traditional
```

## Evaluation Results

The system has been evaluated across four key dimensions using Mistral models:

### 1. Persona Extraction

**Model**: `mistralai/mistral-medium-3-instruct`  
**Dataset**: 23 pages (Curious Connoisseurs segment), 1,051 manually validated metrics

| Metric | Score | Interpretation |
|--------|-------|----------------|
| Persona Detection Rate | 100% | All personas correctly identified (23/23) |
| Metrics Recall | 95.30% | Very high coverage of ground-truth metrics (1002/1051) |
| Metrics Precision | 96.80% | Minimal noise in extracted metrics (1002/1035) |

### 2. Fact Extraction

**Model**: `mistralai/mistral-large-3-675b-instruct-2512`  
**Dataset**: 23 pages, 467 validated metric snippets

| Metric | Score | Interpretation |
|--------|-------|----------------|
| Exact Match Accuracy | 97% | High extraction accuracy with minimal deviation |


### 3. Retrieval Relevance

**Embedding Model**: `sentence-transformers/all-mpnet-base-v2`  
**RAG Setup**: 222-page document, 712 chunks (1,200 chars, 50 overlap)

| Metric | Score | Interpretation |
|--------|-------|----------------|
| Precision@3 | 89.25% | Top-3 results are mostly relevant |
| Precision@5 | 88.39% | High relevance persists in top 5 |
| Precision@10 | 86.13% | Strong top-10 relevance with minor noise |
| Precision@20 | 82.58% | Relevance remains high but dilutes with depth |
| Precision@25 | 80.90% | Moderate noise beyond top 20 |
| Recall@3 | 14.87% | Small share of relevant docs in top 3 |
| Recall@5 | 23.35% | Less than a quarter in top 5 |
| Recall@10 | 45.98% | Roughly half captured by top 10 |
| Recall@20 | 82.08% | Most relevant docs retrieved by top 20 |
| **Recall@25** | **100.00%** | **All relevant docs retrieved by top 25** |

### 4. Persona Authenticity

**Models**: `mistralai/mistral-medium-3-instruct` (filter), `mistralai/mistral-small-24b-instruct` (generation)  
**RAG Setup**: 222-page document, 712 chunks (1,200 chars, 50 overlap)  
**Dataset**: 31 evaluation questions (Curious Connoisseurs segment)

| Metric | Score | Interpretation |
|--------|-------|----------------|
| Expert Authenticity Score | 4.66 / 5 | Persona behavior is highly authentic |
| Style Alignment Score | 4.74 / 5 | Style is highly consistent, with minimal drift |
| Factual Grounding Score | 4.44 / 5 | Responses are well grounded |

**Key Finding**: Authenticity, style alignment, and grounding all score above 4.4/5, indicating strong persona fidelity with consistent style and reliable grounding.

For detailed evaluation methodology and results, see `reports/evaluation/`.

## Project Organization

```
├── LICENSE            <- Open-source license if one is chosen
├── Makefile           <- Makefile with convenience commands like `make data` or `make train`
├── README.md          <- The top-level README for developers using this project.
├── data
│   ├── external       <- Data from third party sources.
│   ├── interim        <- Intermediate data that has been transformed.
│   ├── processed      <- The final, canonical data sets for modeling.
│   └── raw            <- The original, immutable data dump.
│
├── docs               <- Design notes, ADRs, and folder structure reference
│
├── models             <- Trained and serialized models, model predictions, or model summaries
│
├── notebooks          <- Jupyter notebooks. Naming convention is a number (for ordering),
│                         the creator's initials, and a short `-` delimited description, e.g.
│                         `1.0-jqp-initial-data-exploration`.
│
├── pyproject.toml     <- Project configuration file with package metadata for 
│                         adsp and configuration for tools like black
│
├── references         <- Data dictionaries, manuals, and all other explanatory materials.
│
├── reports            <- Generated analysis as HTML, PDF, LaTeX, etc.
│   └── figures        <- Generated graphics and figures to be used in reporting
│
├── requirements.txt   <- The requirements file for reproducing the analysis environment, e.g.
│                         generated with `pip freeze > requirements.txt`
│
├── setup.cfg          <- Configuration file for lint/format tools
│
└── adsp                        <- Source code for use in this project.
    ├── __init__.py             <- Python package bootstrapper
    ├── config.py               <- Shared paths and environment config
    ├── app/                    <- UI-facing services (auth, ingestion, reporting, Q&A)
    ├── fe/                     <- Frontend stubs (chat client, upload UI)
    ├── communication/          <- RPC, cache, and event broker adapters
    ├── core/                   <- Orchestrator, prompt/RAG, persona routing, memory, tool use
    ├── data_pipeline/          <- Data ingestion, transformation, vectorization
    ├── modeling/               <- Training and inference utilities
    ├── monitoring/             <- Evaluation + metrics collection
    ├── storage/                <- Business DB, object store, vector DB shims
    └── utils/                  <- Logging, exceptions, helpers
```

--------


## How to contribute

### **Commit Message and Branch Naming Rules**

1. **Commit Message Format**
    - Use the following format for commit messages:
      ```
      <type>: <short description>
      ```
    - **Types**:
      - `feature` or`feat`: A new feature
      - `fix`: A bug fix
      - `docs`: Documentation changes
      - `chore`: maintenance tasks, repo setup, config, etc.
      - `style`: Code style changes (formatting, missing semicolons, etc.)
      - `refactor`: Code refactoring without adding features or fixing bugs
      - `test`: adding or updating tests.
    - Example:
      ```
      feat: add data preprocessing pipeline
      fix: resolve issue with model training script
      ```
    - Details: [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) 

2. **Branch Naming Convention**
    - Use the following format for branch names:
      ```
      <type>/<short-description>
      ```
    - **Types**:
      - `main` or `master`: Stable, production-ready code
      - `develop`: Integration branch for features before release (optional)
      - `feature` or `feat`: For new features or enhancements
      - `fix`: For bug fixes
      - `hotfix`: For urgent production fixes
      - `chore`: For maintenance, build, or config tasks
      - `docs`: For documentation-only changes
      - `refactor`: For code refactoring without behavior change
      - `test`: For adding or updating tests
      - `release`: For preparing production releases
    - Example:
     ```
     feat/add-preprocessing-pipeline
     fix/model-training-bug
     ```
    - Details: [Git Branch Naming Convention](https://conventional-branch.github.io/#specification)
    
    - Branch Flow:
    ```
    main <--- release <--- develop <--- feature
     ^                         |
     |                         |
     └-------- hotfix ---------┘
   ```
### **Jupyter Notebook Usage**

1. **Notebook Organization**
    - Notebooks must be stored in the `notebooks/` directory.
    - Naming convention: `PHASE.NOTEBOOK-INITIALS-DESCRIPTION.ipynb`
        
        Example: `0.01-pjb-data-source-1.ipynb`
        
        - `PHASE` codes:
            - `0` – Data exploration
            - `1` – Data cleaning & feature engineering
            - `2` – Visualization
            - `3` – Modeling
            - `4` – Publication
        - `INITIALS` – Your initials; helps identify the author and avoid conflicts.
        - `DESCRIPTION` – Short, clear description of the notebook's purpose.

### **Code Reusability & Refactoring Regulation**

1. **Refactor Shared Code into Modules**
    - Store reusable code in the `src/` package.
    - Add the following cell at the top of each notebook:

    ```python
    %load_ext autoreload
    %autoreload 2
    ```
