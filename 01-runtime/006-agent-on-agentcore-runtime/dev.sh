#!/bin/bash
# dev.sh — 006-agent-on-agentcore-runtime
# Start the local AgentCore dev server with hot reload.
# In another terminal: bash invoke-dev.sh
# Usage: bash dev.sh
set -euo pipefail

export JSII_SILENCE_WARNING_UNTESTED_NODE_VERSION=1

echo ""
echo "=== Dev server: 006-agent-on-agentcore-runtime ==="
echo "Starting AgentCore local dev server..."
echo "In another terminal, run: bash invoke-dev.sh"
echo ""

agentcore dev --logs
