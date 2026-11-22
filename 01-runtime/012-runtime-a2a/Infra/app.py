#!/usr/bin/env python3
"""CDK app for 012-runtime-a2a"""
import os
import aws_cdk as cdk
from stacks.main_stack import MainStack

app = cdk.App()
MainStack(
    app,
    "Guide012RuntimeA2A",
    env=cdk.Environment(
        account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
        region="us-east-1",
    ),
    description="012-runtime-a2a",
    tags={"Project": "agentcore-handson", "Guide": "012-runtime-a2a"},
)
app.synth()
