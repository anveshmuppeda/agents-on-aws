"""
005 — Agent on Lambda
======================

Lambda handler wrapping a Strands agent.
Exposes the agent as a Lambda function behind API Gateway.

Event format (from API Gateway HTTP API):
    POST /invoke
    Body: {"prompt": "What's the weather in Seattle?"}

Response format:
    {"response": "...", "session_note": "..."}
"""

import json
import logging
from strands import Agent, tool

logger = logging.getLogger()
logger.setLevel(logging.INFO)


# ---------------------------------------------------------------------------
# Tool definitions (same as guide 003)
# ---------------------------------------------------------------------------

MOCK_WEATHER = {
    "austin":   {"temp": "92°F / 33°C",  "condition": "Sunny",         "humidity": "45%"},
    "new york": {"temp": "75°F / 24°C",  "condition": "Partly Cloudy", "humidity": "60%"},
    "seattle":  {"temp": "58°F / 14°C",  "condition": "Overcast",      "humidity": "78%"},
    "london":   {"temp": "61°F / 16°C",  "condition": "Light Rain",    "humidity": "82%"},
    "tokyo":    {"temp": "79°F / 26°C",  "condition": "Clear",         "humidity": "55%"},
}


@tool
def get_weather(location: str) -> str:
    """Get the current weather for a city or location."""
    key = location.lower().split(",")[0].strip()
    weather = MOCK_WEATHER.get(key)
    if weather is None:
        return f"Weather data not available for '{location}'."
    return f"Weather in {location}: {weather['temp']}, {weather['condition']}, humidity {weather['humidity']}"


@tool
def get_current_time(timezone: str) -> str:
    """Get the current time in a given timezone or city."""
    import datetime
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

    aliases = {
        "london": "Europe/London", "tokyo": "Asia/Tokyo",
        "seattle": "America/Los_Angeles", "new york": "America/New_York",
        "austin": "America/Chicago", "utc": "UTC",
    }
    tz_name = aliases.get(timezone.lower().strip(), timezone)
    try:
        tz = ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        return f"Unknown timezone '{timezone}'."
    now = datetime.datetime.now(tz)
    return f"Time in {timezone}: {now.strftime('%A, %B %d, %Y at %I:%M %p')}"


# ---------------------------------------------------------------------------
# Agent factory — create per invocation to avoid Lambda container sharing
# ---------------------------------------------------------------------------

def create_agent() -> Agent:
    return Agent(
        model="us.amazon.nova-pro-v1:0",
        system_prompt=(
            "You are a helpful travel assistant. "
            "Use tools to answer questions about weather and time. Never guess."
        ),
        tools=[get_weather, get_current_time],
    )


# ---------------------------------------------------------------------------
# Lambda handler
# ---------------------------------------------------------------------------

def handler(event: dict, context) -> dict:
    """
    Lambda entrypoint.

    Supports both:
    - API Gateway HTTP API (event["body"] as JSON string)
    - Direct Lambda invocation (event as plain dict)
    """
    logger.info("Event: %s", json.dumps(event, default=str))

    # Parse body — API Gateway wraps the payload in event["body"]
    body = event
    if "body" in event:
        try:
            body = json.loads(event["body"]) if isinstance(event["body"], str) else event["body"]
        except (json.JSONDecodeError, TypeError):
            return _response(400, {"error": "Invalid JSON in request body"})

    prompt = body.get("prompt", "").strip()
    if not prompt:
        return _response(400, {"error": "Missing 'prompt' in request body"})

    logger.info("Processing prompt: %s", prompt)

    # Create a fresh agent per invocation
    # NOTE: This is the key Lambda limitation — no session state is preserved
    # between invocations. Each call starts fresh.
    agent = create_agent()

    try:
        response = agent(prompt)
        return _response(200, {
            "response": str(response),
            "session_note": (
                "Note: Lambda agents are stateless. "
                "Each invocation starts a fresh context — no memory of previous calls."
            ),
        })
    except Exception as e:
        logger.exception("Agent error")
        return _response(500, {"error": str(e)})


def _response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }
