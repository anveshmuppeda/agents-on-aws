#!/bin/bash
# deploy.sh — 004-local-agent-no-framework
# Deploys all AWS resources for this guide.
# Run: bash deploy.sh
set -euo pipefail

GUIDE="004-local-agent-no-framework"
STACK="NO_STACK"
AGENT="no-agent"
REGION="us-east-1"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo ""
echo "=== Deploying ${GUIDE} ==="
echo ""
echo "This guide runs locally — no AWS deployment needed."
echo "Run:  bash dev.sh"

echo ""
echo "=== Done! ==="
echo "Next: bash invoke.sh"
