#!/usr/bin/env python3
"""CDK app for 011-runtime-mcp-server"""
import os
import aws_cdk as cdk
from stacks.main_stack import MainStack

app = cdk.App()
MainStack(
    app,
    "Guide011RuntimeMcpServer",
    env=cdk.Environment(
        account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
        region="us-east-1",
    ),
    description="011-runtime-mcp-server",
    tags={"Project": "agentcore-handson", "Guide": "011-runtime-mcp-server"},
)
app.synth()
