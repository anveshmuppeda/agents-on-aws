#!/bin/bash
# invoke-dev.sh — 012-runtime-a2a
# Test the local A2A server.
# Start the dev server first: bash dev.sh
# Usage: bash invoke-dev.sh
set -euo pipefail

export JSII_SILENCE_WARNING_UNTESTED_NODE_VERSION=1

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
python3 "$SCRIPT_DIR/Source/test_client.py" --host localhost --port 9000
