#!/usr/bin/env python3
"""
Quick health check script for the API server.

Usage:
    python scripts/check_health.py
    python scripts/check_health.py --url http://localhost:8080
"""

import sys
import argparse
import requests
from urllib.parse import urljoin


def check_health(base_url: str) -> bool:
    """Check if the API server is healthy."""
    try:
        health_url = urljoin(base_url, "/health")
        response = requests.get(health_url, timeout=5)

        if response.status_code == 200:
            data = response.json()
            print(f"✓ Server is healthy")
            print(f"  Status: {data.get('status', 'unknown')}")
            print(f"  Version: {data.get('version', 'unknown')}")
            return True
        else:
            print(f"✗ Server returned status {response.status_code}")
            return False

    except requests.ConnectionError:
        print(f"✗ Cannot connect to {base_url}")
        print(f"  Make sure the server is running:")
        print(f"  python scripts/run_api.py")
        return False
    except requests.Timeout:
        print(f"✗ Request timed out")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Check API server health")
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Base URL of the API server (default: http://localhost:8000)"
    )

    args = parser.parse_args()

    print(f"Checking health of {args.url}...")
    success = check_health(args.url)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
