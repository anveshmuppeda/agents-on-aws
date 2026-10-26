"""
CDK Stack — 006-agent-on-agentcore-runtime

Uses shared IAM role and platform from 000-common-infra.
Run '000-common-infra/deploy.sh' before this stack.
"""

import os
import sys
import aws_cdk as cdk
from aws_cdk import aws_ecr_assets as ecr_assets, aws_bedrockagentcore as agentcore
from constructs import Construct

# ── Import shared helpers from common infra ───────────────────────────────────
# Add the common infra Infra/ directory to the Python path so we can import
# common.py which lives at 00-foundations/000-common-infra/Infra/stacks/common.py
_COMMON_INFRA = os.path.join(
    os.path.dirname(__file__),
    "..", "..", "..", "..", "00-foundations", "000-common-infra", "Infra", "stacks"
)
if _COMMON_INFRA not in sys.path:
    sys.path.insert(0, _COMMON_INFRA)

from common import to_resource_name, get_agentcore_role, guide_log_group, PLATFORM  # noqa: E402

SOURCE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "Source")

GUIDE = "006-agent-on-agentcore-runtime"


class MainStack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ── Container image ───────────────────────────────────────────────
        # PLATFORM = LINUX_ARM64 (defined in common.py)
        # Matches: AgentCore Runtime ARM64 microVMs
        #          Apple Silicon Mac (native ARM64 build — fast)
        #          Intel Mac (cross-compile — slower but works)
        image = ecr_assets.DockerImageAsset(
            self, "Image",
            directory=SOURCE_DIR,
            platform=PLATFORM,
        )

        # ── Shared IAM role (from 000-common-infra) ───────────────────────
        # No new role created here — uses the shared AgentCore execution role.
        # Pre-requisite: bash 00-foundations/000-common-infra/deploy.sh
        role = get_agentcore_role(self)

        # ── CloudWatch log group ──────────────────────────────────────────
        log_group = guide_log_group(self, GUIDE)

        # ── AgentCore Runtime — CfnRuntime L1 construct ───────────────────
        runtime = agentcore.CfnRuntime(
            self, "Runtime",
            agent_runtime_name=to_resource_name(GUIDE),
            description=f"AgentCore Runtime agent for {GUIDE}",
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

        # ── Outputs ───────────────────────────────────────────────────────
        cdk.CfnOutput(self, "RuntimeArn",
            value=runtime.attr_agent_runtime_arn,
            description="AgentCore Runtime ARN — use in agentcore invoke --agent",
        )
        cdk.CfnOutput(self, "RuntimeId",
            value=runtime.attr_agent_runtime_id,
            description="AgentCore Runtime ID",
        )
        cdk.CfnOutput(self, "ImageUri",
            value=image.image_uri,
            description="Container image URI in ECR",
        )
        cdk.CfnOutput(self, "LogGroupName",
            value=log_group.log_group_name,
            description="CloudWatch logs: aws logs tail <see Output Value> --follow",
        )
