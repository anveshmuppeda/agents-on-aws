"""
common.py — Shared helpers for all guide CDK stacks.

Import this in any guide's main_stack.py to get shared IAM roles
from the common infrastructure stack via SSM, without creating
duplicate roles per guide.

Usage in a guide stack:
    from stacks.common import get_agentcore_role, get_lambda_role, PLATFORM

    class MainStack(cdk.Stack):
        def __init__(self, ...):
            ...
            # Get shared AgentCore role (instead of creating a new one)
            role = get_agentcore_role(self)

            # Get shared Lambda role
            lambda_role = get_lambda_role(self)

            # Use consistent platform
            image = ecr_assets.DockerImageAsset(
                self, "Image",
                directory=SOURCE_DIR,
                platform=PLATFORM,          # ← ARM64 for Mac + AgentCore
            )
"""

import aws_cdk as cdk
from aws_cdk import (
    aws_iam as iam,
    aws_ssm as ssm,
    aws_ecr_assets as ecr_assets,
    aws_logs as logs,
)
from constructs import Construct

# ── Platform ──────────────────────────────────────────────────────────────────
# AgentCore Runtime uses ARM64 microVMs.
# On Apple Silicon Macs, docker buildx builds ARM64 images natively (fast).
# On Intel Macs, it cross-compiles (slow but works).
# On Linux CI (amd64), it cross-compiles (slower but correct).
PLATFORM = ecr_assets.Platform.LINUX_ARM64

# ── SSM Parameter paths ───────────────────────────────────────────────────────
SSM_PREFIX              = "/agents-on-aws"
SSM_AGENTCORE_ROLE_ARN  = f"{SSM_PREFIX}/agentcore-role-arn"
SSM_LAMBDA_ROLE_ARN     = f"{SSM_PREFIX}/lambda-role-arn"
SSM_GATEWAY_ROLE_ARN    = f"{SSM_PREFIX}/gateway-role-arn"
SSM_BROWSER_ROLE_ARN    = f"{SSM_PREFIX}/browser-role-arn"
SSM_CI_ROLE_ARN         = f"{SSM_PREFIX}/code-interpreter-role-arn"

# ── Stack name of the common infra ────────────────────────────────────────────
COMMON_STACK_NAME = "AgentsOnAwsCommonInfra"


def get_agentcore_role(scope: Construct) -> iam.IRole:
    """
    Import the shared AgentCore Runtime execution role from common infra.
    Use this instead of creating a new iam.Role in each guide.

    The role has permissions for:
      - bedrock:InvokeModel + InvokeModelWithResponseStream
      - bedrock-agentcore:* (Memory, Gateway, Identity data-plane APIs)
      - logs:CreateLogGroup/Stream/PutLogEvents
      - ecr:GetDownloadUrl + BatchGetImage (pull container images)
      - ssm:GetParameter (read /agents-on-aws/* parameters)
      - s3, dynamodb, cognito-idp (common supporting services)
    """
    role_arn = ssm.StringParameter.value_for_string_parameter(
        scope, SSM_AGENTCORE_ROLE_ARN
    )
    return iam.Role.from_role_arn(
        scope, "ImportedAgentCoreRole", role_arn,
        mutable=False,
    )


def get_lambda_role(scope: Construct) -> iam.IRole:
    """
    Import the shared Lambda execution role from common infra.
    Use for Lambda tool functions in Gateway guides.

    Includes: AWSLambdaBasicExecutionRole + bedrock:InvokeModel.
    """
    role_arn = ssm.StringParameter.value_for_string_parameter(
        scope, SSM_LAMBDA_ROLE_ARN
    )
    return iam.Role.from_role_arn(
        scope, "ImportedLambdaRole", role_arn,
        mutable=False,
    )


def get_gateway_role(scope: Construct) -> iam.IRole:
    """
    Import the shared Gateway execution role from common infra.
    Use for CfnGateway(role_arn=...).
    """
    role_arn = ssm.StringParameter.value_for_string_parameter(
        scope, SSM_GATEWAY_ROLE_ARN
    )
    return iam.Role.from_role_arn(
        scope, "ImportedGatewayRole", role_arn,
        mutable=False,
    )


def get_browser_role(scope: Construct) -> iam.IRole:
    """
    Import the shared Browser execution role from common infra.
    Use for CfnBrowserCustom(execution_role_arn=...).
    """
    role_arn = ssm.StringParameter.value_for_string_parameter(
        scope, SSM_BROWSER_ROLE_ARN
    )
    return iam.Role.from_role_arn(
        scope, "ImportedBrowserRole", role_arn,
        mutable=False,
    )


def get_code_interpreter_role(scope: Construct) -> iam.IRole:
    """
    Import the shared Code Interpreter execution role from common infra.
    Use for CfnCodeInterpreterCustom(execution_role_arn=...).
    """
    role_arn = ssm.StringParameter.value_for_string_parameter(
        scope, SSM_CI_ROLE_ARN
    )
    return iam.Role.from_role_arn(
        scope, "ImportedCodeInterpreterRole", role_arn,
        mutable=False,
    )


def guide_log_group(scope: Construct, guide_name: str) -> logs.LogGroup:
    """
    Create a per-guide CloudWatch log group with standard naming and retention.

    Args:
        scope: CDK construct scope
        guide_name: e.g. "006-agent-on-agentcore-runtime"

    Returns:
        LogGroup at /aws/agents-on-aws/{guide_name}
    """
    return logs.LogGroup(
        scope,
        "LogGroup",
        log_group_name=f"/aws/agents-on-aws/{guide_name}",
        retention=logs.RetentionDays.ONE_WEEK,
        removal_policy=cdk.RemovalPolicy.DESTROY,
    )


def to_resource_name(guide_name: str) -> str:
    """
    Convert a guide name to a valid AgentCore resource name.

    AgentCore API constraint: [a-zA-Z][a-zA-Z0-9_]{0,47}
      - Must start with a letter
      - Only letters, digits, and underscores allowed (NO hyphens)
      - Maximum 48 characters

    Examples:
        "006-agent-on-agentcore-runtime" → "g006_agent_on_agentcore_runtime"
        "016-memory-short-term"          → "g016_memory_short_term"
        "021-gateway-lambda-tool"        → "g021_gateway_lambda_tool"

    The prefix 'g' ensures the name starts with a letter (required by the API).
    """
    clean = "g" + guide_name.replace("-", "_")
    return clean[:48]  # enforce max 48 chars
