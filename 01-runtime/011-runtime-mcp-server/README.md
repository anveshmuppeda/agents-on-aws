# 011 — MCP Server on AgentCore Runtime

## What

Deploy a **Model Context Protocol (MCP) server** to AgentCore Runtime. The server combines four travel tools with five AWS documentation tools that MCP clients can discover and call.

## Why

MCP (Model Context Protocol) is the open standard for connecting agents to tools. Instead of every agent carrying its own tools, you deploy tool servers that **any agent can connect to**. This is composability:

```
MCP Client ──────►  Travel + AWS Docs MCP Server
                    (on AgentCore Runtime)
                    ├── Travel tools (mock data)
                    └── AWS documentation tools (live docs)
```

Benefits:
- One tool server, many consumers — no duplication
- Tools scale independently from agents
- Change tool logic without touching agents
- Runtime gives MCP servers the same isolation and auth as agents

## Architecture

### Component Diagram

```mermaid
flowchart LR
    subgraph SERVER["MCP Server  -  on AgentCore Runtime"]
        MCP["MCPServer (mcp 2.x)
port 8000/mcp"]
        TRAVEL["4 travel tools
weather · time · currency · server info"]
        DOCS["5 AWS documentation tools
search · read · sections · tables · recommend"]
        MCP --> TRAVEL & DOCS
    end
    CLIENT["Any MCP Client
Agent / Inspector"] -- "streamable-HTTP
:8000/mcp" --> MCP
    style SERVER fill:#f0fdf4,stroke:#16a34a
```

### Invocation Flow

```mermaid
sequenceDiagram
    participant C  as MCP Client
    participant S  as MCP Server (Runtime)

    C  ->> S  : initialize()
    S -->> C  : capabilities

    C  ->> S  : tools/list
    S -->> C  : 4 travel tools + 5 AWS documentation tools

    C  ->> S  : tools/call get_weather {"location":"Tokyo"}
    S -->> C  : "79°F, Clear, humidity 55%"

    C  ->> S  : tools/call convert_currency {amount:100, from:USD, to:EUR}
    S -->> C  : "100 USD = 91.74 EUR"
    note over C,S: MCP protocol · streamable-HTTP · stateless_http=True
```

### Guide Overview

```mermaid
mindmap
  root((011
MCP Server
on Runtime))
    MCP Server
      MCPServer (mcp 2.x)
      @mcp.tool decorator
      streamable-HTTP
      Port 8000 not 8080
    Tools Exposed
      get_weather
      get_current_time
      convert_currency
      get_server_info
      AWS documentation tools (5)
    vs Agent Guides
      No LLM here
      Pure tool server
      Path /mcp not /invocations
    Testing
      test_mcp_client.py
      npx @modelcontextprotocol/inspector
      invoke.sh tests deployed server
```

---
## Key Differences from Agent Guides

| Previous guides | This guide |
|---|---|
| Runtime hosts an agent | Runtime hosts a TOOL SERVER |
| Container runs on port 8080 | Container runs on port 8000 |
| Path: `/invocations` | Path: `/mcp` |
| Calls Bedrock | No LLM — pure functions |

## Steps

### 1. Test locally

```bash
cd 011-runtime-mcp-server
pip3 install -r Source/requirements.txt

# Terminal 1: start the MCP server
python3 Source/app/agent.py

# Terminal 2: test with the MCP client
python3 Source/test_mcp_client.py
```

### 2. Test with MCP Inspector

```bash
npx @modelcontextprotocol/inspector http://localhost:8000/mcp
```

### 3. Deploy to AgentCore Runtime

```bash
bash deploy.sh
```

This deploys the MCP server as a Runtime agent with the `MCP` protocol.

### 4. Test the deployed MCP server

```bash
bash invoke.sh
```

The script lists all nine tools and calls travel and AWS documentation tools through the AgentCore Runtime endpoint. The local MCP client example is in [`Source/test_mcp_client.py`](./Source/test_mcp_client.py).


## Cost Estimate

**Approximate cost: ~$0.05–$0.10/day**

Runtime (MCP server): ~$0.0000267/session-sec. Each connected client starts a session.

> For current pricing, see the [AgentCore pricing page](https://aws.amazon.com/bedrock/agentcore/pricing/) and [Bedrock pricing](https://aws.amazon.com/bedrock/pricing/). Always run `bash destroy.sh` after testing to stop billing.
## Cleanup

```bash
bash destroy.sh
```

## Key Takeaways

- AgentCore Runtime hosts MCP servers, not just agents
- MCP servers use port 8000 and path `/mcp` (not 8080/invocations)
- `MCPServer` from `mcp` 2.x + `@mcp.tool()` is the server-side pattern
- `ClientSession` + `streamablehttp_client` is the local MCP client pattern
- MCP enables tool reuse across multiple agents

## Next Steps

- [`012-runtime-a2a`](../../012-runtime-a2a/) — Agent-to-Agent protocol
- [`021-gateway-lambda-tool`](../../021-gateway-lambda-tool/) — Expose tools via AgentCore Gateway
