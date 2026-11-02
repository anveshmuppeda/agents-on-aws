"""
008 — Runtime Sessions & Isolation
====================================

Demonstrates AgentCore Runtime session isolation:

1. Session A and Session B run in separate microVMs
2. Each session has its own conversation context
3. Changes in one session do NOT affect the other
4. Context persists WITHIN a session across multiple calls

The agent remembers things you tell it within a session.
But a completely different session starts fresh.

This is the killer feature of AgentCore Runtime vs Lambda:
  - Lambda: every call is cold, no memory, no isolation
  - AgentCore: every SESSION is isolated, context preserved within session
"""

import logging
from datetime import datetime
from strands import Agent, tool
from bedrock_agentcore import BedrockAgentCoreApp

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Session-aware tools
#
# In a real agent, these tools would access databases, APIs, etc.
# Here we demonstrate stateful behavior within a session.
# ---------------------------------------------------------------------------

# In-memory store within this microVM session
# This persists across multiple calls within the same session.
_session_memory: dict = {}


@tool
def remember(key: str, value: str) -> str:
    """
    Store a key-value pair in the session's memory.

    Args:
        key: What to remember (e.g. "user_name", "preferred_city")
        value: The value to store

    Returns:
        Confirmation message
    """
    _session_memory[key] = value
    logger.info("Stored in session memory: %s = %s", key, value)
    return f"Got it! I'll remember that {key} is '{value}' for this session."


@tool
def recall(key: str) -> str:
    """
    Retrieve a stored value from the session's memory.

    Args:
        key: What to retrieve

    Returns:
        The stored value, or a message saying it's not found
    """
    value = _session_memory.get(key)
    if value is None:
        return f"I don't have anything stored for '{key}' in this session."
    return f"I remember: {key} = '{value}'"


@tool
def show_session_state() -> str:
    """
    Show everything currently stored in this session's memory.

    Returns:
        All key-value pairs stored in this session, plus session start time.
    """
    if not _session_memory:
        return "Session memory is empty — nothing has been remembered yet."
    items = "\n".join(f"  {k}: {v}" for k, v in _session_memory.items())
    return f"Current session memory ({len(_session_memory)} items):\n{items}"


@tool
def get_session_id_from_env() -> str:
    """
    Return the current AgentCore session ID (from environment or context).

    Returns:
        Session ID string
    """
    import os
    # AgentCore Runtime injects session info into the invocation context.
    # For demo purposes we generate a stable ID based on process start.
    pid = os.getpid()
    return f"Session PID: {pid} (each microVM has its own PID space)"


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------


def _strip_thinking(text: str) -> str:
    """Remove <thinking>...</thinking> blocks from model output."""
    import re as _re
    return _re.sub(r'<thinking>.*?</thinking>\s*', '', text, flags=_re.DOTALL).strip()


app = BedrockAgentCoreApp()

# Agent is created once per microVM session — reused across invocations.
# This is different from guide 013 where we created it per call.
# The agent (and _session_memory) persist across multiple calls
# within the same session, then disappear when the session ends.
_agent: Agent | None = None


def get_agent() -> Agent:
    """Return the session-scoped agent, creating it once if needed."""
    global _agent
    if _agent is None:
        _agent = Agent(
            model="us.amazon.nova-pro-v1:0",
            system_prompt=(
                "You are a helpful assistant with session memory. "
                "When the user tells you something, use the 'remember' tool to store it. "
                "When asked about something, use 'recall' to retrieve it. "
                "Always tell the user what session state they have stored when asked. "
                "You exist within an isolated session — your memory is private to this user."
            ),
            tools=[remember, recall, show_session_state, get_session_id_from_env],
        )
    return _agent


@app.entrypoint
def invoke(payload: dict) -> dict:
    prompt = payload.get("prompt", "").strip()
    if not prompt:
        return {"error": "Missing 'prompt'"}

    agent = get_agent()
    response = agent(prompt)
    return {
        "response": _strip_thinking(str(response)),
        "session_memory_size": len(_session_memory),
        "turn": len(_session_memory),
    }


if __name__ == "__main__":
    app.run()
