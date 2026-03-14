import os
from pathlib import Path
import sys

from dotenv import load_dotenv
from loguru import logger

# Paths
PROJ_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = PROJ_ROOT / ".env"

# Load environment variables from the repository .env file if it exists.
load_dotenv(ENV_FILE)
# logger.info(f"PROJ_ROOT path is: {PROJ_ROOT}")

DATA_DIR = PROJ_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
INTERIM_DATA_DIR = DATA_DIR / "interim"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
EXTERNAL_DATA_DIR = DATA_DIR / "external"

MODELS_DIR = PROJ_ROOT / "models"

REPORTS_DIR = PROJ_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"


def get_configured_log_level(default: str = "INFO") -> str:
    """Return the configured log level normalized for Loguru/Uvicorn."""

    for env_var in ("ADSP_LOG_LEVEL", "ADSP_API_LOG_LEVEL"):
        raw = os.environ.get(env_var, "").strip()
        if raw:
            return raw.upper()
    return default.upper()

# If tqdm is installed, configure loguru with tqdm.write
# https://github.com/Delgan/loguru/issues/135
logger.remove()

try:
    from tqdm import tqdm

    logger.add(lambda msg: tqdm.write(msg, end=""), colorize=True, level=get_configured_log_level())
except ModuleNotFoundError:
    logger.add(sys.stderr, level=get_configured_log_level())
