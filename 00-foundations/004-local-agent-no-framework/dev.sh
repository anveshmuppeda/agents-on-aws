#!/bin/bash
# dev.sh — 004-local-agent-no-framework
# Runs the agent locally (no dev server, direct Python execution).
set -euo pipefail

cd "$(dirname "$0")/Source"
pip3 install -q -r requirements.txt
echo "Starting agent in interactive mode..."
python3 app/agent.py
