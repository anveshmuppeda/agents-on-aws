#!/usr/bin/env python3
"""CDK app for 009-runtime-langgraph"""
import os
import aws_cdk as cdk
from stacks.main_stack import MainStack

app = cdk.App()
MainStack(
    app,
    "Guide009RuntimeLanggraph",
    env=cdk.Environment(
        account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
        region="us-east-1",
    ),
    description="009-runtime-langgraph",
    tags={"Project": "agentcore-handson", "Guide": "009-runtime-langgraph"},
)
app.synth()
