# Contributing to Agents on AWS

Thank you for your interest in contributing! This repo is a community-driven hands-on guide to building AI agents on AWS. Every contribution — whether fixing a typo, improving an example, or adding a brand new guide — makes this resource better for everyone.

---

## Table of Contents

- [Types of Contributions](#types-of-contributions)
- [Before You Start](#before-you-start)
- [Adding a New Guide](#adding-a-new-guide)
  - [Guide Requirements](#guide-requirements)
  - [Standard Structure](#standard-structure)
  - [CDK Requirements](#cdk-requirements)
  - [README Requirements](#readme-requirements)
  - [Shell Script Requirements](#shell-script-requirements)
- [Improving an Existing Guide](#improving-an-existing-guide)
- [Development Workflow](#development-workflow)
- [Submitting a Pull Request](#submitting-a-pull-request)
- [PR Checklist](#pr-checklist)
- [Style Guide](#style-guide)
- [Getting Help](#getting-help)

---

## Types of Contributions

| Type | Description |
|------|-------------|
| 🐛 **Bug fix** | A guide's deploy.sh fails, a CDK stack has an error, a link is broken |
| 📝 **Content improvement** | Clearer explanation, better code comments, updated cost estimate |
| 🆕 **New guide** | A self-contained guide for an AgentCore feature not yet covered |
| 🔗 **New blog post** | Add your Medium/Dev.to article about AgentCore to the README blog table |
| 🌐 **Translation** | Translate a guide's README to another language |
| 🎨 **Diagram improvement** | Better Mermaid diagrams for an existing guide |

---

## Before You Start

1. **Check existing guides** — browse the [full guide list](./README.md#-all-66-guides) to avoid duplicating work
2. **Check open issues** — your idea may already be tracked in [Issues](https://github.com/anveshmuppeda/agents-on-aws/issues)
3. **Open an issue first** — for new guides, [propose the guide](https://github.com/anveshmuppeda/agents-on-aws/issues/new?template=new_guide.md) before writing code to get early feedback
4. **Fork the repo** — work on your fork, then open a PR into `main`

---

## Adding a New Guide

New guides are the highest-value contribution. Here's exactly what a guide needs.

### Guide Requirements

Every guide must be:

- ✅ **Self-contained** — no dependency on another guide's deployed resources
- ✅ **Runnable** — `bash deploy.sh` + `bash invoke.sh` + `bash destroy.sh` must all work end-to-end
- ✅ **CDK-first** — all AWS resources created via CDK (no CLI-only deployments)
- ✅ **Cost-aware** — README includes a `## Cost Estimate` section
- ✅ **Clean teardown** — `bash destroy.sh` removes everything; no orphaned resources
- ✅ **Diagrammed** — README has all 3 Mermaid diagrams (flowchart + sequenceDiagram + mindmap)
- ✅ **Documented** — README follows the [template](#readme-requirements)

### Standard Structure

Every guide lives inside its module folder and follows this exact layout:

```
MM-module/NNN-guide-name/
├── README.md                  ← Full guide documentation
├── deploy.sh                  ← Deploy all AWS resources
├── invoke.sh                  ← Invoke the deployed agent
├── invoke-dev.sh              ← Invoke the local dev server
├── dev.sh                     ← Start local dev server (hot reload)
├── destroy.sh                 ← Tear down all AWS resources
├── Source/
│   ├── app/
│   │   ├── __init__.py
│   │   └── agent.py           ← Agent source code
│   ├── requirements.txt
│   └── Dockerfile             ← ARM64, port 8080
└── Infra/
    ├── app.py                 ← CDK app entry point
    ├── cdk.json               ← {"app": "python3 app.py"}
    ├── requirements.txt       ← aws-cdk-lib>=2.243.0, constructs>=10.0.0
    └── stacks/
        ├── __init__.py
        └── main_stack.py      ← CDK stack using aws_bedrockagentcore constructs
```

See [`002-project-template`](./00-foundations/002-project-template/) for a working scaffold.

### CDK Requirements

All infrastructure must be defined in CDK. We use the `aws_bedrockagentcore` L1 constructs from `aws-cdk-lib>=2.243.0`.

**AgentCore resources available as CDK L1 constructs:**

| Resource | CDK Construct |
|----------|--------------|
| Runtime agent | `agentcore.CfnRuntime` |
| Memory | `agentcore.CfnMemory` |
| Gateway | `agentcore.CfnGateway` |
| Gateway Target | `agentcore.CfnGatewayTarget` |
| Workload Identity | `agentcore.CfnWorkloadIdentity` |
| OAuth2 Credential Provider | `agentcore.CfnOAuth2CredentialProvider` |
| API Key Credential Provider | `agentcore.CfnApiKeyCredentialProvider` |
| Browser (custom) | `agentcore.CfnBrowserCustom` |
| Code Interpreter | `agentcore.CfnCodeInterpreterCustom` |
| Policy Engine | `agentcore.CfnPolicyEngine` |
| Policy | `agentcore.CfnPolicy` |
| Evaluator | `agentcore.CfnEvaluator` |

**Exception:** Harness and Registry do not have CloudFormation support yet. These use the AgentCore CLI (`agentcore harness create`, `agentcore registry create`). Document this clearly in the guide's `deploy.sh`.

### README Requirements

Every guide README must have all of these sections in this order:

```markdown
# NNN — Guide Title

## What
One concise sentence describing what gets built.

## Why
Why this feature matters. When would a real developer use it.

## Architecture

### Component Diagram
```
flowchart LR
    ...
```

### Invocation Flow
```
sequenceDiagram
    ...
```

### Guide Overview
```
mindmap
    ...
```

## Prerequisites
- Completed [001-prerequisites](../../00-foundations/001-prerequisites/)
- Any guide-specific requirements

## Steps
### 1. ...
### 2. ...
### 3. ...

## Cost Estimate
**Approximate cost: ~$X.XX/day**
...pricing breakdown...

## Cleanup
```bash
bash destroy.sh
```

## Key Takeaways
- 3–5 bullet points of what was learned

## Next Steps
- Links to 1–3 related guides
```

**Mermaid rules** (applies to all 3 diagrams):
- No Unicode arrows `→` — use `->` in flowchart/sequence
- No `->` inside mindmap nodes — use `:` instead
- No `()` in mindmap leaf nodes — they trigger shape syntax
- No em dashes `—` in node labels — use ` - `
- No smart quotes `''""` — use plain `'"` 

### Shell Script Requirements

All 5 scripts must be present and executable (`chmod +x`). Each script:
- Has `#!/bin/bash` shebang
- Has `set -euo pipefail` for safe execution
- Prints clear progress messages with `echo`
- Uses `GUIDE=`, `STACK=`, `REGION=us-east-1` variables at the top
- Requires no arguments to run

**`deploy.sh`** — must deploy fully with a single `bash deploy.sh`. No manual steps.

**`destroy.sh`** — must prompt for confirmation before deleting. Use:
```bash
read -p "Continue? [y/N] " -n 1 -r
echo ""
[[ $REPLY =~ ^[Yy]$ ]] || { echo "Aborted."; exit 0; }
```

---

## Improving an Existing Guide

For fixes to existing guides:

- **Typo / clarity fix** — open a PR directly, no issue needed
- **Code bug** — open an issue first describing the failure, then a PR with the fix
- **CDK stack improvement** — note what changed and why in the PR description
- **Diagram update** — always validate Mermaid syntax before opening a PR

---

## Development Workflow

```bash
# 1. Fork and clone
git clone https://github.com/YOUR_USERNAME/agents-on-aws.git
cd agents-on-aws

# 2. Create a branch
git checkout -b feature/NNN-your-guide-name

# 3. Build your guide following the template
cp -r 00-foundations/002-project-template MM-module/NNN-your-guide-name
# ... write your guide ...

# 4. Test locally first
cd MM-module/NNN-your-guide-name/Source
agentcore dev                                    # Terminal 1
agentcore invoke --dev '{"prompt": "Hello"}'    # Terminal 2

# 5. Deploy and test on real AWS
bash deploy.sh
bash invoke.sh
bash destroy.sh   # Always clean up

# 6. Commit and push
git add .
git commit -m "feat: add guide NNN-your-guide-name"
git push origin feature/NNN-your-guide-name

# 7. Open a PR on GitHub
```

---

## Submitting a Pull Request

1. **Title format:** `feat: add guide NNN-guide-name` or `fix: guide NNN description`
2. **Fill out the PR template** — every section matters
3. **One guide per PR** — keep PRs focused; multiple small PRs are better than one large one
4. **Link the issue** — use `Closes #123` in the PR description
5. **Be patient** — reviews happen within 48–72 hours

---

## PR Checklist

Before opening a PR, confirm:

```
[ ] bash deploy.sh completes without errors
[ ] bash invoke.sh returns a valid response
[ ] bash destroy.sh removes all resources cleanly
[ ] README has all required sections (What/Why/Architecture/Steps/Cost/Cleanup)
[ ] README has 3 Mermaid diagrams (flowchart + sequenceDiagram + mindmap)
[ ] Mermaid diagrams render without parse errors
[ ] All cross-guide links use ../../NNN- format
[ ] No make references anywhere in the guide
[ ] No Unicode arrows (→) or em dashes (—) inside Mermaid blocks
[ ] agent.py docstring has the correct guide number
[ ] Cost Estimate section is present with realistic numbers
[ ] destroy.sh prompts for confirmation before deleting
[ ] All shell scripts have +x permissions
[ ] Infra/requirements.txt has aws-cdk-lib>=2.243.0
```

---

## Style Guide

### Python (agent code)

- Follow PEP 8
- Docstrings on all tools: description, Args, Returns
- `MODEL_ID = os.environ.get("MODEL_ID", "us.amazon.nova-pro-v1:0")` — always configurable
- Keep agent.py focused — complex logic goes in `tools/`
- All tools use the `@tool` decorator from Strands

### Shell scripts

- Variables at the top: `GUIDE`, `STACK`, `AGENT`, `REGION`
- Echo progress clearly: `echo "Step 1/2 — CDK deploy"`
- Use `--require-approval never` for CDK in deploy scripts
- Never use `set +e` — let errors surface

### CDK (infrastructure)

- One stack per guide — no cross-stack references
- Use `removal_policy=cdk.RemovalPolicy.DESTROY` on all test resources
- Output all resource IDs/ARNs as `cdk.CfnOutput`
- Tag every stack: `tags={"Project": "agents-on-aws", "Guide": guide_name}`

### Naming conventions

| Resource | Pattern | Example |
|----------|---------|---------|
| CDK Stack | `GuideNNNSlugInTitleCase` | `Guide021GatewayLambdaTool` |
| Agent name | `guide-NNN-slug` | `guide-021-gateway-agent` |
| Log group | `/aws/bedrock-agentcore/NNN-slug` | `/aws/bedrock-agentcore/021-gateway-lambda-tool` |

---

## Getting Help

- 💬 **Questions** → [GitHub Discussions](https://github.com/anveshmuppeda/agents-on-aws/discussions)
- 🐛 **Bugs** → [GitHub Issues](https://github.com/anveshmuppeda/agents-on-aws/issues)
- 📧 **Direct** → [muppedaanvesh@gmail.com](mailto:muppedaanvesh@gmail.com)

---

Thank you for contributing! Every guide you add helps the next developer skip hours of frustration. 🙏
