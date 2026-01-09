# Troubleshooting Guide

Common issues and how to fix them.

## Installation Issues

### "ModuleNotFoundError: No module named 'adsp'"

Make sure you installed the package in editable mode:

```bash
pip install -e .
```

### "ImportError: cannot import name 'FastAPI'"

FastAPI is missing. Install it:

```bash
pip install fastapi uvicorn
```

Or just reinstall everything:

```bash
make install
```

## Runtime Issues

### "Port 8000 is already in use"

Another service is using that port. Either:

1. Stop the other service
2. Use a different port:

```bash
ADSP_API_PORT=8080 python scripts/run_api.py
```

### "Connection refused" when calling the API

The server isn't running. Start it first:

```bash
python scripts/run_api.py
```

### Empty responses or "Unauthorized"

Did you register a user first?

```python
import requests

requests.post("http://localhost:8000/v1/auth/register",
              json={"user": "alice", "token": "secret"})
```

Then include auth headers:

```python
headers = {"X-User": "alice", "X-Token": "secret"}
```

## Data Issues

### "No personas found"

The system looks for persona data in `data/processed/personas/`. If that directory is empty, the system will use a default persona.

To add personas, run the data pipeline (see data pipeline docs).

### "Context is always empty"

RAG retrieval needs indexed data. Check:

1. Is the vector DB populated?
2. Is the persona index built?
3. Are you querying the right persona_id?

## Performance Issues

### Slow responses

A few things to check:

1. **Context filtering**: If using `openai` backend for filtering, it adds latency. Switch to `heuristic`:

```bash
export ADSP_CONTEXT_FILTER_BACKEND=heuristic
```

2. **LLM backend**: The stub generator is instant. If you're using a real LLM, response time depends on that service.

3. **Logging**: Debug logging adds overhead. Set log level to INFO:

```bash
export ADSP_API_LOG_LEVEL=info
```

## Testing Issues

### "Tests fail with import errors"

Make sure you're in the project root and the package is installed:

```bash
cd /path/to/2025-P3-AI-Personas
pip install -e .
pytest
```

### "No tests collected"

Pytest looks for files matching `test_*.py`. Make sure your test files follow this naming convention.

## Development Issues

### "Changes aren't reflected"

If running the API server:

1. Stop it (Ctrl+C)
2. Restart it
3. Or use auto-reload:

```bash
python scripts/run_api.py --mode uvicorn --reload
```

### "Git says files are modified but I didn't change them"

Probably line ending issues. The repo uses LF line endings. Check your git config:

```bash
git config core.autocrlf input
```

## Still Having Issues?

1. Check the logs - they usually have helpful error messages
2. Try with a fresh virtual environment
3. Make sure your Python version is 3.10+
4. Open an issue on GitHub with:
   - Your Python version
   - OS and version
   - Full error message
   - Steps to reproduce
