"""Launch the Streamlit frontend for Lavazza AI Personas."""

import os
import sys
import subprocess

from adsp.config import PROJ_ROOT


def main():
    """Launch the Streamlit application."""
    app_path = PROJ_ROOT / "adsp" / "fe" / "app.py"
    frontend_port = os.environ.get("ADSP_FE_PORT", "8501").strip() or "8501"

    if not app_path.exists():
        print(f"Error: Frontend app not found at {app_path}")
        sys.exit(1)

    print("Starting Lavazza AI Personas Frontend...")
    print(f"Open Frontend at http://localhost:{frontend_port}")

    # Launch Streamlit
    subprocess.run(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(app_path),
            "--server.headless=true",
            f"--server.port={frontend_port}",
        ],
        cwd=PROJ_ROOT,
    )


if __name__ == "__main__":
    main()
