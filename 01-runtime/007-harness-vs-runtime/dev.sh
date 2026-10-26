#!/bin/bash
# dev.sh — 007-harness-vs-runtime
# Start the local AgentCore dev server with hot reload.
# In another terminal: bash invoke-dev.sh
# Usage: bash dev.sh
set -euo pipefail

export JSII_SILENCE_WARNING_UNTESTED_NODE_VERSION=1

echo ""
echo "=== Dev server: 007-harness-vs-runtime ==="
echo "Starting AgentCore local dev server..."
echo "In another terminal, run: bash invoke-dev.sh"
echo ""

agentcore dev --logs
