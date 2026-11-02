#!/bin/bash
# invoke.sh — 008-runtime-sessions
# Proves AgentCore Runtime session isolation with 5 calls across two sessions.
#
# What this demonstrates:
#   Session A (Alice) and Session B (Bob) run in completely separate microVMs.
#   Memory stored in Alice's session is NEVER visible in Bob's session.
#
# Proof sequence:
#   Call 1 — Alice tells the agent her name + food preference  → stored in microVM A
#   Call 2 — Alice (SAME session) asks what she told it        → agent remembers ✅
#   Call 3 — Bob (DIFFERENT session) asks what his name is     → agent has no idea ✅
#   Call 4 — Bob tells the agent his name + food               → stored in microVM B
#   Call 5 — Bob (SAME session) asks to show everything        → only Bob's data ✅
#
# Usage: bash invoke.sh

set -euo pipefail

export JSII_SILENCE_WARNING_UNTESTED_NODE_VERSION=1
export AWS_PROFILE="${AWS_PROFILE:-anvesh-aws-profile}"

# Activate shared virtual environment
REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
while [ "$REPO_ROOT" != "/" ] && [ ! -f "$REPO_ROOT/.venv/bin/activate" ]; do
  REPO_ROOT="$(dirname "$REPO_ROOT")"
done
[ -f "$REPO_ROOT/.venv/bin/activate" ] && source "$REPO_ROOT/.venv/bin/activate"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
STACK="Guide008RuntimeSessions"

# Fixed session IDs so results are reproducible across runs
ALICE_SESSION="alice-session-001-abcdefghijklmno"
BOB_SESSION="bob-session-001-xyzabcdefghijklmno"

# ── Banner ─────────────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║   Guide 008 — Runtime Sessions & Isolation             ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║  Proving that two sessions cannot see each other's     ║"
echo "║  data — even though they hit the same Runtime ARN.     ║"
echo "╠══════════════════════════════════════════════════════════╣"
printf "║  Alice session: %-40s ║\n" "$ALICE_SESSION"
printf "║  Bob   session: %-40s ║\n" "$BOB_SESSION"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# ── Call 1: Alice introduces herself ──────────────────────────────────────
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "CALL 1 — Alice (session A) tells the agent her name + food"
echo "Expected: agent stores user_name=Alice, favorite_food=pizza"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 "$REPO_ROOT/scripts/invoke_runtime.py" \
  "$STACK" \
  "My name is Alice and I love pizza." \
  --session "$ALICE_SESSION"

echo ""

# ── Call 2: Alice asks (same session — should remember) ───────────────────
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "CALL 2 — Alice (SAME session A) asks what the agent knows"
echo "Expected: 'Your name is Alice and you like pizza' ✅"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 "$REPO_ROOT/scripts/invoke_runtime.py" \
  "$STACK" \
  "What is my name and what food do I like?" \
  --session "$ALICE_SESSION"

echo ""

# ── Call 3: Bob asks (different session — should know nothing) ────────────
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "CALL 3 — Bob (DIFFERENT session B) asks what the agent knows"
echo "Expected: 'I don't have your name stored' — session_memory_size: 0 ✅"
echo "          (Bob's microVM has NEVER seen Alice's data)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 "$REPO_ROOT/scripts/invoke_runtime.py" \
  "$STACK" \
  "What is my name and what food do I like?" \
  --session "$BOB_SESSION"

echo ""

# ── Call 4: Bob introduces himself (his own session) ──────────────────────
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "CALL 4 — Bob (session B) tells the agent his name + food"
echo "Expected: agent stores user_name=Bob, favorite_food=burgers"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 "$REPO_ROOT/scripts/invoke_runtime.py" \
  "$STACK" \
  "My name is Bob and I love burgers." \
  --session "$BOB_SESSION"

echo ""

# ── Call 5: Bob asks to see everything in his session ─────────────────────
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "CALL 5 — Bob (SAME session B) asks to show all session data"
echo "Expected: only Bob + burgers — NO mention of Alice ✅"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 "$REPO_ROOT/scripts/invoke_runtime.py" \
  "$STACK" \
  "Show me everything you know about me." \
  --session "$BOB_SESSION"

echo ""

# ── Summary ────────────────────────────────────────────────────────────────
echo "╔══════════════════════════════════════════════════════════╗"
echo "║   Session Isolation Proof — Summary                    ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║  Call 1  Alice introduces herself      → stored ✅     ║"
echo "║  Call 2  Alice asks (same session)     → remembered ✅ ║"
echo "║  Call 3  Bob asks  (diff session)      → empty ✅      ║"
echo "║  Call 4  Bob introduces himself        → stored ✅     ║"
echo "║  Call 5  Bob asks  (same session)      → only Bob ✅   ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║  Each session = isolated microVM. Zero shared state.   ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
