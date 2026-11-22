"""
012 — AgentCore Runtime: Agent-to-Agent (A2A) Server
======================================================

Deploys a Google A2A-protocol-compliant server to AgentCore Runtime.
Other agents discover this agent's capabilities via the agent card endpoint
and invoke it as a remote tool using JSON-RPC 2.0.

Tools exposed as A2A skills:
  - add_numbers(a, b) → arithmetic sum
  - summarize_text(text, max_sentences) → LLM-generated summary

Port: 9000 (A2A convention — distinct from AgentCore's 8080)

Local testing:
    agentcore dev --port 9000
    curl http://localhost:9000/.well-known/agent-card.json
    python3 Source/test_client.py
"""

import json
import logging
import os
from typing import Any

from strands import Agent, tool
from strands.models import BedrockModel
from bedrock_agentcore.runtime import BedrockAgentCoreApp

logger = logging.getLogger(__name__)

MODEL_ID = os.environ.get("MODEL_ID", "us.amazon.nova-pro-v1:0")
REGION = os.environ.get("AWS_DEFAULT_REGION", os.environ.get("AWS_REGION", "us-east-1"))
PORT = int(os.environ.get("PORT", "9000"))

# ---------------------------------------------------------------------------
# Tools (become A2A "skills")
# ---------------------------------------------------------------------------


@tool
def add_numbers(a: float, b: float) -> str:
    """
    Add two numbers and return the result.

    Args:
        a: First number
        b: Second number

    Returns:
        A string describing the result, e.g. "3.5 + 2.1 = 5.6"
    """
    result = a + b
    return f"{a} + {b} = {result}"


@tool
def summarize_text(text: str, max_sentences: int = 3) -> str:
    """
    Summarize a piece of text into a concise summary.

    Args:
        text: The text to summarize (any length)
        max_sentences: Maximum number of sentences in the summary (default: 3)

    Returns:
        A concise summary of the input text.
    """
    if not text.strip():
        return "No text provided to summarize."

    # Use the LLM to generate the summary
    summary_agent = Agent(
        model=BedrockModel(model_id=MODEL_ID, region_name=REGION),
        system_prompt=(
            "You are a precise text summarizer. "
            "Summarize the given text concisely. "
            "Do not add any preamble like 'Here is a summary:'. "
            "Just output the summary directly."
        ),
    )

    prompt = (
        f"Summarize the following text in at most {max_sentences} sentences:\n\n"
        f"{text}"
    )
    result = summary_agent(prompt)
    return str(result).strip()


# ---------------------------------------------------------------------------
# A2A Server definition
# ---------------------------------------------------------------------------

AGENT_CARD = {
    "name": "guide-024-a2a-server",
    "description": "A2A-protocol agent with arithmetic and text summarization capabilities.",
    "version": "1.0.0",
    "url": f"http://localhost:{PORT}",
    "capabilities": {
        "streaming": False,
        "pushNotifications": False,
        "stateTransitionHistory": True,
    },
    "skills": [
        {
            "id": "add_numbers",
            "name": "Add Numbers",
            "description": "Adds two numbers (floats) and returns the arithmetic sum.",
            "inputModes": ["text"],
            "outputModes": ["text"],
            "examples": ["Add 42 and 58", "What is 3.14 + 2.72?"],
            "tags": ["math", "arithmetic"],
        },
        {
            "id": "summarize_text",
            "name": "Summarize Text",
            "description": "Summarizes a piece of text using an LLM. Supports configurable sentence count.",
            "inputModes": ["text"],
            "outputModes": ["text"],
            "examples": [
                "Summarize: The quick brown fox...",
                "Summarize this article in 2 sentences: ...",
            ],
            "tags": ["text", "nlp", "summarization"],
        },
    ],
    "defaultInputModes": ["text"],
    "defaultOutputModes": ["text"],
}


# ---------------------------------------------------------------------------
# Strands agent — handles the natural language task dispatch
# ---------------------------------------------------------------------------

def _build_agent() -> Agent:
    return Agent(
        model=BedrockModel(model_id=MODEL_ID, region_name=REGION),
        system_prompt=(
            "You are a helpful A2A agent. You have two tools:\n"
            "1. add_numbers(a, b) — adds two numbers\n"
            "2. summarize_text(text, max_sentences) — summarizes text\n\n"
            "Use these tools to answer user requests. "
            "Always invoke the appropriate tool when the user asks."
        ),
        tools=[add_numbers, summarize_text],
    )


# ---------------------------------------------------------------------------
# AgentCore A2A App
#
# BedrockAgentCoreApp with A2A mode exposes:
#   GET  /.well-known/agent-card.json  → returns AGENT_CARD
#   POST /                             → handles A2A JSON-RPC requests
#
# The @app.entrypoint processes the task message and returns the result.
# ---------------------------------------------------------------------------

app = BedrockAgentCoreApp()  # agent_card and port removed in bedrock-agentcore 1.25+


@app.entrypoint
def invoke(payload: dict) -> dict:
    """
    A2A task handler.

    The payload conforms to A2A JSON-RPC "tasks/send":
        {
            "jsonrpc": "2.0",
            "id": "req-1",
            "method": "tasks/send",
            "params": {
                "id": "task-abc",
                "message": {
                    "role": "user",
                    "parts": [{"type": "text", "text": "Add 42 and 58"}]
                }
            }
        }

    Returns A2A Task object with status and result.
    """
    # Extract the user message from the A2A payload
    params = payload.get("params", payload)
    message = params.get("message", {})
    parts = message.get("parts", [])

    # Collect all text parts
    user_text = " ".join(
        p.get("text", "") for p in parts if p.get("type") == "text"
    ).strip()

    if not user_text:
        # Fallback: try direct prompt field (for dev/test convenience)
        user_text = payload.get("prompt", "").strip()

    if not user_text:
        return {
            "status": {"state": "failed"},
            "error": {"code": -32600, "message": "No text found in message parts"},
        }

    logger.info("[024-a2a] task text=%s", user_text[:120])

    agent = _build_agent()
    response = agent(user_text)
    response_text = str(response).strip()

    # Return A2A Task result format
    return {
        "status": {"state": "completed"},
        "artifacts": [
            {
                "name": "result",
                "parts": [{"type": "text", "text": response_text}],
            }
        ],
    }


# ---------------------------------------------------------------------------
# Local entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run()
