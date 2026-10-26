#!/bin/bash
# destroy.sh — 004-local-agent-no-framework
# Removes ALL AWS resources created by deploy.sh.
# WARNING: This is irreversible. Data will be lost.
set -euo pipefail

GUIDE="004-local-agent-no-framework"
REGION="us-east-1"

echo ""
echo "=== Destroy: ${GUIDE} ==="
echo ""
echo "WARNING: This will delete all AWS resources for this guide."
echo "All data (logs, stored memory, recorded sessions) will be lost."
read -p "Continue? [y/N] " -n 1 -r
echo ""
[[ $REPLY =~ ^[Yy]$ ]] || { echo "Aborted."; exit 0; }

echo "No AWS resources to remove (local guide)."

echo ""
echo "Done. All resources removed."
