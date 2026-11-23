"""Run a local Strands coordinator that delegates tasks to the deployed A2A agent."""

import argparse
import json
import os
import uuid

import boto3
from strands import Agent, tool
from strands.models import BedrockModel


def _read_runtime_response(response: dict) -> dict:
    stream = response.get("response")
    if stream is None:
        raise RuntimeError("AgentCore returned no response body.")

    try:
        body = stream.read()
    finally:
        stream.close()

    result = json.loads(body)
    if "error" in result:
        raise RuntimeError(f"A2A request failed: {result['error']}")
    if "result" not in result:
        raise RuntimeError(f"A2A response did not contain a result: {result}")
    return result["result"]


def _get_result_text(result: dict) -> str:
    if result.get("kind") == "task":
        state = result.get("status", {}).get("state")
        if state != "completed":
            raise RuntimeError(f"Remote A2A task did not complete: {state}")
        parts = [
            part
            for artifact in result.get("artifacts", [])
            for part in artifact.get("parts", [])
        ]
    else:
        parts = result.get("parts", [])

    texts = [
        part["text"]
        for part in parts
        if part.get("kind") == "text" and part.get("text")
    ]
    if not texts:
        raise RuntimeError(f"Remote A2A result did not contain text: {result}")
    return "\n".join(texts)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stack", default="Guide012RuntimeA2A")
    parser.add_argument("--prompt", default="Add 42 and 58.")
    args = parser.parse_args()

    region = (
        os.environ.get("AWS_DEFAULT_REGION")
        or os.environ.get("AWS_REGION")
        or "us-east-1"
    )
    session = boto3.Session(region_name=region)
    cloudformation = session.client("cloudformation")
    stacks = cloudformation.describe_stacks(StackName=args.stack)["Stacks"]
    outputs = {
        output["OutputKey"]: output["OutputValue"]
        for output in stacks[0].get("Outputs", [])
    }
    runtime_arn = outputs.get("RuntimeArn")
    if not runtime_arn:
        raise RuntimeError(f"Stack {args.stack!r} has no RuntimeArn output.")

    runtime = session.client("bedrock-agentcore")
    discovery = runtime.get_agent_card(agentRuntimeArn=runtime_arn)
    agent_card = discovery.get("agentCard")
    if not agent_card:
        raise RuntimeError(f"Runtime {runtime_arn!r} did not return an Agent Card.")

    skill_names = ", ".join(
        skill["name"] for skill in agent_card.get("skills", [])
    )
    if not skill_names:
        raise RuntimeError("The discovered A2A Agent Card advertises no skills.")

    print(f"Coordinator: local Strands agent ({region})")
    print(f"Discovered:  {agent_card['name']}")
    print(f"Skills:      {skill_names}")
    print(f"Prompt:      {args.prompt}")

    @tool
    def delegate_to_a2a_specialist(task: str) -> str:
        """Send a task to the discovered remote A2A agent and return its result."""
        print(f"\nA2A delegation -> {agent_card['name']}: {task}")
        request = {
            "jsonrpc": "2.0",
            "id": f"req-{uuid.uuid4().hex}",
            "method": "message/send",
            "params": {
                "message": {
                    "kind": "message",
                    "messageId": f"msg-{uuid.uuid4().hex}",
                    "role": "user",
                    "parts": [{"kind": "text", "text": task}],
                },
            },
        }
        response = runtime.invoke_agent_runtime(
            agentRuntimeArn=runtime_arn,
            runtimeSessionId=str(uuid.uuid4()),
            contentType="application/json",
            accept="application/json",
            payload=json.dumps(request).encode("utf-8"),
        )
        result = _read_runtime_response(response)
        answer = _get_result_text(result)
        print(f"A2A response <- {agent_card['name']}: {answer}")
        return answer

    coordinator = Agent(
        model=BedrockModel(
            model_id=os.environ.get(
                "ORCHESTRATOR_MODEL_ID", "us.amazon.nova-pro-v1:0"
            ),
            region_name=region,
        ),
        system_prompt=(
            "You are a coordinator agent. You have discovered a remote A2A agent "
            f"named {agent_card['name']!r} with these advertised skills: "
            f"{skill_names}. For arithmetic or summarization requests, always "
            "delegate the task using delegate_to_a2a_specialist. Do not solve "
            "those tasks yourself. Explain the specialist's result briefly."
        ),
        tools=[delegate_to_a2a_specialist],
    )

    print("\nCoordinator response:")
    print(coordinator(args.prompt))


if __name__ == "__main__":
    main()
