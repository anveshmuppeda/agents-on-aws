#!/bin/bash
# deploy.sh — 007-harness-vs-runtime
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


GUIDE="007-harness-vs-runtime"
STACK="Guide007HarnessVsRuntime"
AGENT="guide-007-runtime-agent"
REGION="us-east-1"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo ""
echo "=== Deploying ${GUIDE} ==="
echo ""
# ── CDK deploy: ECR image + IAM role + Runtime (CfnRuntime) ──────────
# All AgentCore Runtime resources are created by CDK (CfnRuntime).
# CDK builds the Docker image, pushes to ECR, and deploys the Runtime.
echo "Step 1/1 — CDK deploy"
echo "  - Builds Docker image and pushes to ECR"
echo "  - Creates IAM execution role"
echo "  - Creates AgentCore Runtime (aws_bedrockagentcore.CfnRuntime)"
echo "  - Creates CloudWatch log group"
cd "$SCRIPT_DIR/Infra"
cdk deploy "$STACK" \
  --require-approval never \
  --outputs-file "/tmp/outputs-${GUIDE}.json"

echo ""
echo "Runtime ARN:"
aws cloudformation describe-stacks \
  --stack-name "$STACK" --region "$REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='RuntimeArn'].OutputValue" \
  --output text

echo ""
echo "=== Done! ==="
echo "Next: bash invoke.sh"
