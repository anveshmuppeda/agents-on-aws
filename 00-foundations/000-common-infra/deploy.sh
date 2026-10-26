#!/bin/bash
# deploy.sh — 000-common-infra
# Deploy ONCE before running any guide.
# Creates shared IAM roles and SSM parameters used by all 66 guides.
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


STACK="AgentsOnAwsCommonInfra"
REGION="us-east-1"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo ""
echo "=== 000-common-infra: Shared Infrastructure ==="
echo ""
echo "This stack deploys ONCE and is used by all 66 guides."
echo "Estimated time: ~2 minutes"
echo ""
echo "Creating:"
echo "  • AgentCoreExecutionRole  (used by all Runtime agents)"
echo "  • LambdaExecutionRole     (used by Lambda tool functions)"
echo "  • GatewayExecutionRole    (used by Gateway resources)"
echo "  • BrowserExecutionRole    (used by Browser resources)"
echo "  • CodeInterpreterRole     (used by Code Interpreter)"
echo "  • 9 SSM Parameters        (guides read roles via SSM)"
echo ""

cd "$SCRIPT_DIR/Infra"
cdk deploy "$STACK" \
  --require-approval never \
  --outputs-file "/tmp/common-infra-outputs.json"

echo ""
echo "=== Common infra deployed! ==="
echo ""
echo "IAM Role ARNs:"
aws cloudformation describe-stacks \
  --stack-name "$STACK" \
  --region "$REGION" \
  --query "Stacks[0].Outputs[*].[OutputKey,OutputValue]" \
  --output table

echo ""
echo "SSM Parameters created:"
aws ssm get-parameters-by-path \
  --path "/agents-on-aws" \
  --region "$REGION" \
  --query "Parameters[*].[Name,Value]" \
  --output table

echo ""
echo "Next step: run any guide's bash deploy.sh"
