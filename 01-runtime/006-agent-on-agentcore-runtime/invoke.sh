#!/bin/bash
# invoke.sh — 006-agent-on-agentcore-runtime
# Invokes the deployed AgentCore Runtime agent via boto3.
# No agentcore CLI project config required.
# Usage: bash invoke.sh
set -euo pipefail

export JSII_SILENCE_WARNING_UNTESTED_NODE_VERSION=1
export AWS_PROFILE="${AWS_PROFILE:-anvesh-aws-profile}"

# Activate shared virtual environment
REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
while [ "$REPO_ROOT" != "/" ] && [ ! -f "$REPO_ROOT/.venv/bin/activate" ]; do
  REPO_ROOT="$(dirname "$REPO_ROOT")"
done
[ -f "$REPO_ROOT/.venv/bin/activate" ] && source "$REPO_ROOT/.venv/bin/activate"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
STACK="Guide006AgentOnAgentcoreRuntime"
PROMPT="What is the weather in Paris and the time there?"

echo ""
echo "Stack:   $STACK"
echo "Profile: $AWS_PROFILE"
echo "Prompt:  $PROMPT"
echo ""

python3 "$REPO_ROOT/scripts/invoke_runtime.py" \
  "$STACK" \
  "$PROMPT"
