#!/usr/bin/env python3
"""CDK app for 000-common-infra — deploy before guides that use its shared resources."""

import os
import aws_cdk as cdk
from stacks.common_stack import CommonInfraStack

app = cdk.App()

CommonInfraStack(
    app,
    "AgentsOnAwsCommonInfra",
    env=cdk.Environment(
        account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
        region="us-east-1",
    ),
    description=(
        "agents-on-aws: shared IAM roles and SSM parameters "
        "shared by guides that opt in. Deploy once, reuse where applicable."
    ),
    tags={
        "Project": "agents-on-aws",
        "Guide":   "000-common-infra",
        "Purpose": "shared-infrastructure",
    },
)

app.synth()
