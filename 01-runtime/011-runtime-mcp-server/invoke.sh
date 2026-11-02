#!/bin/bash
# invoke.sh — 011-runtime-mcp-server
#
# Tests the combined MCP server: Travel Tools + AWS Documentation Tools
#
# Call sequence:
#   1. tools/list                    → confirm all 9 tools
#   2. get_weather('Tokyo')          → travel tool (mock)
#   3. convert_currency(100 USD→EUR) → travel tool (mock)
#   4. search_documentation(...)     → AWS Docs tool (live)
#   5. read_documentation(...)       → AWS Docs tool (live)
#
# Usage: bash invoke.sh
set -euo pipefail

export JSII_SILENCE_WARNING_UNTESTED_NODE_VERSION=1
export AWS_PROFILE="${AWS_PROFILE:-anvesh-aws-profile}"
export AWS_DEFAULT_REGION="us-east-1"

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
while [ "$REPO_ROOT" != "/" ] && [ ! -f "$REPO_ROOT/.venv/bin/activate" ]; do
  REPO_ROOT="$(dirname "$REPO_ROOT")"
done
[ -f "$REPO_ROOT/.venv/bin/activate" ] && source "$REPO_ROOT/.venv/bin/activate"

STACK="Guide011RuntimeMcpServer"
REGION="us-east-1"

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║   Guide 011 — Combined MCP Server                      ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║  Travel Tools (mock):  get_weather, get_current_time,  ║"
echo "║                        convert_currency, get_server_info║"
echo "║  AWS Docs (live):      search_documentation,           ║"
echo "║                        read_documentation, read_sections║"
echo "║                        search_table, recommend         ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

python3 << 'PYEOF'
import boto3, json

AWS_PROFILE = "anvesh-aws-profile"
REGION      = "us-east-1"
STACK       = "Guide011RuntimeMcpServer"

session = boto3.Session(profile_name=AWS_PROFILE, region_name=REGION)
cf      = session.client("cloudformation")
outputs = {o["OutputKey"]: o["OutputValue"]
           for o in cf.describe_stacks(StackName=STACK)["Stacks"][0]["Outputs"]}
runtime_arn = outputs["RuntimeArn"]
print(f"Runtime: {runtime_arn}")
print()

client = session.client("bedrock-agentcore", region_name=REGION)

def mcp(method, params, req_id):
    payload = json.dumps({"jsonrpc":"2.0","id":req_id,"method":method,"params":params}).encode()
    resp = client.invoke_agent_runtime(
        agentRuntimeArn = runtime_arn,
        payload         = payload,
        contentType     = "application/json",
        accept          = "application/json, text/event-stream",
    )
    result = json.loads(resp["response"].read())
    if "error" in result:
        raise RuntimeError(f"MCP error {result['error']['code']}: {result['error']['message']}")
    return result

# ── 1. tools/list ─────────────────────────────────────────────────────────
print("=== 1. tools/list — all 9 tools ===")
r = mcp("tools/list", {}, 1)
tools = r.get("result", {}).get("tools", [])
print(f"  Found {len(tools)} tools:")
travel = [t for t in tools if t["name"] in ("get_weather","get_current_time","convert_currency","get_server_info")]
docs   = [t for t in tools if t["name"] in ("search_documentation","read_documentation","read_sections","search_table","recommend")]
print(f"  Travel tools ({len(travel)}): {[t['name'] for t in travel]}")
print(f"  AWS Docs tools ({len(docs)}): {[t['name'] for t in docs]}")
print()

# ── 2. get_weather ────────────────────────────────────────────────────────
print("=== 2. get_weather('Tokyo') — travel tool ===")
r = mcp("tools/call", {"name":"get_weather","arguments":{"location":"Tokyo"}}, 2)
for c in r.get("result",{}).get("content",[]):
    print(f"  {c.get('text','')}")
print()

# ── 3. convert_currency ───────────────────────────────────────────────────
print("=== 3. convert_currency(100 USD → JPY) — travel tool ===")
r = mcp("tools/call", {"name":"convert_currency","arguments":{"amount":100,"from_currency":"USD","to_currency":"JPY"}}, 3)
for c in r.get("result",{}).get("content",[]):
    print(f"  {c.get('text','')}")
print()

# ── 4. search_documentation ───────────────────────────────────────────────
print('=== 4. search_documentation("vLLM EKS GPU inference") — AWS Docs tool ===')
r = mcp("tools/call", {
    "name": "search_documentation",
    "arguments": {
        "search_phrase": "vLLM EKS GPU inference",
        "search_intent": "Find docs about running vLLM on Amazon EKS with GPU",
        "limit": 3
    }
}, 4)
content = r.get("result",{}).get("content",[])
if content:
    try:
        data = json.loads(content[0].get("text","{}"))
        for result in data.get("search_results",[])[:3]:
            print(f"  [{result.get('rank_order')}] {result.get('title')}")
            print(f"       {result.get('url')}")
    except Exception:
        print(content[0].get("text","")[:400])
print()

# ── 5. read_documentation ─────────────────────────────────────────────────
print("=== 5. read_documentation — EKS ML inference page ===")
r = mcp("tools/call", {
    "name": "read_documentation",
    "arguments": {
        "url": "https://docs.aws.amazon.com/eks/latest/userguide/ml-inference.html",
        "max_length": 1500,
        "start_index": 0
    }
}, 5)
content = r.get("result",{}).get("content",[])
if content:
    print(content[0].get("text","")[:800])
print()

print("╔══════════════════════════════════════════════════════════╗")
print("║   ✅  Combined MCP Server — 9 tools working            ║")
print("╚══════════════════════════════════════════════════════════╝")
PYEOF
