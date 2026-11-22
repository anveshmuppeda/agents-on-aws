# 002 — Project Template

This guide defines the **default structure for deployable guides** in this repo. Guide types differ: use only the files and workflow needed for the feature, and follow the protocol-specific notes below. Use this as a reference when contributing a guide or adapting code to your own project.

---

## Directory Layout

```
NNN-guide-name/
├── README.md        ← What, Why, Steps, Cleanup, Cost Estimate
├── deploy.sh        ← Deploy all AWS resources (CDK + AgentCore)
├── invoke.sh        ← Invoke the deployed agent
├── invoke-dev.sh    ← Invoke the local dev server
├── dev.sh           ← Start the AgentCore local dev server (hot reload)
├── destroy.sh       ← Tear down all AWS resources
├── Source/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── agent.py           ← Main agent entry point
│   │   └── tools/
│   │       ├── __init__.py
│   │       └── my_tool.py     ← Individual tool implementations
│   ├── requirements.txt
│   └── Dockerfile             ← (Runtime guides only)
└── Infra/
    ├── app.py                 ← CDK app entry point
    ├── cdk.json
    ├── requirements.txt
    └── stacks/
        ├── __init__.py
        └── main_stack.py      ← The CDK stack
```

---

## Shell Scripts

Deployable guides use plain shell scripts where applicable — no Make required:

| Script | Command | Description |
|--------|---------|-------------|
| `deploy.sh` | `bash deploy.sh` | Deploy all AWS resources (CDK + AgentCore) |
| `invoke.sh` | `bash invoke.sh` | Invoke the deployed agent with a test prompt |
| `invoke-dev.sh` | `bash invoke-dev.sh` | Invoke the local dev server (requires `dev.sh` running) |
| `dev.sh` | `bash dev.sh` | Start AgentCore local dev server with hot reload |
| `destroy.sh` | `bash destroy.sh` | Tear down all AWS resources |

**Install dependencies manually (one-time):**
```bash
pip3 install -r Source/requirements.txt   # agent runtime deps
pip3 install -r Infra/requirements.txt    # CDK deps
```

**Clean up local build artifacts:**
```bash
rm -rf Infra/cdk.out __pycache__ .pytest_cache
```

Runtime guide `invoke.sh` scripts may reuse the repository-level [`scripts/invoke_runtime.py`](../../scripts/invoke_runtime.py) helper for CloudFormation output lookup and boto3 invocation.

---

## CDK Stack Pattern (for CDK-backed deployment guides)

CDK-backed guides typically follow this pattern; local-only and CLI-managed guides may not have a CDK stack:

```python
# Infra/stacks/main_stack.py
import aws_cdk as cdk
from constructs import Construct

class MainStack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        # Resources defined here
```

```python
# Infra/app.py
import aws_cdk as cdk
from stacks.main_stack import MainStack

app = cdk.App()
MainStack(
    app,
    "GuideNNN",           # Stack name — change per guide
    env=cdk.Environment(
        account=app.node.try_get_context("account") or os.environ["CDK_DEFAULT_ACCOUNT"],
        region="us-east-1",
    ),
)
app.synth()
```

```json
// Infra/cdk.json
{
  "app": "python3 app.py"
}
```

---

## AgentCore Runtime Agent Entry Point Pattern

Runtime guides that host an agent typically wrap it with `BedrockAgentCoreApp`. This pattern does not apply to MCP servers, Lambda handlers, Harness configuration, or local-only guides:

```python
# Source/app/agent.py
from strands import Agent, tool
from bedrock_agentcore import BedrockAgentCoreApp

@tool
def my_tool(input: str) -> str:
    """Tool description shown to the model."""
    return f"Result for: {input}"

app = BedrockAgentCoreApp()

@app.entrypoint
def invoke(payload: dict) -> dict:
    agent = Agent(
        model="us.amazon.nova-pro-v1:0",
        system_prompt="You are a helpful assistant.",
        tools=[my_tool],
    )
    response = agent(payload.get("prompt", "Hello"))
    return {"response": str(response)}

if __name__ == "__main__":
    app.run()   # Starts uvicorn on port 8080
```

---

## README Template

Deployable guide READMEs should explain the guide-specific workflow. Use this structure as a starting point and omit sections that do not apply:

```markdown
# NNN — Guide Title

## What
One sentence.

## Why
Why this feature matters and when you'd use it.

## Architecture

### Component Diagram

```mermaid
flowchart LR
    subgraph EACH["Typical Runtime Agent Guide"]
        direction TB
        SH["deploy.sh  invoke.sh
dev.sh  destroy.sh"]
        SRC["Source/  app/agent.py
Dockerfile  requirements.txt"]
        INFRA["Infra/  app.py  cdk.json
stacks/main_stack.py"]
        README["README.md
What · Why · Steps
Cost · Cleanup"]
    end
    SRC & INFRA -- "bash deploy.sh" --> CLOUD["☁️ AWS Runtime"]
    style EACH fill:#eef2ff,stroke:#6366f1
```

### Invocation Flow

```mermaid
sequenceDiagram
    participant Dev
    note over Dev: Common Runtime-agent workflow  -  adapt for each guide type
    Dev->>Dev: bash dev.sh         (local hot-reload :8080)
    Dev->>Dev: bash invoke-dev.sh  (test locally)
    Dev->>Dev: bash deploy.sh      (CDK -> ECR -> CfnRuntime)
    Dev->>Dev: bash invoke.sh      (test deployed agent)
    Dev->>Dev: bash destroy.sh     (teardown  -  stop billing)
```

### Guide Overview

```mermaid
mindmap
  root((002
Project
Template))
    Shell Scripts
      deploy.sh
      invoke.sh
      invoke-dev.sh
      dev.sh
      destroy.sh
    Source
      app/agent.py
      Dockerfile ARM64
      requirements.txt
    Infra CDK
      app.py entry point
      stacks/main_stack.py
      cdk.json
    README
      What · Why
      Architecture diagrams
      Steps · Cost · Cleanup
```

---
## Prerequisites
Any guide-specific requirements beyond [`001-prerequisites`](../001-prerequisites/).

## Steps
### 1. ...
### 2. ...
### 3. ...

## Test It
How to verify it works.


## Cost Estimate

**Approximate cost: ~$0**

Documentation only. No resources deployed.

> For current pricing, see the [AgentCore pricing page](https://aws.amazon.com/bedrock/agentcore/pricing/) and [Bedrock pricing](https://aws.amazon.com/bedrock/pricing/). Always run `bash destroy.sh` after testing to stop billing.
## Cleanup
`bash destroy.sh` or specific CDK/CLI commands.

## Key Takeaways
3–5 bullet points of what you learned.

## Next Steps
Links to the next guide(s).
```

---

## No Resources Deployed

This guide is documentation-only. Nothing to deploy or destroy.

## Guide-Type Variations

- **Local-only guides** may omit CDK infrastructure and deploy/destroy scripts.
- **Lambda guides** use a Lambda handler and the infrastructure required for Lambda; they do not use `BedrockAgentCoreApp`.
- **AgentCore Runtime agent guides** typically use `BedrockAgentCoreApp` and the `/invocations` endpoint on port 8080.
- **MCP Runtime guides** use an MCP server entry point and the MCP protocol endpoint (for this repo's MCP guide, port 8000 and `/mcp`).
- **Harness guides** may use configuration and AgentCore CLI commands rather than a Docker image or CDK stack.
- **Prerequisite and template guides** may be documentation or setup-script only.
