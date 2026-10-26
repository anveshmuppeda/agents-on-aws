"""
007 — Harness vs Runtime (Runtime path)
========================================

This is the Runtime version of the same agent that harness_config.json describes.
Both do the same job — the difference is HOW you deploy them.

  Harness:  agentcore harness create --config harness_config.json  (no Docker, 30 sec)
  Runtime:  bash deploy.sh  (Docker + CDK + CfnRuntime)
"""

import re
from strands import Agent, tool
from bedrock_agentcore import BedrockAgentCoreApp

# ── Mock weather data ────────────────────────────────────────────────────────
MOCK_WEATHER = {
    "austin":    "92°F / 33°C, Sunny",
    "new york":  "75°F / 24°C, Partly Cloudy",
    "seattle":   "58°F / 14°C, Overcast",        # ← added
    "london":    "61°F / 16°C, Light Rain",
    "tokyo":     "79°F / 26°C, Clear",
    "sydney":    "68°F / 20°C, Sunny",
    "paris":     "64°F / 18°C, Cloudy",
    "berlin":    "55°F / 13°C, Partly Cloudy",   # ← added
    "dubai":     "95°F / 35°C, Sunny",            # ← added
    "singapore": "86°F / 30°C, Humid",            # ← added
}

TIMEZONE_ALIASES = {
    "london": "Europe/London",   "tokyo":     "Asia/Tokyo",
    "paris":  "Europe/Paris",    "sydney":    "Australia/Sydney",
    "seattle":"America/Los_Angeles", "new york": "America/New_York",
    "austin": "America/Chicago", "berlin":    "Europe/Berlin",
    "dubai":  "Asia/Dubai",      "singapore": "Asia/Singapore",
    "utc":    "UTC",
}


@tool
def get_weather(location: str) -> str:
    """Get the current weather for a city or location."""
    key = location.lower().split(",")[0].strip()
    result = MOCK_WEATHER.get(key)
    if result is None:
        # Try partial match
        for city, data in MOCK_WEATHER.items():
            if city in key or key in city:
                return f"Weather in {location}: {data}"
        return (
            f"Weather data not available for '{location}'. "
            f"Try: {', '.join(MOCK_WEATHER.keys())}"
        )
    return f"Weather in {location}: {result}"


@tool
def get_current_time(timezone: str) -> str:
    """Get the current date and time for a timezone or city."""
    import datetime
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

    tz_name = TIMEZONE_ALIASES.get(timezone.lower().strip(), timezone)
    try:
        now = datetime.datetime.now(ZoneInfo(tz_name))
        return f"Time in {timezone} ({tz_name}): {now.strftime('%I:%M %p, %A %B %d, %Y')}"
    except ZoneInfoNotFoundError:
        return f"Unknown timezone '{timezone}'. Try: {', '.join(TIMEZONE_ALIASES.keys())}"


def strip_thinking_tags(text: str) -> str:
    """Remove <thinking>...</thinking> blocks from model output."""
    return re.sub(r'<thinking>.*?</thinking>\s*', '', text, flags=re.DOTALL).strip()


# ── App ──────────────────────────────────────────────────────────────────────


def _strip_thinking(text: str) -> str:
    """Remove <thinking>...</thinking> blocks from model output."""
    import re as _re
    return _re.sub(r'<thinking>.*?</thinking>\s*', '', text, flags=_re.DOTALL).strip()


app = BedrockAgentCoreApp()


@app.entrypoint
def invoke(payload: dict) -> dict:
    prompt = payload.get("prompt", "Hello")
    agent = Agent(
        model="us.amazon.nova-pro-v1:0",
        system_prompt=(
            "You are a helpful travel assistant. "
            "Use the get_weather and get_current_time tools whenever asked about "
            "weather or time in any city. Never guess — always use the tools."
        ),
        tools=[get_weather, get_current_time],
    )
    response = str(agent(prompt))
    return {
        "response": strip_thinking_tags(response),
        "path": "runtime",
    }


if __name__ == "__main__":
    app.run()
