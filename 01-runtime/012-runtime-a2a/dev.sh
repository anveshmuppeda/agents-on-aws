#!/bin/bash
# dev.sh — 012-runtime-a2a
# Start the local A2A server.
# In another terminal: bash invoke-dev.sh
# Usage: bash dev.sh
set -euo pipefail

export JSII_SILENCE_WARNING_UNTESTED_NODE_VERSION=1

echo ""
echo "=== Dev server: 012-runtime-a2a ==="
echo "Starting A2A server on port 9000..."
echo "In another terminal, run: bash invoke-dev.sh"
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$SCRIPT_DIR"
while [ "$REPO_ROOT" != "/" ] && [ ! -f "$REPO_ROOT/.venv/bin/activate" ]; do
  REPO_ROOT="$(dirname "$REPO_ROOT")"
done
[ -f "$REPO_ROOT/.venv/bin/activate" ] && source "$REPO_ROOT/.venv/bin/activate"

cd "$SCRIPT_DIR/Source"
exec python3 -m app.agent
