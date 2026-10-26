#!/usr/bin/env python3
"""CDK app for 007-harness-vs-runtime"""
import os
import aws_cdk as cdk
from stacks.main_stack import MainStack

app = cdk.App()
MainStack(
    app,
    "Guide007HarnessVsRuntime",
    env=cdk.Environment(
        account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
        region="us-east-1",
    ),
    description="007-harness-vs-runtime",
    tags={"Project": "agentcore-handson", "Guide": "007-harness-vs-runtime"},
)
app.synth()
