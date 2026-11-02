"""
test_models.py — compare 3 Bedrock models against the local dev server.

Prerequisites:
    Start the dev server:
        agentcore dev --port 8080          (default Nova Pro)

    Or start with a specific model:
        MODEL_ID=us.anthropic.claude-3-5-sonnet-20241022-v2:0 agentcore dev --port 8080

Usage:
    python3 Source/test_models.py

The script starts the server ONCE per model and runs the same test prompt,
then prints a side-by-side comparison table.

Note: Because the dev server picks up MODEL_ID at start time, this script
forks a subprocess for each model so it can inject a different MODEL_ID.
Each server binds to a unique port (8081, 8082, 8083) to avoid conflicts.
"""

import json
import os
import subprocess
import sys
import time
import textwrap
import urllib.request
import urllib.error

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ------------------------------------------------------------------
# Models to compare
# ------------------------------------------------------------------
MODELS = [
    {
        "name": "Amazon Nova Pro",
        "model_id": "us.amazon.nova-pro-v1:0",
        "port": 8081,
    },
    {
        "name": "Amazon Nova Lite",
        "model_id": "us.amazon.nova-lite-v1:0",
        "port": 8082,
    },
    {
        "name": "Amazon Nova Micro",
        "model_id": "us.amazon.nova-micro-v1:0",
        "port": 8083,
    },
]

TEST_PROMPTS = [
    "What is the weather in London right now?",
    "Compare the weather in Austin and Seattle.",
]

SERVER_STARTUP_SECONDS = 5
INVOKE_TIMEOUT_SECONDS = 60


def _wait_for_server(port: int, retries: int = 20) -> bool:
    """Poll until the server is accepting connections."""
    for _ in range(retries):
        try:
            urllib.request.urlopen(
                f"http://localhost:{port}/health",
                timeout=2,
            )
            return True
        except Exception:  # noqa: BLE001
            pass
        try:
            req = urllib.request.Request(
                f"http://localhost:{port}/invocations",
                data=b"{}",
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urllib.request.urlopen(req, timeout=2)
            return True
        except urllib.error.HTTPError:
            # Any HTTP error means the server IS up
            return True
        except Exception:  # noqa: BLE001
            time.sleep(0.5)
    return False


def _invoke(port: int, prompt: str) -> dict:
    """Send a prompt to the local dev server and return the parsed response."""
    payload = json.dumps({"prompt": prompt}).encode()
    req = urllib.request.Request(
        f"http://localhost:{port}/invocations",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=INVOKE_TIMEOUT_SECONDS) as resp:
        return json.loads(resp.read().decode())


def _run_model(model: dict, prompts: list[str]) -> list[dict]:
    """Start a dev server for the given model, run prompts, return results."""
    model_id = model["model_id"]
    port = model["port"]
    name = model["name"]

    print(f"\n{'─'*60}")
    print(f"  Starting {name} ({model_id}) on port {port}...")
    print(f"{'─'*60}")

    env = os.environ.copy()
    env["MODEL_ID"] = model_id
    env["AWS_DEFAULT_REGION"] = env.get("AWS_DEFAULT_REGION", "us-east-1")

    # Start the agent server as a subprocess
    proc = subprocess.Popen(
        [sys.executable, "-m", "app.agent"],
        cwd=BASE_DIR,
        env={**env, "PORT": str(port)},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        time.sleep(SERVER_STARTUP_SECONDS)
        if not _wait_for_server(port):
            print(f"  ⚠  Server for {name} did not start in time.")
            return [{"model": name, "prompt": p, "response": "SERVER_TIMEOUT", "model_id": model_id} for p in prompts]

        results = []
        for prompt in prompts:
            print(f"\n  → Prompt: {prompt}")
            try:
                t0 = time.monotonic()
                data = _invoke(port, prompt)
                elapsed = time.monotonic() - t0
                resp_text = data.get("response", str(data))
                print(f"  ✓ Response ({elapsed:.1f}s): {resp_text[:120]}...")
                results.append({
                    "model": name,
                    "model_id": model_id,
                    "prompt": prompt,
                    "response": resp_text,
                    "latency_s": round(elapsed, 2),
                })
            except Exception as e:  # noqa: BLE001
                print(f"  ✗ Error: {e}")
                results.append({
                    "model": name,
                    "model_id": model_id,
                    "prompt": prompt,
                    "response": f"ERROR: {e}",
                    "latency_s": -1,
                })

        return results
    finally:
        proc.terminate()
        proc.wait(timeout=5)


def _print_comparison_table(all_results: list[dict], prompts: list[str]) -> None:
    """Print a side-by-side comparison table."""
    print("\n\n" + "═" * 80)
    print("  MODEL COMPARISON RESULTS")
    print("═" * 80)

    for prompt in prompts:
        print(f"\nPrompt: \"{prompt}\"")
        print("─" * 80)

        prompt_results = [r for r in all_results if r["prompt"] == prompt]
        for r in prompt_results:
            wrapped = textwrap.fill(r["response"], width=70, initial_indent="  ", subsequent_indent="  ")
            latency = f"{r['latency_s']}s" if r["latency_s"] >= 0 else "N/A"
            print(f"\n  [{r['model']}] (latency: {latency})")
            print(f"  Model ID: {r['model_id']}")
            print(wrapped)

        print()

    # Summary table
    print("\n" + "═" * 80)
    print("  LATENCY SUMMARY (seconds)")
    print("─" * 80)
    print(f"  {'Model':<30} {'Prompt 1':>12} {'Prompt 2':>12}")
    print("─" * 80)

    model_names = list({r["model"] for r in all_results})
    for name in model_names:
        rows = [r for r in all_results if r["model"] == name]
        latencies = [str(r.get("latency_s", "N/A")) for r in rows]
        row = f"  {name:<30}"
        for lat in latencies[:2]:
            row += f" {lat:>12}"
        print(row)

    print("═" * 80)


def main():
    print("=" * 60)
    print("  Guide 022 — Model Comparison Test")
    print("  Running same agent against 3 Bedrock models")
    print("=" * 60)

    # Check AWS credentials
    if not os.environ.get("AWS_ACCESS_KEY_ID") and not os.environ.get("AWS_PROFILE"):
        print(
            "\n⚠  No AWS credentials detected. "
            "Set AWS_ACCESS_KEY_ID/SECRET/TOKEN or AWS_PROFILE before running.\n"
        )

    all_results = []

    for model in MODELS:
        results = _run_model(model, TEST_PROMPTS)
        all_results.extend(results)

    _print_comparison_table(all_results, TEST_PROMPTS)

    # Save JSON results
    output_file = os.path.join(BASE_DIR, "..", "model_comparison_results.json")
    with open(output_file, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nFull results saved to: {os.path.abspath(output_file)}")


if __name__ == "__main__":
    main()
