#!/bin/bash
# deploy.sh — 003-local-agent-strands
# Deploys all AWS resources for this guide.
# Run: bash deploy.sh
set -euo pipefail

GUIDE="003-local-agent-strands"
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
