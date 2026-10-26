#!/usr/bin/env python3
"""
CDK App for Guide 005 — Agent on Lambda
"""

import os
import aws_cdk as cdk
from stacks.main_stack import AgentOnLambdaStack

app = cdk.App()

AgentOnLambdaStack(
    app,
    "Guide005AgentOnLambda",
    env=cdk.Environment(
        account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
        region="us-east-1",
    ),
    description="Guide 005: Strands travel agent deployed as a Lambda function + API Gateway",
    tags={
        "Project": "agents-on-aws",
        "Guide":   "005-agent-on-lambda",
    },
)

app.synth()
