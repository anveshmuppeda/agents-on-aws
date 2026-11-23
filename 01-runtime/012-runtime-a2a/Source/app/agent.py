"""
012 — AgentCore Runtime: Agent-to-Agent (A2A) Server
======================================================

Deploys an A2A 0.3 server to AgentCore Runtime using the AgentCore A2A adapter.
Clients discover capabilities through the Agent Card and send tasks using
JSON-RPC 2.0.

The Agent Card advertises these capabilities, which the Strands agent fulfills
using its internal tools:
  - add_numbers(a, b) → arithmetic sum
  - summarize_text(text, max_sentences) → LLM-generated summary

Port: 9000 (A2A convention — distinct from AgentCore's 8080)

Local testing:
    bash dev.sh
    curl http://localhost:9000/.well-known/agent-card.json
    python3 Source/test_client.py
"""

import logging
import os
import threading

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
    Part,
    TextPart,
)
from a2a.utils import new_task
from strands import Agent, tool
from strands.models import BedrockModel
from bedrock_agentcore.runtime import serve_a2a

logger = logging.getLogger(__name__)

MODEL_ID = os.environ.get("MODEL_ID", "us.amazon.nova-pro-v1:0")
REGION = os.environ.get("AWS_DEFAULT_REGION", os.environ.get("AWS_REGION", "us-east-1"))

# ---------------------------------------------------------------------------
# Internal tools selected by the Strands agent
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
# A2A Agent Card
# ---------------------------------------------------------------------------

AGENT_CARD = AgentCard(
    name="guide-012-a2a-server",
    description="A Strands agent that can add numbers and summarize text.",
    url="http://localhost:9000/",
    version="1.0.0",
    capabilities=AgentCapabilities(streaming=False, pushNotifications=False),
    skills=[
        AgentSkill(
            id="add_numbers",
            name="Add Numbers",
            description="Adds two numbers and returns their sum.",
            tags=["math", "arithmetic"],
            examples=["Add 42 and 58", "What is 3.14 + 2.72?"],
        ),
        AgentSkill(
            id="summarize_text",
            name="Summarize Text",
            description="Summarizes text in a requested number of sentences.",
            tags=["text", "summarization"],
            examples=["Summarize this paragraph in two sentences."],
        ),
    ],
    defaultInputModes=["text"],
    defaultOutputModes=["text"],
)


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
# A2A executor
# ---------------------------------------------------------------------------

class StrandsA2AExecutor(AgentExecutor):
    def __init__(self) -> None:
        self._cancel_signals: dict[str, threading.Event] = {}

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        task = context.current_task or new_task(context.message)
        cancel_signal = threading.Event()
        self._cancel_signals[task.id] = cancel_signal

        if context.current_task is None:
            await event_queue.enqueue_event(task)

        try:
            updater = TaskUpdater(event_queue, task.id, task.context_id)
            user_text = context.get_user_input()
            logger.info("A2A task received: %s", user_text[:120])

            agent = _build_agent()
            response = await agent.invoke_async(
                user_text,
                cancel_signal=cancel_signal,
            )
            if cancel_signal.is_set():
                return

            await updater.add_artifact(
                [Part(root=TextPart(text=str(response).strip()))],
                name="result",
            )
            await updater.complete()
        finally:
            self._cancel_signals.pop(task.id, None)

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        task = context.current_task
        if task is None:
            raise ValueError("A2A cancellation requires an active task.")

        cancel_signal = self._cancel_signals.get(task.id)
        if cancel_signal is None:
            raise ValueError(f"No active execution found for A2A task {task.id!r}.")

        cancel_signal.set()
        updater = TaskUpdater(event_queue, task.id, task.context_id)
        await updater.cancel()


# ---------------------------------------------------------------------------
# A2A server entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    serve_a2a(StrandsA2AExecutor(), AGENT_CARD)
