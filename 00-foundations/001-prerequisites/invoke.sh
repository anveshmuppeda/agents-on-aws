#!/bin/bash
# invoke.sh — 001-prerequisites
# Invokes the deployed agent with a test prompt.
set -euo pipefail

GUIDE="001-prerequisites"
AGENT="no-agent"
REGION="us-east-1"

echo "Running locally: 001-prerequisites"
cd "$(dirname "$0")/Source"
pip3 install -q -r requirements.txt
python3 app/agent.py "Hello, what can you help me with?"
