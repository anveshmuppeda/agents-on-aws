#!/bin/bash
# setup-env.sh — Create the shared Python virtual environment for all 66 guides.
#
# Run ONCE from the repo root:
#   bash setup-env.sh
#
# Then activate at the start of every session:
#   source .venv/bin/activate

set -euo pipefail

# Silence JSII warning about untested Node.js version — cosmetic, not an error
export JSII_SILENCE_WARNING_UNTESTED_NODE_VERSION=1


VENV_DIR=".venv"

echo ""
echo "=== Agents on AWS — Environment Setup ==="
echo ""

# ── 1. Check Python version ──────────────────────────────────────────────────
PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)

if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]; }; then
  echo "❌  Python 3.10+ required, found $PY_VER"
  echo "    Install: brew install python@3.11"
  exit 1
fi
echo "✅  Python $PY_VER"

# ── 2. Create virtual environment ────────────────────────────────────────────
if [ -d "$VENV_DIR" ]; then
  echo "✅  .venv already exists"
else
  echo "→   Creating .venv ..."
  python3 -m venv "$VENV_DIR"
  echo "✅  .venv created"
fi

# ── 3. Activate ──────────────────────────────────────────────────────────────
echo "→   Activating .venv ..."
# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"

# ── 4. Upgrade pip ───────────────────────────────────────────────────────────
echo "→   Upgrading pip ..."
pip3 install --quiet --upgrade pip
echo "→   Upgrading CDK CLI (must be >=2.1146 for aws_bedrockagentcore constructs) ..."
npm install -g aws-cdk@latest 2>&1 | tail -1

# ── 5. Install core packages (needed for all guides) ─────────────────────────
echo ""
echo "→   Step 1/3 — Installing core packages ..."
echo "    (strands-agents, bedrock-agentcore, boto3, aws-cdk-lib)"
pip3 install \
  "strands-agents>=1.57.2" \
  "bedrock-agentcore>=1.24.0" \
  "boto3>=1.38.0" \
  "aws-cdk-lib>=2.243.0" \
  "constructs>=10.0.0" \
  "packaging>=23.0" \
  "python-dotenv>=1.0.0"

echo "    ✅  Core packages installed"

# ── 6. Install guide-specific packages ────────────────────────────────────────
echo ""
echo "→   Step 2/3 — Installing guide-specific packages ..."
echo "    (httpx, requests, mcp, opentelemetry, langgraph, playwright)"

pip3 install \
  "httpx>=0.28.1" \
  "requests>=2.32.0" \
  "mcp>=1.23.0"

pip3 install \
  "aws-opentelemetry-distro>=0.21.0" \
  "opentelemetry-sdk>=1.30.0" \
  "opentelemetry-api>=1.30.0"

pip3 install \
  "langgraph>=0.2.0" \
  "langchain-aws>=0.2.0"

# CrewAI is large — install it but don't fail the whole setup if it errors
pip3 install "crewai>=0.11.0" || \
  echo "    ⚠️   crewai install failed (optional — only needed for guide 064)"

pip3 install "playwright>=1.40.0" || \
  echo "    ⚠️   playwright install failed (optional — only needed for guides 038-041)"

echo "    ✅  Guide packages installed"

# ── 7. Install Playwright browsers ────────────────────────────────────────────
echo ""
echo "→   Step 3/3 — Installing Playwright Chromium browser ..."
playwright install chromium 2>/dev/null && \
  echo "    ✅  Playwright Chromium installed" || \
  echo "    ⚠️   Playwright browser install failed — run manually later:\n    playwright install chromium"

# ── 8. Show what was installed ─────────────────────────────────────────────────
echo ""
echo "=== Installed package versions ==="
pip3 show strands-agents bedrock-agentcore boto3 aws-cdk-lib 2>/dev/null | \
  grep -E "^Name:|^Version:" | \
  paste - - | \
  awk '{printf "  %-30s %s\n", $2, $4}'

# ── 9. Done ────────────────────────────────────────────────────────────────────
echo ""
echo "=== Setup complete! ✅ ==="
echo ""
echo "Activate the environment at the start of every session:"
echo ""
echo "    source .venv/bin/activate"
echo ""
echo "Then verify everything is ready:"
echo ""
echo "    cd 00-foundations/001-prerequisites"
echo "    python3 verify_setup.py"
echo ""
echo "Run your first agent:"
echo ""
echo "    cd 00-foundations/003-local-agent-strands"
echo "    python3 Source/app/agent.py"
echo ""
