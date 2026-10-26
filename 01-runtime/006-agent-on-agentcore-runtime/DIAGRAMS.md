# 006 — Diagram Showcase (All Options)

All diagram types for guide 006 (Agent on AgentCore Runtime).
Compare them side by side and pick your preferred style.

---

## Option 1A — Mermaid `flowchart LR` (Deployment Pipeline)

Shows how code flows from your laptop to a running Runtime agent.
**Best for:** infrastructure pipelines, component relationships.

```mermaid
flowchart LR
    subgraph LOCAL["💻 Your Machine"]
        CODE["agent.py\nDockerfile"]
        CDK["CDK Stack\nmain_stack.py"]
    end

    subgraph CICD["bash deploy.sh"]
        BUILD["docker build\nARM64"]
        PUSH["docker push"]
        DEPLOY["cdk deploy"]
    end

    subgraph AWS["☁️ AWS  us-east-1"]
        ECR["ECR\nRegistry"]
        IAM["IAM Role"]
        CW["CloudWatch\nLogs"]
        RUNTIME["AgentCore\nRuntime"]
    end

    CODE --> BUILD --> PUSH --> ECR
    CDK  --> DEPLOY --> IAM
    DEPLOY --> CW
    ECR -- imageUri --> RUNTIME
    IAM -- roleArn  --> RUNTIME

    style LOCAL   fill:#eef2ff,stroke:#6366f1,color:#312e81
    style AWS     fill:#fff7ed,stroke:#f97316,color:#7c2d12
    style RUNTIME fill:#dcfce7,stroke:#16a34a,color:#14532d,font-weight:bold
```

---

## Option 1B — Mermaid `sequenceDiagram` (Invocation Flow)

Shows the runtime round-trip from user prompt to response.
**Best for:** request/response flows, protocol interactions, agent reasoning loops.

```mermaid
sequenceDiagram
    actor User
    participant R  as AgentCore Runtime
    participant VM as microVM
    participant A  as agent.py
    participant B  as Bedrock Nova Pro

    User  ->> R  : POST /invocations {"prompt":"Weather in Paris?"}
    R     ->> VM : Route → session microVM
    VM    ->> A  : invoke(payload)

    loop Agent reasoning loop
        A ->> B  : converse(messages + tool_schema)
        B -->> A : tool_use → get_weather("Paris")
        A ->> A  : execute get_weather()  → "64°F, Cloudy"
        A ->> B  : converse(tool_result)
        B -->> A : end_turn → "Current weather in Paris..."
    end

    A  -->> VM : {"response": "64°F, Cloudy"}
    VM -->> R  : HTTP 200
    R  -->> User : {"response": "64°F, Cloudy"}
```

---

## Option 1C — Mermaid `flowchart TB` (Session Isolation)

Shows the microVM-per-session model.
**Best for:** multi-user isolation, parallel execution, state boundaries.

```mermaid
flowchart TB
    U1["👤 Alice"] & U2["👤 Bob"] & U3["👤 Carol"]

    subgraph RT["AgentCore Runtime"]
        R["Session Router\n(by session-id)"]
        subgraph M1["microVM A  —  isolated"]
            A1["agent.py"] --- S1["state: Alice's context"]
        end
        subgraph M2["microVM B  —  isolated"]
            A2["agent.py"] --- S2["state: Bob's context"]
        end
        subgraph M3["microVM C  —  isolated"]
            A3["agent.py"] --- S3["state: Carol's context"]
        end
    end

    BED["☁️ Bedrock  Nova Pro"]

    U1 & U2 & U3 --> R
    R --> M1 & M2 & M3
    A1 & A2 & A3 --> BED

    style M1  fill:#dcfce7,stroke:#16a34a
    style M2  fill:#dbeafe,stroke:#2563eb
    style M3  fill:#fef9c3,stroke:#ca8a04
    style RT  fill:#f8fafc,stroke:#94a3b8
    style BED fill:#ff9900,color:#fff,stroke:#b45309
```

---

## Option 2 — Mermaid `block` (System Layer Overview)

Shows the system in layered blocks — local → deploy → cloud → execution → model.
**Best for:** high-level architecture overviews at the top of a README.

```mermaid
block-beta
    columns 3

    block:LOCAL:1
        L1["💻 Your Machine"]
        L2["agent.py + Dockerfile"]
        L3["CDK Stack  Infra/"]
    end

    ARROW1<["  bash deploy.sh  "]>(right)

    block:AWS:1
        A1["☁️ AWS  us-east-1"]
        A2["ECR  ·  IAM  ·  CloudWatch"]
        A3["AgentCore Runtime"]
    end

    ARROW2<["POST /invocations"]>(down)

    block:EXEC:3
        E1["microVM — Alice"]
        E2["microVM — Bob"]
        E3["microVM — Carol"]
    end

    ARROW3<["converse()"]>(down)

    block:MODEL:3
        M1["Amazon Bedrock  Nova Pro"]
        M2["get_weather()"]
        M3["get_current_time()"]
    end
```

---

## Option 3 — Mermaid `C4Context` (Architecture View)

C4 model system context — shows actors, system boundaries, and external dependencies.
**Best for:** enterprise documentation, architecture review boards.

```mermaid
C4Context
    title System Context — 006 AgentCore Runtime

    Person(user, "End User", "Sends prompts via curl / SDK / app")

    System_Boundary(agentcore, "Amazon Bedrock AgentCore") {
        System(runtime,  "AgentCore Runtime",  "Manages microVMs, session isolation, auth")
        System(ecr,      "Amazon ECR",         "Stores ARM64 container image")
        System(iam,      "IAM Role",            "Execution permissions for the agent")
        System(cw,       "CloudWatch",          "Logs, metrics, traces")
    }

    System_Ext(bedrock, "Amazon Bedrock",      "Foundation model — Nova Pro")
    System_Ext(dev,     "Developer Machine",   "Runs bash deploy.sh → CDK")

    Rel(user,    runtime, "POST /invocations", "HTTPS / SigV4")
    Rel(runtime, bedrock, "InvokeModel",       "HTTPS / SigV4")
    Rel(dev,     ecr,     "docker push",       "HTTPS")
    Rel(dev,     runtime, "cdk deploy → CfnRuntime", "AWS API")
    Rel(runtime, cw,      "emits logs + traces", "OTEL")
```

---

## Option 4 — Mermaid `stateDiagram-v2` (Lifecycle)

Shows state transitions from local dev → deploy → running → destroyed.
**Best for:** session lifecycle, async workflows, state machines.

```mermaid
stateDiagram-v2
    direction LR

    [*] --> LocalDev : bash dev.sh

    state LocalDev {
        [*]    --> Running    : uvicorn :8080
        Running --> HotReload : file saved
        HotReload --> Running
    }

    LocalDev --> Deploying : bash deploy.sh

    state Deploying {
        [*]         --> BuildImage : docker build
        BuildImage  --> PushECR    : docker push
        PushECR     --> CDKDeploy  : cdk deploy
        CDKDeploy   --> [*]
    }

    Deploying --> Active : Runtime ACTIVE

    state Active {
        [*]        --> Idle       : waiting
        Idle       --> Processing : invoke
        Processing --> ToolExec   : tool_use
        ToolExec   --> Processing : tool_result
        Processing --> Idle       : end_turn
    }

    Active --> Destroyed : bash destroy.sh
    Destroyed --> [*]
```

---

## Option 5 — ASCII / Plain-text Art

Pure text boxes and arrows — renders everywhere: GitHub, terminals, raw text, offline.
**Best for:** terminal-friendly docs, universal compatibility, no rendering dependency.

```
┌──────────────────────────────────────────────────────────────────────┐
│                     006 — AgentCore Runtime                          │
└──────────────────────────────────────────────────────────────────────┘

  DEPLOY                                INVOKE
  ──────                                ──────

  💻 Your Machine                       👤 User
       │                                    │
       │  bash deploy.sh                    │  POST /invocations
       ▼                                    ▼
  ┌──────────┐  imageUri  ┌──────────────────────────────────────┐
  │  Amazon  │───────────▶│         AgentCore Runtime            │
  │   ECR    │            │                                      │
  └──────────┘            │  ┌──────────────┐ ┌──────────────┐  │
                          │  │  microVM A   │ │  microVM B   │  │
  ┌──────────┐  roleArn   │  │  (Alice)     │ │  (Bob)       │  │
  │  IAM     │───────────▶│  │  agent.py    │ │  agent.py    │  │
  │  Role    │            │  └──────┬───────┘ └──────┬───────┘  │
  └──────────┘            └─────────┼────────────────┼──────────┘
                                    │                │
                                    ▼                ▼
                           ┌──────────────────────────────┐
                           │      Amazon Bedrock           │
                           │      Nova Pro                 │
                           │  ┌────────────────────────┐  │
                           │  │   Agent Loop            │  │
                           │  │   1. converse()         │  │
                           │  │   2. tool_use           │  │
                           │  │   3. execute tool       │  │
                           │  │   4. converse()         │  │
                           │  │   5. end_turn → done    │  │
                           │  └────────────────────────┘  │
                           └──────────────────────────────┘
```

---

## Option 6 — HTML `<picture>` + SVG

Full visual control with exported SVG — renders everywhere, dark mode support.
**Best for:** pixel-perfect diagrams, brand-consistent docs.
**Downside:** requires exporting from draw.io / Excalidraw / Lucidchart, and committing SVG files.

```html
<!-- Paste this directly into your README.md -->
<picture>
  <source media="(prefers-color-scheme: dark)"
          srcset="./diagrams/arch-dark.svg">
  <img src="./diagrams/arch-light.svg"
       alt="006 — AgentCore Runtime Architecture"
       width="700">
</picture>
```

> SVG files live in a `diagrams/` folder next to the README.
> Export from [draw.io](https://draw.io), [Excalidraw](https://excalidraw.com),
> or [Lucidchart](https://lucidchart.com) as SVG (not PNG — SVG is crisp at any zoom).

---

## Option 7 — Mermaid `erDiagram` (Resource Map)

Shows how AWS resources relate to each other — like an ER diagram but for infrastructure.
**Best for:** showing what CDK creates and how resources connect.

```mermaid
erDiagram
    DEVELOPER         ||--o{ CDK_STACK : "runs bash deploy.sh"
    CDK_STACK         ||--|| ECR_REPO  : "creates"
    CDK_STACK         ||--|| IAM_ROLE  : "creates"
    CDK_STACK         ||--|| CW_LOGS   : "creates"
    CDK_STACK         ||--|| AGENTCORE_RUNTIME : "creates via CfnRuntime"

    AGENTCORE_RUNTIME ||--o{ MICROV_VM : "spawns per session"
    AGENTCORE_RUNTIME ||--|| ECR_REPO  : "pulls image from"
    AGENTCORE_RUNTIME ||--|| IAM_ROLE  : "assumes"
    AGENTCORE_RUNTIME ||--|| CW_LOGS   : "writes logs to"

    MICROV_VM         ||--|| AGENT_PY  : "runs"
    AGENT_PY          ||--o{ TOOL      : "calls"
    AGENT_PY          ||--|| BEDROCK   : "calls converse()"

    ECR_REPO {
        string platform  "linux/arm64"
        string tag       "latest"
    }
    IAM_ROLE {
        string principal "bedrock-agentcore.amazonaws.com"
        string policy    "bedrock:InvokeModel"
    }
    AGENTCORE_RUNTIME {
        string name        "006-agent-on-agentcore-runtime"
        string networkMode "PUBLIC"
        string modelId     "us.amazon.nova-pro-v1:0"
    }
```

---

## Option 8 — Mermaid `mindmap` (Concepts at a Glance)

Shows all topics covered in the guide as a visual TOC.
**Best for:** quick orientation, study guides, concept maps.

```mermaid
mindmap
  root((006\nAgentCore\nRuntime))
    Deploy
      bash deploy.sh
      CDK CfnRuntime
      Docker ARM64 → ECR
      IAM execution role
    Local Dev
      bash dev.sh
      agentcore dev
      Hot reload
      bash invoke-dev.sh
    Runtime Concepts
      microVM per session
      Session isolation
      8-hour max runtime
      SigV4 auth built-in
    Agent Code
      BedrockAgentCoreApp
      @app.entrypoint
      Strands Agent
      get_weather tool
      get_current_time tool
    Cleanup
      bash destroy.sh
      Removes Runtime
      Removes ECR + IAM
```

---

## Comparison Table

| # | Type | GitHub renders? | Extra tooling? | Best for |
|---|------|:-:|:-:|---|
| 1A | `flowchart LR` | ✅ | None | Deployment pipelines, component maps |
| 1B | `sequenceDiagram` | ✅ | None | Request flows, agent reasoning loops |
| 1C | `flowchart TB` | ✅ | None | Isolation, parallel components |
| 2  | `block`          | ✅ | None | Layered system overview |
| 3  | `C4Context`      | ✅ | None | Enterprise architecture docs |
| 4  | `stateDiagram-v2`| ✅ | None | Lifecycle, state machines |
| 5  | ASCII art        | ✅ everywhere | None | Terminal-friendly, universal |
| 6  | HTML + SVG       | ✅ | draw.io / Excalidraw | Pixel-perfect, branded |
| 7  | `erDiagram`      | ✅ | None | Resource relationships |
| 8  | `mindmap`        | ✅ | None | Guide concepts at a glance |

---

## Recommended Combination (adopted across all 66 guides)

1. **Option 1A `flowchart LR`** — Architecture section, shows the deployment + component view
2. **Option 1B `sequenceDiagram`** — Invocation Flow section, shows what happens at runtime
3. **Option 8 `mindmap`** — Guide Overview section, visual concept map

All three are Mermaid, render natively on GitHub, and require zero extra tooling.
