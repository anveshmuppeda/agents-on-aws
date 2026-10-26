#!/usr/bin/env python3
"""CDK App for 000-common-infra — deploy this ONCE before any guide."""

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
        "used by all 66 guides. Deploy once, reuse everywhere."
    ),
    tags={
        "Project": "agents-on-aws",
        "Guide":   "000-common-infra",
        "Purpose": "shared-infrastructure",
    },
)

app.synth()
