"""
004 — Local Agent with Raw boto3 (No Framework)
================================================

Implements the same agent as guide 004 but using ONLY boto3 and the
Bedrock Converse API. Zero frameworks. This makes the agent loop visible.

This is how every agent framework works under the hood:
  1. Build a messages list
  2. Call the model
  3. If the model returns a tool_use block → execute the tool
  4. Append tool result to messages
  5. Call the model again
  6. Repeat until the model returns text only (no tool call) → done

Usage:
    python3 Source/app/agent.py
    python3 Source/app/agent.py "What time is it in Paris?"
"""

import json
import sys
import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import boto3

# ---------------------------------------------------------------------------
# Tool implementations (same logic as guide 010, no @tool decorator)
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

TIMEZONE_ALIASES = {
    "utc": "UTC", "est": "America/New_York", "cst": "America/Chicago",
    "pst": "America/Los_Angeles", "london": "Europe/London",
    "paris": "Europe/Paris", "tokyo": "Asia/Tokyo",
    "sydney": "Australia/Sydney", "austin": "America/Chicago",
    "new york": "America/New_York", "seattle": "America/Los_Angeles",
}


def _get_weather(location: str) -> str:
    key = location.lower().split(",")[0].strip()
    weather = MOCK_WEATHER.get(key)
    if weather is None:
        for city, data in MOCK_WEATHER.items():
            if city in key or key in city:
                weather = data
                break
    if weather is None:
        return f"Weather data not available for '{location}'. Try: {', '.join(MOCK_WEATHER.keys())}"
    return (
        f"Current weather in {location}: "
        f"{weather['temp']}, {weather['condition']}, humidity {weather['humidity']}"
    )


def _get_current_time(timezone: str) -> str:
    key = timezone.lower().strip()
    tz_name = TIMEZONE_ALIASES.get(key, timezone)
    try:
        tz = ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        return f"Unknown timezone '{timezone}'. Try 'America/New_York', 'Europe/London', 'Tokyo', etc."
    now = datetime.datetime.now(tz)
    return f"Current time in {timezone} ({tz_name}): {now.strftime('%A, %B %d, %Y at %I:%M %p')}"


# ---------------------------------------------------------------------------
# Tool registry — maps tool name → callable
# ---------------------------------------------------------------------------

TOOL_FUNCTIONS = {
    "get_weather": lambda args: _get_weather(args["location"]),
    "get_current_time": lambda args: _get_current_time(args["timezone"]),
}


# ---------------------------------------------------------------------------
# Tool specifications — this JSON tells the model what tools exist.
# This is the EXACT format the Bedrock Converse API expects.
# ---------------------------------------------------------------------------

TOOL_CONFIG = {
    "tools": [
        {
            "toolSpec": {
                "name": "get_weather",
                "description": "Get the current weather for a city or location.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "City name, e.g. 'Austin, TX' or 'London'",
                            }
                        },
                        "required": ["location"],
                    }
                },
            }
        },
        {
            "toolSpec": {
                "name": "get_current_time",
                "description": "Get the current date and time in a given timezone or city.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "timezone": {
                                "type": "string",
                                "description": "Timezone or city name, e.g. 'America/New_York', 'Tokyo', 'PST'",
                            }
                        },
                        "required": ["timezone"],
                    }
                },
            }
        },
    ]
}

SYSTEM_PROMPT = [
    {
        "text": (
            "You are a helpful travel assistant. You can check the current weather "
            "and time in cities around the world. Always use tools when asked about "
            "weather or time — never guess."
        )
    }
]

MODEL_ID = "us.amazon.nova-pro-v1:0"


# ---------------------------------------------------------------------------
# The Agent Loop — this is what frameworks do for you
# ---------------------------------------------------------------------------

def run_agent(user_prompt: str, verbose: bool = True) -> str:
    """
    Run the agent loop for a given user prompt.

    The loop:
      1. Add user message to messages list
      2. Call model via Converse API
      3. If model returns tool_use → execute tool, add result, go to 2
      4. If model returns text → return it

    Returns:
        The model's final text response.
    """
    client = boto3.client("bedrock-runtime", region_name="us-east-1")

    # Conversation history — grows with each turn
    messages = [
        {"role": "user", "content": [{"text": user_prompt}]}
    ]

    iteration = 0
    max_iterations = 10  # Safety limit to prevent infinite loops

    while iteration < max_iterations:
        iteration += 1

        if verbose:
            print(f"\n[Loop iteration {iteration}] Calling model...")

        # --- Step 1: Call the model ---
        response = client.converse(
            modelId=MODEL_ID,
            system=SYSTEM_PROMPT,
            messages=messages,
            toolConfig=TOOL_CONFIG,
        )

        stop_reason = response["stopReason"]
        output_message = response["output"]["message"]

        if verbose:
            print(f"[Loop iteration {iteration}] Stop reason: {stop_reason}")

        # Append model response to messages
        messages.append(output_message)

        # --- Step 2: Check stop reason ---
        if stop_reason == "end_turn":
            # Model is done — extract and return the text
            for block in output_message["content"]:
                if "text" in block:
                    return block["text"]

        elif stop_reason == "tool_use":
            # Model wants to call tools — process ALL tool calls in this response
            tool_results = []

            for block in output_message["content"]:
                if "toolUse" not in block:
                    continue

                tool_name = block["toolUse"]["name"]
                tool_input = block["toolUse"]["input"]
                tool_use_id = block["toolUse"]["toolUseId"]

                if verbose:
                    print(f"[Loop iteration {iteration}] Tool call: {tool_name}({json.dumps(tool_input)})")

                # Execute the tool
                fn = TOOL_FUNCTIONS.get(tool_name)
                if fn is None:
                    tool_result_content = f"Error: unknown tool '{tool_name}'"
                else:
                    try:
                        tool_result_content = fn(tool_input)
                    except Exception as e:
                        tool_result_content = f"Error executing {tool_name}: {e}"

                if verbose:
                    print(f"[Loop iteration {iteration}] Tool result: {tool_result_content}")

                tool_results.append({
                    "toolUseId": tool_use_id,
                    "content": [{"text": tool_result_content}],
                })

            # Append all tool results as a single "user" turn
            messages.append({
                "role": "user",
                "content": [{"toolResult": r} for r in tool_results],
            })

        else:
            # Unexpected stop reason
            return f"Unexpected stop reason: {stop_reason}"

    return "Agent loop exceeded maximum iterations."


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def run_interactive():
    print("\n" + "=" * 65)
    print("  AgentCore Hands-On | Guide 004: Raw boto3 Agent (No Framework)")
    print("=" * 65)
    print("The agent loop is fully visible in this guide.")
    print("Ask about weather or time. Type 'quit' to exit.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() in {"quit", "exit", "q"}:
            print("Goodbye!")
            break

        result = run_agent(user_input, verbose=True)
        print(f"\nAgent: {result}\n")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
        print(f"\nPrompt: {prompt}")
        result = run_agent(prompt, verbose=True)
        print(f"\nFinal answer: {result}")
    else:
        run_interactive()
