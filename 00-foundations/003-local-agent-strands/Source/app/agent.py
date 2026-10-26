"""
003 — Local Agent with Strands
==============================

The simplest possible Strands agent. Runs entirely on your local machine.
Uses Amazon Bedrock (Nova Pro) for the model.

Usage:
    python3 Source/app/agent.py                    # Interactive mode
    python3 Source/app/agent.py "What time is it in Tokyo?"  # Single prompt
"""

import sys
from strands import Agent
from tools import get_weather, get_current_time

# ---------------------------------------------------------------------------
# Build the agent
# ---------------------------------------------------------------------------

# The system prompt tells the model its persona and purpose.
SYSTEM_PROMPT = """You are a helpful travel assistant. You can check the current
weather and time in cities around the world to help users plan their trips.

When asked about weather or time, always use the appropriate tool rather than
guessing. Be concise and friendly in your responses."""


def create_agent() -> Agent:
    """Create and return a Strands agent with our tools."""
    return Agent(
        # Amazon Bedrock model — Nova Pro in us-east-1
        # The "us." prefix routes to the US inference profile.
        model="us.amazon.nova-pro-v1:0",
        system_prompt=SYSTEM_PROMPT,
        tools=[get_weather, get_current_time],
    )


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

def run_interactive():
    """Start an interactive REPL with the agent."""
    agent = create_agent()

    print("\n" + "=" * 60)
    print("  AgentCore Hands-On | Guide 003: Local Agent with Strands")
    print("=" * 60)
    print("Ask me about weather or time in any major city.")
    print("Type 'quit' or press Ctrl+C to exit.\n")

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

        print()
        response = agent(user_input)
        print(f"\nAgent: {response}\n")


def run_single(prompt: str):
    """Run a single prompt and print the response."""
    agent = create_agent()
    print(f"\nPrompt: {prompt}\n")
    response = agent(prompt)
    print(f"Response: {response}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Single prompt mode
        run_single(" ".join(sys.argv[1:]))
    else:
        # Interactive mode
        run_interactive()
