#!/bin/bash
# invoke-dev.sh — 011-runtime-mcp-server
# Send a prompt to the running local dev server.
# Start the dev server first: bash dev.sh
# Usage: bash invoke-dev.sh
set -euo pipefail

export JSII_SILENCE_WARNING_UNTESTED_NODE_VERSION=1

PROMPT="List the available tools."

echo "Sending to local dev server..."
echo "Prompt: $PROMPT"
echo "(Make sure bash dev.sh is running in another terminal)"
echo ""

agentcore dev \
  --json \
  "$PROMPT"
