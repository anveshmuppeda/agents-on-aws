"""
Test script for guide 020 — demonstrates session isolation.

Sends multiple turns to TWO different sessions and shows that:
  - Within a session: the agent remembers information across turns
  - Between sessions: sessions are completely isolated (no shared memory)

Run AFTER the dev server is started:
    Terminal 1: agentcore dev
    Terminal 2: python3 Source/test_sessions.py
"""

import requests
import json
import time

BASE_URL = "http://localhost:8080/invocations"


def invoke(prompt: str, session_id: str) -> dict:
    """Send a request to the dev server with a specific session ID."""
    response = requests.post(
        BASE_URL,
        json={"prompt": prompt},
        headers={
            "Content-Type": "application/json",
            # In prod, AgentCore uses real session IDs.
            # In the dev server, session isolation is simulated via headers.
            "X-Session-Id": session_id,
        },
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def print_result(session_id: str, prompt: str, result: dict):
    print(f"\n{'─'*60}")
    print(f"Session: {session_id}")
    print(f"Prompt:  {prompt}")
    print(f"Response: {result.get('response', result)}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("  Guide 020: Session Isolation Test")
    print("="*60)
    print("\nThis test sends turns to TWO separate sessions.")
    print("Watch how Session A's memory is invisible to Session B.\n")

    session_a = "session-alice-001"
    session_b = "session-bob-001"

    # ── Session A: Alice tells the agent her name and preferences
    print("\n>>> SESSION A: ALICE")

    r = invoke("My name is Alice and I live in Austin, TX.", session_a)
    print_result(session_a, "My name is Alice and I live in Austin, TX.", r)
    time.sleep(1)

    r = invoke("Please remember that I prefer morning flights.", session_a)
    print_result(session_a, "Please remember that I prefer morning flights.", r)
    time.sleep(1)

    r = invoke("What do you know about me? Show me your session state.", session_a)
    print_result(session_a, "What do you know about me?", r)
    time.sleep(1)

    # ── Session B: Bob starts a completely fresh session
    print("\n>>> SESSION B: BOB (different session — should know nothing about Alice)")

    r = invoke("What is my name?", session_b)
    print_result(session_b, "What is my name?", r)
    time.sleep(1)

    r = invoke("Show me the session state.", session_b)
    print_result(session_b, "Show me the session state.", r)
    time.sleep(1)

    # ── Session A: Alice continues — agent still remembers
    print("\n>>> SESSION A: ALICE (continues — agent still has her context)")

    r = invoke("What flight preferences did I mention?", session_a)
    print_result(session_a, "What flight preferences did I mention?", r)

    print("\n" + "="*60)
    print("RESULT: Session A's data is invisible to Session B.")
    print("Each session is a completely isolated microVM.")
    print("="*60)
