#!/usr/bin/env python3
"""CDK app for 006-agent-on-agentcore-runtime"""
import os
import aws_cdk as cdk
from stacks.main_stack import MainStack

app = cdk.App()
MainStack(
    app,
    "Guide006AgentOnAgentcoreRuntime",
    env=cdk.Environment(
        account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
        region="us-east-1",
    ),
    description="006-agent-on-agentcore-runtime",
    tags={"Project": "agentcore-handson", "Guide": "006-agent-on-agentcore-runtime"},
)
app.synth()
