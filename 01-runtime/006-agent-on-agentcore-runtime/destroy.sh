#!/bin/bash
# destroy.sh — 006-agent-on-agentcore-runtime
# Removes ALL AWS resources created by deploy.sh.
# WARNING: This is irreversible. Data will be lost.
set -euo pipefail

# Silence JSII warning about untested Node.js version — cosmetic, not an error
export JSII_SILENCE_WARNING_UNTESTED_NODE_VERSION=1


GUIDE="006-agent-on-agentcore-runtime"
REGION="us-east-1"

echo ""
echo "=== Destroy: ${GUIDE} ==="
echo ""
echo "WARNING: This will delete all AWS resources for this guide."
echo "All data (logs, stored memory, recorded sessions) will be lost."
read -p "Continue? [y/N] " -n 1 -r
echo ""
[[ $REPLY =~ ^[Yy]$ ]] || { echo "Aborted."; exit 0; }

echo "Destroying CDK stack..."
echo "(This removes: Runtime, Memory, Gateway, Lambda, ECR, Cognito, IAM — everything)"
cd "$(dirname "$0")/Infra"
cdk destroy "Guide006AgentOnAgentcoreRuntime" --force

echo ""
echo "Done. All resources removed."
