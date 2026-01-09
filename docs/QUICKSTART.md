# Quick Start Guide

Get the AI Personas system running locally in a few minutes.

## Prerequisites

- Python 3.10+
- pip or make

## Installation

Clone the repo and install dependencies:

```bash
git clone <repository-url>
cd 2025-P3-AI-Personas
make install
```

Or manually:

```bash
pip install -r requirements.txt
pip install -e .
```

## Run the Chat CLI

List available personas:

```bash
python scripts/run_chat.py list-personas
```

Start chatting with a persona:

```bash
python scripts/run_chat.py chat --persona-id basic-traditional
```

## Run the REST API

Start the FastAPI server:

```bash
python scripts/run_api.py
```

Then open your browser:
- Swagger docs: http://localhost:8000/docs
- API health: http://localhost:8000/health

## Optional: Use a Real LLM

By default the system uses a stub generator. To connect to an actual LLM backend (like vLLM):

```bash
export ADSP_LLM_BACKEND=openai
export ADSP_LLM_BASE_URL=http://localhost:8000/v1
export ADSP_LLM_MODEL=your-model-name
export ADSP_LLM_API_KEY=EMPTY

python scripts/run_chat.py chat --persona-id basic-traditional
```

## What's Next?

- Check out the [API Guide](API_GUIDE.md) for endpoint documentation
- Read [ARCHITECTURE.md](ARCHITECTURE.md) to understand the system design
- See [CONTRIBUTING.md](../README.md#how-to-contribute) for development guidelines

## Troubleshooting

**Import errors?** Make sure you ran `pip install -e .`

**Port already in use?** Change the port with `ADSP_API_PORT=8080 python scripts/run_api.py`

**Can't find personas?** The system looks for persona data in `data/processed/personas/`
