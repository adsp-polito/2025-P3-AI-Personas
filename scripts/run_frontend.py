"""Launch the Streamlit frontend for Lavazza AI Personas."""

import sys
import subprocess

from adsp.config import PROJ_ROOT

def main():
    """Launch the Streamlit application."""
    app_path = PROJ_ROOT / "adsp" / "fe" / "app.py"
    
    if not app_path.exists():
        print(f"Error: Frontend app not found at {app_path}")
        sys.exit(1)
    
    print("Starting Lavazza AI Personas Frontend...")
    print("Open Frontend")
    
    # Launch Streamlit
    subprocess.run([
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_path),
        "--server.headless=true",
    ])

if __name__ == "__main__":
    main()