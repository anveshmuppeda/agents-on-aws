#!/bin/bash
# dev.sh — 005-agent-on-lambda
# Test the Lambda handler locally using the Lambda Runtime Interface Emulator (RIE).
#
# How it works:
#   1. Builds the ARM64 container image
#   2. Starts the container with Lambda RIE on port 9000
#   3. You invoke it with: bash test-local.sh (in another terminal)
#
# This is the correct local test path for Lambda guides.
# (NOT agentcore dev — that is only for BedrockAgentCoreApp / Runtime guides)
set -euo pipefail

export JSII_SILENCE_WARNING_UNTESTED_NODE_VERSION=1

IMAGE_NAME="guide-005-lambda:local"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo ""
echo "=== Guide 005: Lambda Local Test ==="
echo ""

# ── Step 1: Build container ──────────────────────────────────────────────────
echo "→  Building ARM64 container image..."
docker build \
  --platform linux/arm64 \
  -t "$IMAGE_NAME" \
  "$SCRIPT_DIR/Source/"
echo "   ✅  Built $IMAGE_NAME"

# ── Step 2: Start Lambda RIE ──────────────────────────────────────────────────
echo ""
echo "→  Starting Lambda Runtime Interface Emulator on port 9000..."
echo "   Endpoint: http://localhost:9000/2015-03-31/functions/function/invocations"
echo ""
echo "   In ANOTHER terminal, run:"
echo "   curl -s -X POST http://localhost:9000/2015-03-31/functions/function/invocations \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"body\": \"{\\\"prompt\\\": \\\"What is the weather in Austin?\\\"}\"}'  | python3 -m json.tool"
echo ""
echo "   Press Ctrl+C to stop."
echo ""

docker run --rm \
  --platform linux/arm64 \
  -p 9000:8080 \
  -e AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID:-}" \
  -e AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY:-}" \
  -e AWS_SESSION_TOKEN="${AWS_SESSION_TOKEN:-}" \
  -e AWS_DEFAULT_REGION="us-east-1" \
  "$IMAGE_NAME"
