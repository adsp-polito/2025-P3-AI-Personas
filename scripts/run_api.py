"""Run the REST API server locally.

Usage:
  python scripts/run_api.py

Or directly:
  python -m uvicorn adsp.app.api_server:app --reload --port 8000
"""

from __future__ import annotations

import os


def main() -> None:
    try:
        import uvicorn  # type: ignore
    except ImportError as exc:
        raise SystemExit(
            "uvicorn is required to run the API server. Install deps with `make install`."
        ) from exc

    host = os.environ.get("ADSP_API_HOST", "0.0.0.0")
    port = int(os.environ.get("ADSP_API_PORT", "8000"))
    reload = os.environ.get("ADSP_API_RELOAD", "true").strip().lower() in {"1", "true", "yes", "on"}

    uvicorn.run("adsp.app.api_server:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    main()

