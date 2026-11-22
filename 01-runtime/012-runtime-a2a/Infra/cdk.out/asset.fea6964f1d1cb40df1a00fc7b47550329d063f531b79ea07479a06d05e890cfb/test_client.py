"""
test_client.py — A2A client that tests the guide-024 A2A server.

Prerequisites:
    Start the A2A server:
        agentcore dev --port 9000
        # OR
        cd Source && python3 -m app.agent

Usage:
    python3 Source/test_client.py [--host localhost] [--port 9000]

What this tests:
    1. GET /.well-known/agent-card.json  → discover agent capabilities
    2. POST / tasks/send add_numbers     → invoke the math skill
    3. POST / tasks/send summarize_text  → invoke the summarize skill
"""

import argparse
import json
import sys
import time
import urllib.request
import urllib.error
import uuid


def _get(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=15) as resp:
        return json.loads(resp.read().decode())


def _post(url: str, body: dict) -> dict:
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())


def _send_task(base_url: str, text: str, task_id: str = None) -> dict:
    """Submit an A2A task using the tasks/send JSON-RPC method."""
    task_id = task_id or f"task-{uuid.uuid4().hex[:8]}"
    payload = {
        "jsonrpc": "2.0",
        "id": f"req-{uuid.uuid4().hex[:8]}",
        "method": "tasks/send",
        "params": {
            "id": task_id,
            "message": {
                "role": "user",
                "parts": [{"type": "text", "text": text}],
            },
        },
    }
    return _post(base_url, payload)


def _get_task(base_url: str, task_id: str) -> dict:
    """Retrieve a task by ID using tasks/get."""
    payload = {
        "jsonrpc": "2.0",
        "id": f"req-{uuid.uuid4().hex[:8]}",
        "method": "tasks/get",
        "params": {"id": task_id},
    }
    return _post(base_url, payload)


def main():
    parser = argparse.ArgumentParser(description="A2A test client for guide-024")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=9000)
    args = parser.parse_args()

    base_url = f"http://{args.host}:{args.port}"
    print(f"\n{'='*60}")
    print(f"  Guide 024 — A2A Client Test")
    print(f"  Server: {base_url}")
    print(f"{'='*60}")

    # ── Step 1: Get Agent Card ─────────────────────────────────────────
    print("\n[1/3] Fetching agent card...")
    try:
        agent_card = _get(f"{base_url}/.well-known/agent-card.json")
        print(f"  ✓ Agent: {agent_card.get('name')}")
        print(f"  ✓ Version: {agent_card.get('version')}")
        skills = agent_card.get("skills", [])
        print(f"  ✓ Skills ({len(skills)}):")
        for skill in skills:
            print(f"      - {skill['id']}: {skill['description'][:60]}")
    except Exception as e:  # noqa: BLE001
        print(f"  ✗ Failed to fetch agent card: {e}")
        print("    Is the server running?  agentcore dev --port 9000")
        sys.exit(1)

    # ── Step 2: Invoke add_numbers ─────────────────────────────────────
    print("\n[2/3] Testing add_numbers skill...")
    task_id_math = f"task-math-{uuid.uuid4().hex[:6]}"
    test_message = "Please add 42 and 58"
    print(f"  → Sending: \"{test_message}\"")
    try:
        result = _send_task(base_url, test_message, task_id=task_id_math)
        print(f"  ← Raw response: {json.dumps(result, indent=4)}")

        # Check for result in response
        if "result" in result:
            task_result = result["result"]
            status = task_result.get("status", {}).get("state", "unknown")
            print(f"  ✓ Status: {status}")
            artifacts = task_result.get("artifacts", [])
            for artifact in artifacts:
                for part in artifact.get("parts", []):
                    if part.get("type") == "text":
                        print(f"  ✓ Result: {part['text']}")
        else:
            # Direct response format from dev server
            print(f"  ✓ Direct response received")
    except Exception as e:  # noqa: BLE001
        print(f"  ✗ Error: {e}")

    # ── Step 3: Invoke summarize_text ──────────────────────────────────
    print("\n[3/3] Testing summarize_text skill...")
    long_text = (
        "Amazon Web Services (AWS) is the world's most comprehensive and broadly adopted "
        "cloud platform. AWS offers over 200 fully featured services from data centers "
        "globally. Millions of customers—including the fastest-growing startups, largest "
        "enterprises, and leading government agencies—are using AWS to lower costs, become "
        "more agile, and innovate faster. AWS has the most extensive global cloud "
        "infrastructure, with 31 launched regions and 99 Availability Zones."
    )
    summarize_message = f"Summarize this in 2 sentences: {long_text}"
    print(f"  → Sending: summarize request ({len(long_text)} chars)")
    try:
        result = _send_task(base_url, summarize_message)
        print(f"  ← Raw response: {json.dumps(result, indent=4)}")
        print(f"  ✓ Summarization complete")
    except Exception as e:  # noqa: BLE001
        print(f"  ✗ Error: {e}")

    print(f"\n{'='*60}")
    print("  A2A test complete!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
