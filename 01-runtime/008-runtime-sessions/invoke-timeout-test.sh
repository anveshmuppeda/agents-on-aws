#!/bin/bash
# invoke-timeout-test.sh — 008-runtime-sessions
#
# Tests the 60-second idle timeout behaviour:
#   Call 1: Tell the agent your name              → stored in microVM
#   Call 2: Ask your name immediately (~5s later) → agent remembers ✅
#   [Wait 75 seconds — microVM idle timeout expires, microVM terminated]
#   Call 3: Ask your name again                   → agent has no idea ❌
#
# Expected outcome proves: in-memory state is LOST when microVM is stopped.
# For durable memory across sessions, use AgentCore Memory (Guide 016).

set -euo pipefail

export JSII_SILENCE_WARNING_UNTESTED_NODE_VERSION=1
export AWS_PROFILE="${AWS_PROFILE:-anvesh-aws-profile}"

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
while [ "$REPO_ROOT" != "/" ] && [ ! -f "$REPO_ROOT/.venv/bin/activate" ]; do
  REPO_ROOT="$(dirname "$REPO_ROOT")"
done
[ -f "$REPO_ROOT/.venv/bin/activate" ] && source "$REPO_ROOT/.venv/bin/activate"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
STACK="Guide008RuntimeSessions"
SESSION="timeout-test-session-$(date +%s)-abcdefg"

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║   Guide 008 — Idle Timeout Test (60s)                  ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║  idleRuntimeSessionTimeout = 60 seconds                ║"
echo "║                                                          ║"
echo "║  Test plan:                                              ║"
echo "║  Call 1 → tell agent your name                          ║"
echo "║  Call 2 → ask immediately (~5s)  → should remember      ║"
echo "║  Wait   → 75 seconds             → microVM terminates   ║"
echo "║  Call 3 → ask again              → should NOT remember  ║"
echo "╚══════════════════════════════════════════════════════════╝"
printf "\n  Session ID: %s\n\n" "$SESSION"

# ── Call 1: Store the name ──────────────────────────────────────────────────
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "CALL 1 — Tell agent: 'My name is Anvesh'"
echo "         [$(date '+%H:%M:%S')] — microVM starts, stores name"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 "$REPO_ROOT/scripts/invoke_runtime.py" \
  "$STACK" \
  "My name is Anvesh." \
  --session "$SESSION"

echo ""

# ── Call 2: Ask immediately ─────────────────────────────────────────────────
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "CALL 2 — Ask immediately: 'What is my name?'"
echo "         [$(date '+%H:%M:%S')] — same microVM, should remember ✅"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 "$REPO_ROOT/scripts/invoke_runtime.py" \
  "$STACK" \
  "What is my name?" \
  --session "$SESSION"

echo ""

# ── Wait 75 seconds ─────────────────────────────────────────────────────────
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "WAITING 75 seconds..."
echo "  idleRuntimeSessionTimeout = 60s"
echo "  microVM will go idle → terminate → memory sanitized"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

for i in $(seq 75 -5 5); do
  printf "  [$(date '+%H:%M:%S')] %2ds remaining...\n" "$i"
  sleep 5
done
echo "  [$(date '+%H:%M:%S')] 75s elapsed — microVM should be terminated"
echo ""

# ── Call 3: Ask after timeout ───────────────────────────────────────────────
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "CALL 3 — Ask after timeout: 'What is my name?'"
echo "         [$(date '+%H:%M:%S')] — NEW microVM, name should be GONE ❌"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 "$REPO_ROOT/scripts/invoke_runtime.py" \
  "$STACK" \
  "What is my name?" \
  --session "$SESSION"

echo ""

# ── Summary ─────────────────────────────────────────────────────────────────
echo "╔══════════════════════════════════════════════════════════╗"
echo "║   Timeout Test — Summary                               ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║  Call 1  'My name is Anvesh'     → stored in microVM   ║"
echo "║  Call 2  'What is my name?' (5s) → remembered ✅       ║"
echo "║  [waited 75s — idle timeout fired — microVM gone]       ║"
echo "║  Call 3  'What is my name?' (75s)→ FORGOTTEN ❌        ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║  In-memory state = ephemeral. Lives only while          ║"
echo "║  the microVM is alive (idle timeout: 60s in this demo). ║"
echo "║  For durable memory → Guide 016: AgentCore Memory       ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
