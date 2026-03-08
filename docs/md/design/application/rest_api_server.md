# Application: REST API Server (FastAPI)

**Code**: `adsp/app/api_server.py`

## Purpose

Expose the Application layer over HTTP so external clients (frontend/UI, tools, other services) can interact with:
- authentication
- persona discovery
- persona chat (Q&A)
- ingestion (upload)
- reports

The server is designed for local development and demos. It wires existing in-process services (`adsp/app/*`) and returns typed JSON responses.

## Key technologies

- **FastAPI**: REST framework + OpenAPI generation
- **Pydantic**: request/response validation (reuses `adsp/core/types.py`)
- **Uvicorn**: ASGI server

Dependencies are declared in `requirements.txt` (`fastapi`, `uvicorn[standard]`).

## Runtime architecture (in-process)

On startup, the API server creates and stores service singletons:

- `AuthService` (`adsp/app/auth_service.py`)
- `QAService` (`adsp/app/qa_service.py`) → uses Core orchestrator with local RAG + persona loading
- `IngestionService` (`adsp/app/ingestion_service.py`) → writes to `object_store` shim
- `ReportService` (`adsp/app/report_service.py`) → writes markdown to `reports/api/` by default
- `SurveyManager` (`adsp/core/survey/survey_manager.py`) → stores survey definitions
- `GroupGenerator` (`adsp/core/survey/group_generator.py`) → creates respondent groups
- `ResponseSynthesizer` (`adsp/core/survey/response_synthesizer.py`) → runs survey simulations and exports results

These are accessible to endpoints via a FastAPI dependency (`get_services()`).

## Authentication model (dev)

If `ADSP_REQUIRE_AUTH=true`, protected endpoints require:
- `X-User: <user>`
- `X-Token: <token>`

Register tokens via:
- `POST /v1/auth/register`

When `ADSP_REQUIRE_AUTH` is unset/false, endpoints are open for local demo convenience.

## Swagger / OpenAPI

- Swagger UI: `GET /docs`
- OpenAPI JSON: `GET /openapi.json`
- ReDoc: `GET /redoc`

## Endpoints

### System

- `GET /health`
  - Response fields:
    - `status`: API health indicator (`ok` when service is up)
    - `version`: API version string
    - `qa_status`: QA service warmup status (`idle|warming|ready|error`)
  - Example:

```bash
curl -X GET "http://localhost:8000/health"
```

### Auth

- `POST /v1/auth/register`
  - Request fields:
    - `user`: user identifier
    - `token`: API token assigned to this user
  - Response fields:
    - `status`: registration result (`ok`)
  - Example:

```bash
curl -X POST "http://localhost:8000/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"user":"demo-user","token":"demo-token-123"}'
```

- `POST /v1/auth/validate`
  - Request fields:
    - `user`: user identifier to validate
    - `token`: token to validate
  - Response fields:
    - `authorized`: `true` when user/token pair matches registry
  - Example:

```bash
curl -X POST "http://localhost:8000/v1/auth/validate" \
  -H "Content-Type: application/json" \
  -d '{"user":"demo-user","token":"demo-token-123"}'
```

### Personas

- `GET /v1/personas`
  - Response fields:
    - `personas`: array of persona summaries
    - `persona_id`: stable persona key
    - `persona_name`: human-readable name
    - `summary_bio`: short profile summary
  - Example:

```bash
curl -X GET "http://localhost:8000/v1/personas"
```

- `GET /v1/personas/{persona_id}/profile`
  - Path fields:
    - `persona_id`: persona to retrieve
  - Response fields:
    - Full `PersonaProfileModel` payload (`adsp/data_pipeline/schema.py`)
  - Example:

```bash
curl -X GET "http://localhost:8000/v1/personas/curious-connoisseurs/profile"
```

- `GET /v1/personas/{persona_id}/system-prompt`
  - Path fields:
    - `persona_id`: persona to retrieve
  - Response fields:
    - `system_prompt`: generated prompt string used by the orchestrator
  - Example:

```bash
curl -X GET "http://localhost:8000/v1/personas/curious-connoisseurs/system-prompt"
```

### Chat

- `POST /v1/chat`
  - Request fields (`ChatRequest`):
    - `persona_id`: target persona id
    - `query`: user question
    - `session_id`: optional session key
    - `persona_display_name`: optional persona label
    - `attachments`: optional list of attachment objects (`type`, `name`, `mime_type`, `payload`)
    - `top_k`: retrieval depth
    - `use_tools`: enable/disable tool use
  - Response fields (`response: ChatResponse`):
    - `persona_id`: persona used to answer
    - `answer`: generated response text
    - `context`: assembled retrieval context
    - `citations`: evidence list
    - `tool_calls`: tool execution trace
  - Example:

```bash
curl -X POST "http://localhost:8000/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "persona_id":"curious-connoisseurs",
    "query":"What matters most when buying coffee?",
    "top_k":5,
    "use_tools":false
  }'
```

### Ingestion

- `POST /v1/ingestion/upload`
  - Request fields:
    - `filename`: target object key
    - `content_base64`: Base64-encoded file payload
    - `bucket`: optional destination bucket override
  - Response fields:
    - `bucket`: storage bucket used
    - `key`: object key written
    - `size_bytes`: decoded payload size
  - Example:

```bash
curl -X POST "http://localhost:8000/v1/ingestion/upload" \
  -H "Content-Type: application/json" \
  -d '{
    "filename":"notes.txt",
    "content_base64":"SGVsbG8gTGF2YXp6YSBBSSBQZXJzb25hcyE=",
    "bucket":"uploads"
  }'
```

### Reports

- `POST /v1/reports/{persona_id}`
  - Path fields:
    - `persona_id`: persona key used to name output report
  - Request fields:
    - `insights`: free-form insights object rendered to markdown
  - Response fields:
    - `path`: generated report path
  - Example:

```bash
curl -X POST "http://localhost:8000/v1/reports/curious-connoisseurs" \
  -H "Content-Type: application/json" \
  -d '{
    "insights":{
      "top_drivers":["taste","price","brand trust"],
      "summary":"Segment values consistent quality and practical pricing."
    }
  }'
```

### Survey Simulation

- `GET /api/surveys`
  - Query fields:
    - `page`: 1-based page number (default `1`)
    - `page_size`: items per page (default `20`, max `200`)
  - Response fields:
    - `items`: paged survey list (`survey_id`, `title`, `description`, `created_at`, `questions`)
    - `paging`: metadata (`page`, `page_size`, `total_items`, `total_pages`)
  - Example:

```bash
curl -X GET "http://localhost:8000/api/surveys?page=1&page_size=20"
```

- `POST /api/surveys`
  - Request fields:
    - `survey_id`: optional id (auto-generated if omitted)
    - `title`: survey title
    - `description`: survey objective
    - `questions`: question array (`question_id`, `text`, `type`, optional `options`, optional `metadata`)
  - Response fields:
    - `survey_id`, `title`, `description`, `created_at`, `questions`
  - Example:

```bash
curl -X POST "http://localhost:8000/api/surveys" \
  -H "Content-Type: application/json" \
  -d '{
    "survey_id":"coffee-pref-2026-q1",
    "title":"Coffee Preference Survey",
    "description":"Capture coffee purchase preferences.",
    "questions":[
      {
        "question_id":"q1",
        "text":"Which product claim matters most?",
        "type":"multiple_choice",
        "options":["Great taste","Affordable price","Sustainable sourcing"]
      },
      {
        "question_id":"q2",
        "text":"How likely are you to try a new blend?",
        "type":"rating",
        "metadata":{"scale":"1-5"}
      }
    ]
  }'
```

- `GET /api/surveys/{survey_id}`
  - Path fields:
    - `survey_id`: survey identifier
  - Response fields:
    - `survey_id`, `title`, `description`, `created_at`, `questions`
    - `simulations`: all simulation runs for this survey
      - `simulation_id`, `group_id`, `status`, `started_at`, `completed_at`
      - `progress` (`completed`, `pending`)
      - `responses_count`, `responses`, `statistics_ready`
  - Example:

```bash
curl -X GET "http://localhost:8000/api/surveys/coffee-pref-2026-q1"
```

- `POST /api/groups`
  - Request fields:
    - `composition`: list of group parts (`persona_id`, `count`)
    - `mode`: `random` or `llm`
    - `sampling_ratio`: trait sampling ratio
    - `include_names`: generate synthetic names flag
    - `countries`: optional list of allowed countries (for example `["italy","france"]`)
    - `seed`: optional deterministic seed
  - Response fields:
    - `group_id`, `created_at`, `total_respondents`, `composition`, `generation_method`, `sample_profiles`
    - each generated profile includes `name`, `country`, `gender`, and `ethnicity`
  - Example:

```bash
curl -X POST "http://localhost:8000/api/groups" \
  -H "Content-Type: application/json" \
  -d '{
    "composition":[
      {"persona_id":"curious-connoisseurs","count":25},
      {"persona_id":"conscious-explorers","count":15}
    ],
    "mode":"random",
    "sampling_ratio":0.7,
    "include_names":true,
    "countries":["italy","france"],
    "seed":42
  }'
```

- `GET /api/groups/countries`
  - Purpose:
    - Lists every country id supported by `POST /api/groups` in `countries`
  - Response fields:
    - `countries[]`: `country_id`, `display_name`, `description`
  - Example:

```bash
curl -X GET "http://localhost:8000/api/groups/countries"
```

- `GET /api/groups`
  - Query fields:
    - `page`: 1-based page number (default `1`)
    - `page_size`: items per page (default `20`, max `200`)
  - Response fields:
    - `items`: paged group list (`group_id`, `created_at`, `total_respondents`, `composition`, `generation_method`, `sample_profiles`)
    - `paging`: metadata (`page`, `page_size`, `total_items`, `total_pages`)
  - Example:

```bash
curl -X GET "http://localhost:8000/api/groups?page=1&page_size=20"
```

- `GET /api/groups/{group_id}`
  - Path fields:
    - `group_id`: group identifier
  - Query fields:
    - `include_full_profiles`: `true` to include full respondent payloads
  - Response fields:
    - `group_id`, `created_at`, `total_respondents`, `composition`, `generation_method`, `respondents`, `sample_profiles`
  - Example:

```bash
curl -X GET "http://localhost:8000/api/groups/group-ab12cd34?include_full_profiles=false"
```

- `POST /api/surveys/{survey_id}/simulate`
  - Path fields:
    - `survey_id`: target survey id
  - Query fields:
    - `background`: when `true` (default), starts async run and returns immediately
  - Request fields:
    - `group_id`: source respondent group
    - `batch_size`: processing batch size
    - `format`: output format hint
  - Response fields:
    - `simulation_id`, `status`, `total_respondents`, `progress`, `estimated_time_minutes`
    - `status` is `processing` while running and becomes `completed` after finish
  - Example:

```bash
curl -X POST "http://localhost:8000/api/surveys/coffee-pref-2026-q1/simulate?background=true" \
  -H "Content-Type: application/json" \
  -d '{
    "group_id":"group-ab12cd34",
    "batch_size":10,
    "format":"json"
  }'
```

- `GET /api/surveys/{survey_id}/responses`
  - Path fields:
    - `survey_id`: target survey id
  - Query fields:
    - `simulation_id`: optional simulation id (latest when omitted)
    - `format`: `csv` or `json`
  - Response:
    - File download (`text/csv` for `format=csv`, `application/json` for `format=json`)
  - Example:

```bash
curl -L -X GET "http://localhost:8000/api/surveys/coffee-pref-2026-q1/responses?format=csv" -o responses.csv
```

- `GET /api/surveys/{survey_id}/statistics`
  - Path fields:
    - `survey_id`: target survey id
  - Query fields:
    - `simulation_id`: optional simulation id (latest when omitted)
  - Notes:
    - Statistics are computed only for `completed` simulations.
    - The first computation is stored as cache per simulation and reused on subsequent calls.
  - Response fields:
    - `survey_id`, `simulation_id`, `total_respondents`, `total_responses`, `computed_at`, `questions`
    - Per-question fields:
      - `question_id`, `text`, `type`, `answered_count`, `response_rate`
      - `choice_distribution` (`multiple_choice`)
      - `rating_distribution`, `rating_average`, `rating_min`, `rating_max` (`rating`)
      - `text_response_count`, `sample_text_responses` (`open_ended`)
  - Example:

```bash
curl -X GET "http://localhost:8000/api/surveys/coffee-pref-2026-q1/statistics?simulation_id=sim-1234abcd"
```

## How to run locally

```bash
make install
python scripts/run_api.py
```

Then open:
- `http://localhost:8000/docs`

## Configuration

Environment variables (see `.env.example`):

- API:
  - `ADSP_API_HOST` (default `0.0.0.0`)
  - `ADSP_API_PORT` (default `8000`)
  - `ADSP_API_RELOAD` (default `true`)
  - `ADSP_REQUIRE_AUTH` (default `false`)
- Data paths:
  - `ADSP_PERSONAS_DIR`
  - `ADSP_PERSONA_TRAITS_DIR`
- Runtime LLM backend (optional):
  - `ADSP_LLM_BACKEND=stub|openai`
  - `ADSP_LLM_BASE_URL`, `ADSP_LLM_MODEL`, `ADSP_LLM_API_KEY`
