# REST API Swagger (OpenAPI)

The REST server is implemented with FastAPI, which generates the Swagger/OpenAPI specification at runtime:

- Swagger UI: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

## Quick export (optional)

Once dependencies are installed, you can export the OpenAPI JSON to a file:

```bash
python -c "from adsp.app.api_server import app; import json; print(json.dumps(app.openapi(), indent=2))" > openapi.json
```

## Contract summary

For the authoritative schema, use `/openapi.json`. The key routes are:

- `GET /health`
- `POST /v1/auth/register`
- `POST /v1/auth/validate`
- `GET /v1/personas`
- `GET /v1/personas/{persona_id}/profile`
- `GET /v1/personas/{persona_id}/system-prompt`
- `POST /v1/chat`
- `POST /v1/ingestion/upload`
- `POST /v1/reports/{persona_id}`

