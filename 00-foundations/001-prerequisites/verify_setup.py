#!/usr/bin/env python3
"""
Verify all prerequisites for the AgentCore hands-on guides.
Run: python3 verify_setup.py
"""

import subprocess
import sys
import importlib


RESET = "\033[0m"
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BOLD = "\033[1m"

passed = []
failed = []


def check(label: str, fn):
    try:
        result = fn()
        msg = result if isinstance(result, str) else "OK"
        print(f"  {GREEN}✓{RESET} {label}: {msg}")
        passed.append(label)
    except Exception as e:
        print(f"  {RED}✗{RESET} {label}: {e}")
        failed.append(label)


def run(cmd: str) -> str:
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"exit code {result.returncode}")
    return result.stdout.strip()


def check_python():
    v = sys.version_info
    if v.major < 3 or (v.major == 3 and v.minor < 10):
        raise RuntimeError(f"Python 3.10+ required, got {v.major}.{v.minor}")
    return f"{v.major}.{v.minor}.{v.micro}"


def check_node():
    out = run("node --version")
    version = out.lstrip("v")
    major = int(version.split(".")[0])
    if major < 20:
        raise RuntimeError(f"Node 20+ required, got {version}")
    return out


def check_aws_cli():
    out = run("aws --version")
    return out.split()[0]


def check_aws_credentials():
    out = run("aws sts get-caller-identity --query Account --output text --region us-east-1")
    return f"Account {out}"


def check_agentcore_cli():
    import os
    env = os.environ.copy()
    env["JSII_SILENCE_WARNING_UNTESTED_NODE_VERSION"] = "1"
    result = subprocess.run("agentcore --version", shell=True, capture_output=True, text=True, env=env)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"exit code {result.returncode}")
    return result.stdout.strip().split("\n")[0]


def check_cdk():
    # Suppress the JSII Node.js untested-version warning — it's cosmetic,
    # not a real error. CDK still works fine on Node 26.
    import os, re
    env = os.environ.copy()
    env["JSII_SILENCE_WARNING_UNTESTED_NODE_VERSION"] = "1"
    result = subprocess.run("cdk --version", shell=True, capture_output=True, text=True, env=env)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"exit code {result.returncode}")
    version_line = result.stdout.strip().split("\n")[0]
    # Check CDK CLI is new enough to read aws-cdk-lib 2.243+ cloud assembly
    # aws-cdk-lib 2.243+ generates schema 53+, requiring CDK CLI >= 2.1146
    m = re.search(r'(\d+)\.(\d+)', version_line)
    if m:
        major, minor = int(m.group(1)), int(m.group(2))
        if major < 2 or (major == 2 and minor < 1146):
            raise RuntimeError(
                f"{version_line} — too old. Run: npm install -g aws-cdk@latest"
            )
    return version_line


def check_docker():
    out = run("docker --version")
    return out


def check_python_pkg(pkg: str, min_version: str = None):
    def inner():
        # importlib.metadata gives the real installed version
        # even for packages that don't expose __version__
        import importlib.metadata as meta
        pkg_root = pkg.replace("-", "_").split("[")[0]
        # Try the dist name first, then the import name
        for name in [pkg.split("[")[0], pkg_root]:
            try:
                ver = meta.version(name)
                break
            except meta.PackageNotFoundError:
                continue
        else:
            # Fallback: try importing and reading __version__
            mod = importlib.import_module(pkg_root)
            ver = getattr(mod, "__version__", "installed")

        if min_version and ver != "installed":
            try:
                from packaging.version import Version
                if Version(ver) < Version(min_version):
                    raise RuntimeError(f"{ver} < {min_version} required")
            except ImportError:
                pass
        return ver
    return inner


def check_bedrock_model():
    import boto3
    client = boto3.client("bedrock", region_name="us-east-1")
    response = client.list_foundation_models(byOutputModality="TEXT")
    model_ids = [m["modelId"] for m in response["modelSummaries"]]
    target = "amazon.nova-pro-v1:0"
    if not any(target in m for m in model_ids):
        raise RuntimeError(f"{target} not found — check model access in Bedrock console")
    return f"Nova Pro accessible"


print(f"\n{BOLD}AWS Bedrock AgentCore — Prerequisites Check{RESET}\n")

# Check we're inside the repo's .venv
import os
venv = os.environ.get("VIRTUAL_ENV", "")
if ".venv" in venv:
    print(f"  {GREEN}✓{RESET} Virtual env: {venv}")
else:
    print(f"  {YELLOW}⚠{RESET}  Not in .venv — run: source .venv/bin/activate")
    print(f"      (Or run bash setup-env.sh from the repo root first)")
    print()

print(f"{BOLD}System:{RESET}")
check("Python version", check_python)
check("Node.js version", check_node)
check("Docker", check_docker)

print(f"\n{BOLD}AWS:{RESET}")
check("AWS CLI", check_aws_cli)
check("AWS credentials (us-east-1)", check_aws_credentials)
check("CDK CLI", check_cdk)
check("AgentCore CLI", check_agentcore_cli)

print(f"\n{BOLD}Python packages:{RESET}")
check("boto3", check_python_pkg("boto3"))
check("strands (strands-agents)", check_python_pkg("strands-agents", "1.57.2"))
check("bedrock-agentcore", check_python_pkg("bedrock-agentcore", "1.24.0"))
check("aws-cdk-lib (>=2.243.0)", check_python_pkg("aws-cdk-lib", "2.243.0"))

print(f"\n{BOLD}Bedrock model access:{RESET}")
check("Nova Pro model access", check_bedrock_model)

print(f"\n{'─' * 50}")
total = len(passed) + len(failed)
if failed:
    print(f"{RED}{BOLD}Result: {len(failed)}/{total} checks failed{RESET}")
    print(f"\nFailed checks:")
    for f in failed:
        print(f"  {RED}✗{RESET} {f}")
    print(f"\nSee README.md for setup instructions.")
    sys.exit(1)
else:
    print(f"{GREEN}{BOLD}Result: All {total} checks passed! You're ready to go.{RESET}")
    print(f"\nNext step → cd ../003-local-agent-strands && python3 Source/app/agent.py")
