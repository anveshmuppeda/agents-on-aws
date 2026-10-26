#!/bin/bash
# dev.sh — 003-local-agent-strands
# Runs the agent locally (no dev server, direct Python execution).
set -euo pipefail

cd "$(dirname "$0")/Source"
pip3 install -q -r requirements.txt
echo "Starting agent in interactive mode..."
python3 app/agent.py
