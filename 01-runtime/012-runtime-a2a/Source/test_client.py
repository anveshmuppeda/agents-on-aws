"""Exercise Agent Card discovery and A2A 0.3 message/send over HTTP."""

import argparse
import json
import uuid
from urllib.request import Request, urlopen


def _get(url: str) -> dict:
    with urlopen(url, timeout=15) as response:
        return json.loads(response.read().decode())


def _send_message(base_url: str, text: str) -> dict:
    request_id = f"req-{uuid.uuid4().hex}"
    payload = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": "message/send",
        "params": {
            "message": {
                "kind": "message",
                "messageId": f"msg-{uuid.uuid4().hex}",
                "role": "user",
                "parts": [{"kind": "text", "text": text}],
            },
        },
    }
    request = Request(
        base_url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=120) as response:
        result = json.loads(response.read().decode())

    if "error" in result:
        raise RuntimeError(f"A2A request failed: {result['error']}")
    task = result.get("result")
    if not task:
        raise RuntimeError(f"A2A response did not contain a task: {result}")
    if task.get("status", {}).get("state") != "completed":
        raise RuntimeError(f"A2A task did not complete: {task}")
    return task


def _artifact_text(task: dict) -> str:
    texts = [
        part["text"]
        for artifact in task.get("artifacts", [])
        for part in artifact.get("parts", [])
        if part.get("kind") == "text" and part.get("text")
    ]
    if not texts:
        raise RuntimeError(f"A2A task completed without a text artifact: {task}")
    return "\n".join(texts)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=9000)
    args = parser.parse_args()

    base_url = f"http://{args.host}:{args.port}"
    print(f"Server: {base_url}")

    print("\n[1/3] Discovering agent capabilities...")
    card = _get(f"{base_url}/.well-known/agent-card.json")
    skill_ids = {skill["id"] for skill in card.get("skills", [])}
    expected_skills = {"add_numbers", "summarize_text"}
    if not expected_skills.issubset(skill_ids):
        raise RuntimeError(f"Agent Card is missing skills: {expected_skills - skill_ids}")
    print(f"  Agent: {card['name']}")
    print(f"  Skills: {', '.join(sorted(skill_ids))}")

    print("\n[2/3] Sending an A2A math message...")
    task = _send_message(base_url, "Please add 42 and 58")
    print(f"  Result: {_artifact_text(task)}")

    print("\n[3/3] Sending an A2A summarization message...")
    text = (
        "Amazon Web Services offers cloud services around the world. "
        "Customers use AWS to lower costs, become more agile, and innovate faster."
    )
    task = _send_message(base_url, f"Summarize this in one sentence: {text}")
    print(f"  Result: {_artifact_text(task)}")

    print("\nA2A discovery and task requests passed.")


if __name__ == "__main__":
    main()
