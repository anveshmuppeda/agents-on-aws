#!/bin/bash
# invoke.sh — 004-local-agent-no-framework
# Invokes the deployed agent with a test prompt.
set -euo pipefail

GUIDE="004-local-agent-no-framework"
AGENT="no-agent"
REGION="us-east-1"

echo "Running locally: 004-local-agent-no-framework"
cd "$(dirname "$0")/Source"
pip3 install -q -r requirements.txt
python3 app/agent.py "What time is it in London?"
