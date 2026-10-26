"""
006 — Agent on AgentCore Runtime
==================================

Same travel agent as guide 003/005, but deployed to AgentCore Runtime.

The key difference from Lambda (005):
  - Wrapped with BedrockAgentCoreApp + @app.entrypoint
  - Sessions are isolated microVMs (true session isolation)
  - State persists across multiple calls within a session
  - No 15-min timeout limit
  - Starts from a snapshot for fast cold starts (V2)

Local testing:
    python3 Source/app/agent.py        → starts uvicorn on :8080
    agentcore dev                       → same, via AgentCore CLI dev server

Invoke locally:
    agentcore invoke --dev '{"prompt": "What time is it in Tokyo?"}'
    curl -X POST http://localhost:8080/invocations \
         -H "Content-Type: application/json" \
         -d '{"prompt": "What time is it in Tokyo?"}'
"""

import logging
from strands import Agent, tool
from bedrock_agentcore import BedrockAgentCoreApp

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

MOCK_WEATHER = {
    "austin":     {"temp": "92°F / 33°C",  "condition": "Sunny",         "humidity": "45%"},
    "new york":   {"temp": "75°F / 24°C",  "condition": "Partly Cloudy", "humidity": "60%"},
    "seattle":    {"temp": "58°F / 14°C",  "condition": "Overcast",      "humidity": "78%"},
    "london":     {"temp": "61°F / 16°C",  "condition": "Light Rain",    "humidity": "82%"},
    "tokyo":      {"temp": "79°F / 26°C",  "condition": "Clear",         "humidity": "55%"},
    "sydney":     {"temp": "68°F / 20°C",  "condition": "Sunny",         "humidity": "50%"},
    "paris":      {"temp": "64°F / 18°C",  "condition": "Cloudy",        "humidity": "70%"},
}


@tool
def get_weather(location: str) -> str:
    """Get the current weather for a city or location."""
    key = location.lower().split(",")[0].strip()
    weather = MOCK_WEATHER.get(key)
    if weather is None:
        return f"Weather data not available for '{location}'."
    return (
        f"Current weather in {location}:\n"
        f"  Temperature: {weather['temp']}\n"
        f"  Condition:   {weather['condition']}\n"
        f"  Humidity:    {weather['humidity']}"
    )


@tool
def get_current_time(timezone: str) -> str:
    """Get the current date and time in a given timezone or city."""
    import datetime
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

    aliases = {
        "london": "Europe/London", "tokyo": "Asia/Tokyo",
        "paris": "Europe/Paris", "sydney": "Australia/Sydney",
        "seattle": "America/Los_Angeles", "new york": "America/New_York",
        "austin": "America/Chicago", "utc": "UTC",
        "pst": "America/Los_Angeles", "est": "America/New_York",
    }
    tz_name = aliases.get(timezone.lower().strip(), timezone)
    try:
        tz = ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        return f"Unknown timezone '{timezone}'."
    now = datetime.datetime.now(tz)
    return (
        f"Current time in {timezone} ({tz_name}):\n"
        f"  Date: {now.strftime('%A, %B %d, %Y')}\n"
        f"  Time: {now.strftime('%I:%M %p')}"
    )


# ---------------------------------------------------------------------------
# AgentCore App — the key difference from Lambda
#
# BedrockAgentCoreApp wraps your agent for AgentCore Runtime hosting.
# @app.entrypoint marks the function AgentCore calls on each invocation.
#
# The function receives a payload dict and returns a dict.
# It runs inside an isolated microVM — one microVM per session.
# ---------------------------------------------------------------------------


def _strip_thinking(text: str) -> str:
    """Remove <thinking>...</thinking> blocks from model output."""
    import re as _re
    return _re.sub(r'<thinking>.*?</thinking>\s*', '', text, flags=_re.DOTALL).strip()


app = BedrockAgentCoreApp()


@app.entrypoint
def invoke(payload: dict) -> dict:
    """
    AgentCore Runtime entrypoint.

    Called by AgentCore on each invocation within a session.
    The same agent instance handles all turns within a session.

    Args:
        payload: Dict with at minimum {"prompt": "user's question"}

    Returns:
        Dict with {"response": "agent's answer"}
    """
    prompt = payload.get("prompt", "").strip()
    if not prompt:
        return {"error": "Missing 'prompt' in payload"}

    logger.info("Received prompt: %s", prompt)

    # Create agent — in Runtime, this runs inside the session's microVM.
    # Unlike Lambda, you can also move agent creation OUTSIDE entrypoint
    # to reuse it across calls within the same session.
    agent = Agent(
        model="us.amazon.nova-pro-v1:0",
        system_prompt=(
            "You are a helpful travel assistant. "
            "Use tools to answer questions about weather and time. "
            "Be concise and friendly."
        ),
        tools=[get_weather, get_current_time],
    )

    response = agent(prompt)
    return {"response": _strip_thinking(str(response))}


# ---------------------------------------------------------------------------
# Local entry point — starts uvicorn for local testing
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # This starts the same HTTP server AgentCore Runtime expects.
    # Listens on http://localhost:8080/invocations
    app.run()
