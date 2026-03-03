"""Run the REST API server locally.

Usage:
  python scripts/run_api.py                  # uvicorn runner (default)
  python scripts/run_api.py --mode direct    # direct import (better for debugging)
  python scripts/run_api.py --debug          # FastAPI debug mode

Or directly:
  python -m uvicorn adsp.app.api_server:app --reload --port 8000
"""

from __future__ import annotations

import argparse
import os

from adsp.config import get_configured_log_level


def _env_flag(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_positive_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise SystemExit(f"{name} must be an integer >= 1.") from exc
    if value < 1:
        raise SystemExit(f"{name} must be an integer >= 1.")
    return value


def _normalize_uvicorn_log_level(raw: str) -> str:
    normalized = raw.strip().lower()
    valid_levels = {"critical", "error", "warning", "info", "debug", "trace"}
    if normalized in valid_levels:
        return normalized
    raise SystemExit(
        "Invalid log level. Use one of: CRITICAL, ERROR, WARNING, INFO, DEBUG, TRACE."
    )


def _resolve_worker_count(*, mode: str, reload_enabled: bool, workers: int) -> int:
    if workers < 1:
        raise SystemExit("ADSP_API_WORKERS must be an integer >= 1.")
    if mode == "direct" and workers != 1:
        print("Note: --workers is not supported in --mode direct; running with workers=1.")
        return 1
    if reload_enabled and workers != 1:
        print("Note: --workers > 1 is not supported with --reload; running with workers=1.")
        return 1
    return workers


def main() -> None:
    try:
        import uvicorn  # type: ignore
    except ImportError as exc:
        raise SystemExit(
            "uvicorn is required to run the API server. Install deps with `make install`."
        ) from exc

    parser = argparse.ArgumentParser(description="Run the Lavazza AI Personas REST API.")
    parser.add_argument(
        "--mode",
        choices=("uvicorn", "direct"),
        default=os.environ.get("ADSP_API_RUN_MODE", "uvicorn").strip().lower(),
        help="Runner mode: 'uvicorn' (import string) or 'direct' (import & run app instance).",
    )
    parser.add_argument("--host", default=os.environ.get("ADSP_API_HOST", "0.0.0.0"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("ADSP_API_PORT", "8000")))
    parser.add_argument(
        "--reload",
        action=argparse.BooleanOptionalAction,
        default=_env_flag("ADSP_API_RELOAD", True),
        help="Auto-reload on code changes (only supported in --mode uvicorn).",
    )
    parser.add_argument(
        "--debug",
        action=argparse.BooleanOptionalAction,
        default=_env_flag("ADSP_API_DEBUG", False),
        help="Enable FastAPI debug mode (tracebacks in responses).",
    )
    parser.add_argument("--log-level", default=get_configured_log_level())
    parser.add_argument(
        "--workers",
        type=int,
        default=_env_positive_int("ADSP_API_WORKERS", 1),
        help="Number of Uvicorn worker processes (uvicorn mode only; requires --no-reload).",
    )
    args = parser.parse_args()
    args.log_level = _normalize_uvicorn_log_level(args.log_level)
    args.workers = _resolve_worker_count(
        mode=args.mode,
        reload_enabled=args.reload,
        workers=args.workers,
    )

    os.environ["ADSP_API_DEBUG"] = "true" if args.debug else "false"

    if args.mode == "direct":
        if args.reload:
            print("Note: --reload is not supported in --mode direct; running without reload.")
        from adsp.app.api_server import create_app

        uvicorn.run(create_app(), host=args.host, port=args.port, reload=False, log_level=args.log_level)
        return

    uvicorn.run(
        "adsp.app.api_server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers,
        log_level=args.log_level,
    )


if __name__ == "__main__":
    main()
