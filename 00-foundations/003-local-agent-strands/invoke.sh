#!/bin/bash
# invoke.sh — 003-local-agent-strands
# Invokes the deployed agent with a test prompt.
set -euo pipefail

GUIDE="003-local-agent-strands"
AGENT="no-agent"
REGION="us-east-1"

echo "Running locally: 003-local-agent-strands"
cd "$(dirname "$0")/Source"
pip3 install -q -r requirements.txt
python3 app/agent.py "What is the weather in Tokyo?"
