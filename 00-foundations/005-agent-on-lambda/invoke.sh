#!/bin/bash
# invoke.sh — 005-agent-on-lambda
# Invokes the deployed agent with a test prompt.
set -euo pipefail

GUIDE="005-agent-on-lambda"
AGENT="no-agent"
REGION="us-east-1"

STACK="Guide005AgentOnLambda"
API_URL=$(aws cloudformation describe-stacks \
  --stack-name "$STACK" --region "$REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" \
  --output text)

echo "Invoking: $API_URL"
curl -s -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{ "prompt": "What is the weather in Austin?" }' | python3 -m json.tool
