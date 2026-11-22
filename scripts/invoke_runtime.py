#!/usr/bin/env python3
"""Invoke an AgentCore Runtime deployed by one of this repo's CDK stacks."""

import argparse
import json
import os


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stack", help="CloudFormation stack name")
    parser.add_argument("prompt", help="Prompt to send to the Runtime")
    parser.add_argument(
        "--session",
        dest="session_id",
        help="Optional Runtime session ID to reuse",
    )
    args = parser.parse_args()

    import boto3

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
        raise RuntimeError(
            f"CloudFormation stack {args.stack!r} has no RuntimeArn output."
        )

    client = session.client("bedrock-agentcore")
    request = {
        "agentRuntimeArn": runtime_arn,
        "payload": json.dumps({"prompt": args.prompt}).encode("utf-8"),
        "contentType": "application/json",
        "accept": "application/json",
    }
    if args.session_id:
        request["runtimeSessionId"] = args.session_id

    result = client.invoke_agent_runtime(**request)
    response = json.loads(result["response"].read())

    print(f"Stack:   {args.stack}")
    if args.session_id:
        print(f"Session: {args.session_id}")
    print(f"Prompt:  {args.prompt}")
    print(f"Runtime: {runtime_arn}")
    print()
    print(json.dumps(response, indent=2))


if __name__ == "__main__":
    main()
