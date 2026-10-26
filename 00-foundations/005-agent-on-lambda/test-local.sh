#!/bin/bash
# test-local.sh — 005-agent-on-lambda
# Invoke the Lambda handler running locally via the RIE.
# Run dev.sh first in another terminal, then run this.
set -euo pipefail

ENDPOINT="http://localhost:9000/2015-03-31/functions/function/invocations"

echo "→  Invoking Lambda locally via RIE..."
echo "   (Make sure dev.sh is running in another terminal)"
echo ""

# Lambda RIE expects the full API Gateway event format
# We simulate it here with body as JSON string
curl -s -X POST "$ENDPOINT" \
  -H "Content-Type: application/json" \
  -d '{"body": "{\"prompt\": \"What is the weather in Austin?\"}"}' \
  | python3 -m json.tool
