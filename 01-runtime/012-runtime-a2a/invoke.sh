#!/bin/bash
# invoke.sh — 012-runtime-a2a
# Runs a local coordinator agent that discovers and calls the deployed A2A agent.
# Usage: bash invoke.sh
set -euo pipefail

export JSII_SILENCE_WARNING_UNTESTED_NODE_VERSION=1

# Activate shared virtual environment
REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
while [ "$REPO_ROOT" != "/" ] && [ ! -f "$REPO_ROOT/.venv/bin/activate" ]; do
  REPO_ROOT="$(dirname "$REPO_ROOT")"
done
[ -f "$REPO_ROOT/.venv/bin/activate" ] && source "$REPO_ROOT/.venv/bin/activate"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
STACK="Guide012RuntimeA2A"
PROMPT="${1:-Add 42 and 58.}"

echo ""
echo "Stack:   $STACK"
echo "Profile: ${AWS_PROFILE:-default credential chain}"
echo "Prompt:  $PROMPT"
echo "Flow:    local coordinator -> A2A Runtime specialist"
echo ""

python3 "$SCRIPT_DIR/Source/a2a_orchestrator.py" \
  --stack "$STACK" \
  --prompt "$PROMPT"
