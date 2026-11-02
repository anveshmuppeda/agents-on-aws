#!/usr/bin/env python3
"""CDK app for 008-runtime-sessions"""
import os
import aws_cdk as cdk
from stacks.main_stack import MainStack

app = cdk.App()
MainStack(
    app,
    "Guide008RuntimeSessions",
    env=cdk.Environment(
        account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
        region="us-east-1",
    ),
    description="008-runtime-sessions",
    tags={"Project": "agentcore-handson", "Guide": "008-runtime-sessions"},
)
app.synth()
