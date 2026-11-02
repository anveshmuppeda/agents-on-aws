"""
010 — AgentCore Runtime: Model-Agnostic Agents
===============================================

The SAME agent code runs on any Bedrock model by reading MODEL_ID from env.
No code changes, no rebuild — just update the environment variable.

Supported model IDs (examples):
  us.amazon.nova-pro-v1:0                            (default)
  us.anthropic.claude-3-5-sonnet-20241022-v2:0
  amazon.titan-text-premier-v1:0

Local testing:
    agentcore dev --port 8080
    MODEL_ID=us.anthropic.claude-3-5-sonnet-20241022-v2:0 agentcore dev --port 8080

    curl -X POST http://localhost:8080/invocations \\
         -H "Content-Type: application/json" \\
         -d '{"prompt": "What is the weather in Austin, TX?"}'
"""

import logging
import os

from strands import Agent, tool
from strands.models import BedrockModel
from bedrock_agentcore import BedrockAgentCoreApp

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Model selection — the entire point of this guide
# ---------------------------------------------------------------------------

MODEL_ID = os.environ.get("MODEL_ID", "us.amazon.nova-pro-v1:0")
REGION = os.environ.get("AWS_DEFAULT_REGION", os.environ.get("AWS_REGION", "us-east-1"))

logger.info("Starting with model_id=%s region=%s", MODEL_ID, REGION)

# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

WEATHER_DB: dict[str, dict] = {
    "austin":      {"temp": "92°F / 33°C",  "condition": "Sunny",         "humidity": "45%", "wind": "12 mph S"},
    "new york":    {"temp": "75°F / 24°C",  "condition": "Partly Cloudy", "humidity": "60%", "wind": "8 mph NE"},
    "seattle":     {"temp": "58°F / 14°C",  "condition": "Overcast",      "humidity": "78%", "wind": "15 mph W"},
    "london":      {"temp": "61°F / 16°C",  "condition": "Light Rain",    "humidity": "82%", "wind": "10 mph SW"},
    "tokyo":       {"temp": "79°F / 26°C",  "condition": "Clear",         "humidity": "55%", "wind": "5 mph E"},
    "sydney":      {"temp": "68°F / 20°C",  "condition": "Sunny",         "humidity": "50%", "wind": "18 mph SE"},
    "paris":       {"temp": "64°F / 18°C",  "condition": "Cloudy",        "humidity": "70%", "wind": "9 mph W"},
    "chicago":     {"temp": "70°F / 21°C",  "condition": "Windy",         "humidity": "52%", "wind": "22 mph N"},
    "miami":       {"temp": "88°F / 31°C",  "condition": "Thunderstorm",  "humidity": "88%", "wind": "14 mph E"},
    "san francisco": {"temp": "62°F / 17°C", "condition": "Foggy",        "humidity": "75%", "wind": "11 mph W"},
}


@tool
def get_weather(location: str) -> str:
    """
    Get the current weather for a city or location.

    Args:
        location: City name (e.g. "Austin", "London", "Tokyo")

    Returns:
        Formatted weather string with temperature, conditions, humidity, and wind.
    """
    key = location.lower().split(",")[0].strip()
    data = WEATHER_DB.get(key)
    if data is None:
        known = ", ".join(k.title() for k in WEATHER_DB)
        return (
            f"Weather data not available for '{location}'. "
            f"Known cities: {known}."
        )
    return (
        f"Current weather in {location.title()}:\n"
        f"  Temperature : {data['temp']}\n"
        f"  Condition   : {data['condition']}\n"
        f"  Humidity    : {data['humidity']}\n"
        f"  Wind        : {data['wind']}"
    )


# ---------------------------------------------------------------------------
# Build Bedrock model — reusable across calls
# ---------------------------------------------------------------------------

def _build_model() -> BedrockModel:
    """Construct BedrockModel from environment variables."""
    return BedrockModel(
        model_id=MODEL_ID,
        region_name=REGION,
        temperature=0.0,
        max_tokens=1024,
    )


# Build model once at module load time — hot in the microVM
_model = _build_model()

# ---------------------------------------------------------------------------
# AgentCore App
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

    Payload:
        {"prompt": "What is the weather in London?"}

    Response:
        {"response": "...", "model_id": "us.amazon.nova-pro-v1:0"}
    """
    prompt = payload.get("prompt", "").strip()
    if not prompt:
        return {"error": "Missing 'prompt' in payload"}

    logger.info("[022] model=%s prompt=%s", MODEL_ID, prompt[:80])

    agent = Agent(
        model=_model,
        system_prompt=(
            "You are a helpful weather assistant. "
            "Use the get_weather tool to answer questions about weather. "
            "Always mention which model you are (hint: you don't know your own model ID, "
            "but the API metadata will show it). Be concise and friendly."
        ),
        tools=[get_weather],
    )

    response = agent(prompt)

    return {
        "response": _strip_thinking(str(response)),
        "model_id": MODEL_ID,
        "region": REGION,
    }


# ---------------------------------------------------------------------------
# Local entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(port=port)
