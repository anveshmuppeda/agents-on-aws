#!/bin/bash
# deploy.sh — 001-prerequisites
# Deploys all AWS resources for this guide.
# Run: bash deploy.sh
set -euo pipefail

GUIDE="001-prerequisites"
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
