"""CDK stack for 007-harness-vs-runtime — uses shared role from 000-common-infra."""
import os
import sys
import aws_cdk as cdk
from aws_cdk import (
    aws_ecr_assets as ecr_assets,
    aws_logs as logs,
    aws_bedrockagentcore as agentcore,
)
from constructs import Construct

# ── Shared helpers from 000-common-infra ─────────────────────────────────────
_common_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..',
                             '00-foundations', '000-common-infra', 'Infra', 'stacks')
if _common_path not in sys.path:
    sys.path.insert(0, _common_path)
from common import get_agentcore_role, guide_log_group, to_resource_name, PLATFORM  # noqa: E402

SOURCE_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'Source')
GUIDE = "007-harness-vs-runtime"


class MainStack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Container image — CDK builds and pushes to ECR on cdk deploy
        image = ecr_assets.DockerImageAsset(
            self, "Image",
            directory=SOURCE_DIR,
            platform=PLATFORM,          # LINUX_ARM64 — defined in common.py
        )

        # Shared execution role from 000-common-infra (broad permissions for testing)
        # Includes: bedrock, ecr:GetAuthorizationToken, logs, bedrock-agentcore:*
        role = get_agentcore_role(self)

        # Per-guide CloudWatch log group
        log_group = guide_log_group(self, GUIDE)

        # AgentCore Runtime — CfnRuntime L1 construct
        runtime = agentcore.CfnRuntime(
            self, "Runtime",
            agent_runtime_name=to_resource_name(GUIDE),
            description=f"AgentCore Runtime for 007-harness-vs-runtime",
            agent_runtime_artifact=agentcore.CfnRuntime.AgentRuntimeArtifactProperty(
                container_configuration=agentcore.CfnRuntime.ContainerConfigurationProperty(
                    container_uri=image.image_uri,
                ),
            ),
            role_arn=role.role_arn,
            network_configuration=agentcore.CfnRuntime.NetworkConfigurationProperty(
                network_mode="PUBLIC",
            ),
            environment_variables={
                "MODEL_ID": "us.amazon.nova-pro-v1:0",
            },
        )

        cdk.CfnOutput(self, "RuntimeArn",    value=runtime.attr_agent_runtime_arn)
        cdk.CfnOutput(self, "RuntimeId",     value=runtime.attr_agent_runtime_id)
        cdk.CfnOutput(self, "ImageUri",      value=image.image_uri)
        cdk.CfnOutput(self, "LogGroupName",  value=log_group.log_group_name)
