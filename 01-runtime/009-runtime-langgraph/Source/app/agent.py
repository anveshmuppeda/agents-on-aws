"""
009 — Runtime: LangGraph Agent
================================

A LangGraph ReAct agent deployed to AgentCore Runtime.

Key difference vs. Strands:
  - Strands:    pass a list of @tool functions to Agent(tools=[...]) — the
                framework builds the ReAct loop automatically.
  - LangGraph:  you build the state graph manually. create_react_agent() is a
                helper that wires a ToolNode + LLM into a standard ReAct
                StateGraph, but you own the graph construction, checkpointing,
                and streaming logic. BedrockAgentCoreApp wraps the resulting
                graph exactly the same way it wraps a Strands agent.

Graph structure (created by create_react_agent):
    START → agent_node → (tool_node ↔ agent_node) → END

Required environment variables:
    AWS_REGION — defaults to us-east-1

Local testing:
    python3 Source/app/agent.py
    agentcore invoke --dev '{"prompt": "What is the weather in Seattle?"}'
"""

import logging
import os
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from langchain_aws import ChatBedrockConverse
from langchain_core.tools import tool as lc_tool
from langgraph.prebuilt import create_react_agent

from bedrock_agentcore import BedrockAgentCoreApp

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tools (LangChain-style @tool so LangGraph can bind them to the LLM)
# ---------------------------------------------------------------------------

MOCK_WEATHER = {
    "austin":   {"temp": "92°F / 33°C",  "condition": "Sunny",      "humidity": "45%"},
    "new york": {"temp": "75°F / 24°C",  "condition": "Partly Cloudy", "humidity": "60%"},
    "seattle":  {"temp": "58°F / 14°C",  "condition": "Overcast",   "humidity": "78%"},
    "london":   {"temp": "61°F / 16°C",  "condition": "Light Rain", "humidity": "82%"},
    "tokyo":    {"temp": "79°F / 26°C",  "condition": "Clear",      "humidity": "55%"},
    "sydney":   {"temp": "68°F / 20°C",  "condition": "Sunny",      "humidity": "50%"},
    "paris":    {"temp": "64°F / 18°C",  "condition": "Cloudy",     "humidity": "70%"},
}

TIMEZONE_MAP = {
    "london":   "Europe/London",
    "tokyo":    "Asia/Tokyo",
    "paris":    "Europe/Paris",
    "sydney":   "Australia/Sydney",
    "seattle":  "America/Los_Angeles",
    "new york": "America/New_York",
    "austin":   "America/Chicago",
    "utc":      "UTC",
}


@lc_tool
def get_weather(location: str) -> str:
    """Get the current weather for a city or location."""
    key = location.lower().split(",")[0].strip()
    w = MOCK_WEATHER.get(key)
    if w is None:
        return f"Weather data not available for '{location}'."
    return (
        f"Weather in {location}: {w['condition']}, "
        f"{w['temp']}, humidity {w['humidity']}."
    )


@lc_tool
def get_time(location: str) -> str:
    """Get the current local time for a city or timezone name."""
    key = location.lower().strip()
    tz_name = TIMEZONE_MAP.get(key, location)
    try:
        tz = ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        return f"Unknown timezone: '{location}'."
    now = datetime.now(tz)
    return (
        f"Current time in {location} ({tz_name}): "
        f"{now.strftime('%A, %B %d %Y  %I:%M %p')}"
    )


# ---------------------------------------------------------------------------
# Build the LangGraph ReAct agent
#
# create_react_agent wires: START → llm_node → ToolNode → llm_node → END
# State is a MessagesState; the LLM loops until it stops calling tools.
# ---------------------------------------------------------------------------

_llm = ChatBedrockConverse(
    model="us.amazon.nova-pro-v1:0",
    region_name=os.environ.get("AWS_REGION", "us-east-1"),
)

_graph = create_react_agent(
    model=_llm,
    tools=[get_weather, get_time],
    prompt=(
        "You are a helpful travel assistant. "
        "Use get_weather and get_time to answer questions. "
        "Be concise and friendly."
    ),
)

# ---------------------------------------------------------------------------
# AgentCore Runtime app
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

    Unlike Strands where agent(prompt) runs the ReAct loop automatically,
    here we invoke the LangGraph graph directly with a HumanMessage and
    extract the final AI message from the output state.
    """
    from langchain_core.messages import HumanMessage

    prompt = payload.get("prompt", "").strip()
    if not prompt:
        return {"error": "Missing 'prompt' in payload."}

    logger.info("LangGraph invoke: %s", prompt)

    # Invoke the graph — returns final MessagesState
    result = _graph.invoke({"messages": [HumanMessage(content=prompt)]})

    # The last message in the state is the final AI response
    messages = result.get("messages", [])
    final_answer = messages[-1].content if messages else "No response generated."

    return {"response": final_answer}


if __name__ == "__main__":
    app.run()
