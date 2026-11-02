#!/usr/bin/env python3
"""CDK app for 010-runtime-any-model"""
import os
import aws_cdk as cdk
from stacks.main_stack import MainStack

app = cdk.App()
MainStack(
    app,
    "Guide010RuntimeAnyModel",
    env=cdk.Environment(
        account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
        region="us-east-1",
    ),
    description="010-runtime-any-model",
    tags={"Project": "agentcore-handson", "Guide": "010-runtime-any-model"},
)
app.synth()
