#!/bin/bash
# deploy.sh — 005-agent-on-lambda
# Deploys all AWS resources for this guide.
# Run: bash deploy.sh
set -euo pipefail

# Silence JSII warning about untested Node.js version — cosmetic, not an error
export JSII_SILENCE_WARNING_UNTESTED_NODE_VERSION=1

export AWS_PROFILE="${AWS_PROFILE:-anvesh-aws-profile}"

# Activate the shared virtual environment (repo root)
REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
while [ "$REPO_ROOT" != "/" ] && [ ! -f "$REPO_ROOT/.venv/bin/activate" ]; do
  REPO_ROOT="$(dirname "$REPO_ROOT")"
done
[ -f "$REPO_ROOT/.venv/bin/activate" ] && source "$REPO_ROOT/.venv/bin/activate"

GUIDE="005-agent-on-lambda"
STACK="Guide005AgentOnLambda"
AGENT="no-agent"
REGION="us-east-1"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo ""
echo "=== Deploying ${GUIDE} ==="
echo ""
# ── CDK deploy: Lambda + API Gateway + ECR + IAM ──────────────────
echo "Step 1/1 — CDK deploy (Lambda, API Gateway, ECR, IAM)"
cd "$SCRIPT_DIR/Infra"
cdk deploy "$STACK" \
  --require-approval never \
  --outputs-file "/tmp/outputs-${GUIDE}.json"

# Show the API URL
echo ""
echo "API URL:"
aws cloudformation describe-stacks \
  --stack-name "$STACK" --region "$REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" \
  --output text

echo ""
echo "=== Done! ==="
echo "Next: bash invoke.sh"
