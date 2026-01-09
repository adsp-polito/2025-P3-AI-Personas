# REST API Guide

Complete reference for the FastAPI endpoints.

## Starting the Server

```bash
python scripts/run_api.py
```

Access the interactive docs at http://localhost:8000/docs

## Authentication

Most endpoints require authentication headers:

```
X-User: your-username
X-Token: your-token
```

First register a user, then include these headers in subsequent requests.

## Endpoints

### Health Check

```http
GET /health
```

Returns server status. No auth required.

**Response:**
```json
{
  "status": "ok",
  "version": "0.1.0"
}
```

### Register User

```http
POST /v1/auth/register
```

**Body:**
```json
{
  "user": "alice",
  "token": "secret123"
}
```

**Response:** 200 OK

### Validate Credentials

```http
POST /v1/auth/validate
```

**Body:**
```json
{
  "user": "alice",
  "token": "secret123"
}
```

**Response:**
```json
{
  "authorized": true
}
```

### List Personas

```http
GET /v1/personas
```

Returns all available personas.

**Response:**
```json
{
  "personas": [
    {
      "persona_id": "basic-traditional",
      "persona_name": "Traditional Coffee Drinker",
      "summary_bio": "Values classic coffee experiences..."
    }
  ]
}
```

### Get Persona Profile

```http
GET /v1/personas/{persona_id}/profile
```

**Response:**
```json
{
  "persona_id": "basic-traditional",
  "persona_name": "Traditional Coffee Drinker",
  "summary_bio": "...",
  "demographics": {...},
  "preferences": {...}
}
```

### Get System Prompt

```http
GET /v1/personas/{persona_id}/system-prompt
```

Returns the system prompt used for this persona.

**Response:**
```json
{
  "system_prompt": "You are a helpful assistant representing..."
}
```

### Send Chat Message

```http
POST /v1/chat
```

**Body:**
```json
{
  "persona_id": "basic-traditional",
  "query": "What coffee do you recommend?",
  "session_id": "optional-session-id",
  "top_k": 5
}
```

**Response:**
```json
{
  "response": {
    "persona_id": "basic-traditional",
    "answer": "I'd recommend...",
    "context": "Retrieved context...",
    "citations": [
      {
        "indicator_id": "coffee_preference",
        "score": 0.95
      }
    ]
  }
}
```

### Upload File

```http
POST /v1/ingestion/upload
```

**Body:**
```json
{
  "filename": "document.pdf",
  "content_base64": "base64_encoded_content",
  "bucket": "optional-bucket-name"
}
```

**Response:**
```json
{
  "bucket": "default",
  "key": "document.pdf",
  "size_bytes": 12345
}
```

### Generate Report

```http
POST /v1/reports/{persona_id}
```

**Body:**
```json
{
  "insights": {
    "key": "value"
  }
}
```

**Response:**
```json
{
  "path": "reports/persona_report.pdf"
}
```

## Error Responses

All endpoints return standard HTTP status codes:

- `200` - Success
- `400` - Bad request (invalid input)
- `401` - Unauthorized
- `404` - Resource not found
- `500` - Server error

Error body format:
```json
{
  "detail": "Error message"
}
```

## Rate Limiting

Currently no rate limiting is enforced. In production, consider adding rate limits per user.

## Examples

### Python

```python
import requests

# Register
requests.post("http://localhost:8000/v1/auth/register",
              json={"user": "alice", "token": "secret"})

# Chat
headers = {"X-User": "alice", "X-Token": "secret"}
response = requests.post(
    "http://localhost:8000/v1/chat",
    headers=headers,
    json={"persona_id": "basic-traditional", "query": "hello"}
)
print(response.json())
```

### cURL

```bash
# Register
curl -X POST http://localhost:8000/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"user":"alice","token":"secret"}'

# Chat
curl -X POST http://localhost:8000/v1/chat \
  -H "X-User: alice" \
  -H "X-Token: secret" \
  -H "Content-Type: application/json" \
  -d '{"persona_id":"basic-traditional","query":"hello"}'
```
