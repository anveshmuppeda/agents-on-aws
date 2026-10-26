#!/bin/bash
# invoke.sh — 002-project-template
# Invokes the deployed agent with a test prompt.
set -euo pipefail

GUIDE="002-project-template"
AGENT="no-agent"
REGION="us-east-1"

echo "Running locally: 002-project-template"
cd "$(dirname "$0")/Source"
pip3 install -q -r requirements.txt
python3 app/agent.py "Hello, what can you help me with?"
