"""
CDK Stack — 005-agent-on-lambda

Uses shared Lambda execution role from 000-common-infra.
Run '000-common-infra/deploy.sh' before this stack.
"""

import os
import sys
import aws_cdk as cdk
from aws_cdk import (
    aws_lambda as lambda_,
    aws_apigatewayv2 as apigwv2,
    aws_logs as logs,
)
from aws_cdk.aws_apigatewayv2_integrations import HttpLambdaIntegration
from constructs import Construct

# ── Shared helpers from common infra ─────────────────────────────────────────
_COMMON_INFRA = os.path.join(
    os.path.dirname(__file__),
    "..", "..", "..", "000-common-infra", "Infra", "stacks"
)
if _COMMON_INFRA not in sys.path:
    sys.path.insert(0, _COMMON_INFRA)

from common import to_resource_name, get_lambda_role, guide_log_group  # noqa: E402

SOURCE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "Source")

GUIDE = "005-agent-on-lambda"


class AgentOnLambdaStack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ── Shared Lambda execution role (from 000-common-infra) ─────────
        lambda_role = get_lambda_role(self)

        # ── CloudWatch log group ──────────────────────────────────────────
        log_group = guide_log_group(self, GUIDE)

        # ── Lambda Function — ARM64 container image ───────────────────────
        # ARM64 Lambda = 20% cheaper + better perf on Graviton3.
        # The container image must target linux/arm64 — set in the Dockerfile
        # with: FROM --platform=linux/arm64 public.ecr.aws/lambda/python:3.11-arm64
        # CDK uses architecture=ARM_64 to tell Lambda which CPU family to use.
        # DockerImageCode does NOT accept a 'platform' argument — the architecture
        # is inferred from the Dockerfile's base image and the function's architecture.
        agent_fn = lambda_.DockerImageFunction(
            self,
            "AgentFunction",
            code=lambda_.DockerImageCode.from_image_asset(SOURCE_DIR),
            architecture=lambda_.Architecture.ARM_64,
            role=lambda_role,
            timeout=cdk.Duration.minutes(10),
            memory_size=512,
            log_group=log_group,
            # AWS_DEFAULT_REGION is set automatically by the Lambda runtime —
            # do NOT set it manually (Lambda reserves this env var).
            description="Guide 005 — Strands travel agent on Lambda",
        )

        # ── API Gateway HTTP API ──────────────────────────────────────────
        http_api = apigwv2.HttpApi(
            self,
            "AgentApi",
            description=f"Guide 005 — Agent on Lambda  (POST /invoke)",
            cors_preflight=apigwv2.CorsPreflightOptions(
                allow_methods=[apigwv2.CorsHttpMethod.POST],
                allow_origins=["*"],
                allow_headers=["Content-Type"],
            ),
        )

        http_api.add_routes(
            path="/invoke",
            methods=[apigwv2.HttpMethod.POST],
            integration=HttpLambdaIntegration("AgentIntegration", agent_fn),
        )

        # ── Outputs ───────────────────────────────────────────────────────
        cdk.CfnOutput(
            self, "ApiUrl",
            value=f"{http_api.api_endpoint}/invoke",
            description="POST your {'prompt':'...'} here",
            export_name="Guide005ApiUrl",
        )
        cdk.CfnOutput(
            self, "LambdaFunctionName",
            value=agent_fn.function_name,
            # NOTE: CfnOutput.description must be a static string —
            # tokens like agent_fn.function_name are NOT allowed here.
            description="Lambda function name — see LambdaFunctionName output value for the real name",
        )
