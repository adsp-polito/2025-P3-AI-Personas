"""
Example demonstrating how to interact with the REST API.

Make sure the API server is running first:
    python scripts/run_api.py
"""

import requests
import time


def main():
    base_url = "http://localhost:8000"

    print("=== API Usage Example ===\n")

    # Check health
    print("1. Checking server health...")
    resp = requests.get(f"{base_url}/health")
    print(f"   Status: {resp.json()['status']}\n")

    # Register user
    print("2. Registering user...")
    username = f"demo_user_{int(time.time())}"
    token = "demo_token_123"

    resp = requests.post(
        f"{base_url}/v1/auth/register",
        json={"user": username, "token": token}
    )
    print(f"   Registration: {resp.status_code == 200}\n")

    # Setup headers
    headers = {
        "X-User": username,
        "X-Token": token
    }

    # List personas
    print("3. Listing available personas...")
    resp = requests.get(f"{base_url}/v1/personas", headers=headers)
    personas = resp.json()["personas"]
    print(f"   Found {len(personas)} personas")

    if personas:
        print(f"   First persona: {personas[0]['persona_id']}\n")
        persona_id = personas[0]['persona_id']
    else:
        persona_id = "default"
        print(f"   Using default persona\n")

    # Send chat message
    print("4. Sending chat message...")
    resp = requests.post(
        f"{base_url}/v1/chat",
        headers=headers,
        json={
            "persona_id": persona_id,
            "query": "What's your recommendation for a morning coffee?",
            "top_k": 5
        }
    )

    if resp.status_code == 200:
        data = resp.json()["response"]
        print(f"   Answer: {data['answer'][:100]}...")
        print(f"   Citations: {len(data['citations'])}\n")
    else:
        print(f"   Error: {resp.status_code}\n")

    print("=== Done ===")


if __name__ == "__main__":
    main()
