"""
Common Infrastructure Stack — agents-on-aws

Deploy ONCE before running any guide that requires AWS resources.
All guide CDK stacks read from this stack via SSM Parameter Store
instead of creating duplicate IAM roles and log groups per guide.

Resources created:
  IAM Roles:
    AgentCoreExecutionRole   — used by all AgentCore Runtime agents
    LambdaExecutionRole      — used by Lambda function guides (005, 021–027...)
    GatewayExecutionRole     — used by AgentCore Gateway resources
    BrowserExecutionRole     — used by AgentCore Browser resources
    CodeInterpreterRole      — used by AgentCore Code Interpreter resources

  SSM Parameters (exported so guides can import at deploy time):
    /agents-on-aws/iam/agentcore-role-arn
    /agents-on-aws/iam/lambda-role-arn
    /agents-on-aws/iam/gateway-role-arn
    /agents-on-aws/iam/browser-role-arn
    /agents-on-aws/iam/code-interpreter-role-arn
    /agents-on-aws/account-id
    /agents-on-aws/region

Usage in a guide stack:
    from aws_cdk import aws_ssm as ssm

    agentcore_role_arn = ssm.StringParameter.value_for_string_parameter(
        self, "/agents-on-aws/iam/agentcore-role-arn"
    )
    role = iam.Role.from_role_arn(self, "AgentCoreRole", agentcore_role_arn)
"""

import aws_cdk as cdk
from aws_cdk import (
    aws_iam as iam,
    aws_ssm as ssm,
    aws_logs as logs,
)
from constructs import Construct

ACCOUNT_ID = cdk.Aws.ACCOUNT_ID
REGION     = cdk.Aws.REGION


def _bedrock_policy() -> iam.PolicyStatement:
    """Allow invoking any Bedrock model — broad for testing."""
    return iam.PolicyStatement(
        effect=iam.Effect.ALLOW,
        actions=[
            "bedrock:InvokeModel",
            "bedrock:InvokeModelWithResponseStream",
            "bedrock:ListFoundationModels",
        ],
        resources=["*"],
    )


def _logs_policy() -> iam.PolicyStatement:
    """Allow writing CloudWatch logs."""
    return iam.PolicyStatement(
        effect=iam.Effect.ALLOW,
        actions=[
            "logs:CreateLogGroup",
            "logs:CreateLogStream",
            "logs:PutLogEvents",
            "logs:DescribeLogGroups",
            "logs:DescribeLogStreams",
        ],
        resources=["*"],
    )


def _agentcore_data_policy() -> iam.PolicyStatement:
    """Allow calling AgentCore data-plane APIs (Memory, Gateway, Identity, etc.)."""
    return iam.PolicyStatement(
        effect=iam.Effect.ALLOW,
        actions=["bedrock-agentcore:*"],
        resources=["*"],
    )


def _ecr_pull_policy() -> iam.PolicyStatement:
    """Allow pulling container images from ECR."""
    return iam.PolicyStatement(
        effect=iam.Effect.ALLOW,
        actions=[
            "ecr:GetDownloadUrlForLayer",
            "ecr:BatchGetImage",
            "ecr:BatchCheckLayerAvailability",
            "ecr:GetAuthorizationToken",
        ],
        resources=["*"],
    )


def _ssm_read_policy() -> iam.PolicyStatement:
    """Allow agents to read their own SSM parameters at runtime."""
    return iam.PolicyStatement(
        effect=iam.Effect.ALLOW,
        actions=[
            "ssm:GetParameter",
            "ssm:GetParameters",
            "ssm:GetParametersByPath",
        ],
        resources=[f"arn:aws:ssm:{REGION}:{ACCOUNT_ID}:parameter/agents-on-aws/*"],
    )


class CommonInfraStack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ── 1. AgentCore Runtime Execution Role ───────────────────────────
        # Assumed by: bedrock-agentcore.amazonaws.com
        # Used by: ALL guides that deploy to AgentCore Runtime (006–066)
        agentcore_role = iam.Role(
            self,
            "AgentCoreExecutionRole",
            role_name="agents-on-aws-agentcore-execution-role",
            assumed_by=iam.ServicePrincipal("bedrock-agentcore.amazonaws.com"),
            description=(
                "Shared execution role for all AgentCore Runtime agents in agents-on-aws. "
                "Broad permissions intentional for testing/learning purposes."
            ),
        )
        agentcore_role.add_to_policy(_bedrock_policy())
        agentcore_role.add_to_policy(_logs_policy())
        agentcore_role.add_to_policy(_agentcore_data_policy())
        agentcore_role.add_to_policy(_ecr_pull_policy())
        agentcore_role.add_to_policy(_ssm_read_policy())
        # Allow agents to interact with supporting AWS services used across guides
        agentcore_role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "s3:GetObject", "s3:PutObject", "s3:ListBucket",
                "dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:Query", "dynamodb:Scan",
                "cognito-idp:AdminInitiateAuth", "cognito-idp:GetUser",
                "secretsmanager:GetSecretValue",
                "kms:Decrypt", "kms:GenerateDataKey",
            ],
            resources=["*"],
        ))

        # ── 2. Lambda Execution Role ──────────────────────────────────────
        # Assumed by: lambda.amazonaws.com
        # Used by: guides 005, 021–027 (Lambda tool functions)
        lambda_role = iam.Role(
            self,
            "LambdaExecutionRole",
            role_name="agents-on-aws-lambda-execution-role",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ],
            description="Shared Lambda execution role for agents-on-aws tool functions.",
        )
        lambda_role.add_to_policy(_bedrock_policy())
        lambda_role.add_to_policy(_ssm_read_policy())

        # ── 3. Gateway Execution Role ────────────────────────────────────
        # Assumed by: bedrock-agentcore.amazonaws.com (Gateway service)
        # Used by: guides 021–027, 043–045, 054–056
        gateway_role = iam.Role(
            self,
            "GatewayExecutionRole",
            role_name="agents-on-aws-gateway-execution-role",
            assumed_by=iam.ServicePrincipal("bedrock-agentcore.amazonaws.com"),
            description="Shared Gateway execution role for agents-on-aws.",
        )
        gateway_role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["lambda:InvokeFunction"],
            resources=[f"arn:aws:lambda:{REGION}:{ACCOUNT_ID}:function:*"],
        ))
        gateway_role.add_to_policy(_logs_policy())
        gateway_role.add_to_policy(_agentcore_data_policy())

        # ── 4. Browser Execution Role ─────────────────────────────────────
        # Assumed by: bedrock-agentcore.amazonaws.com (Browser service)
        # Used by: guides 037–041
        browser_role = iam.Role(
            self,
            "BrowserExecutionRole",
            role_name="agents-on-aws-browser-execution-role",
            assumed_by=iam.ServicePrincipal("bedrock-agentcore.amazonaws.com"),
            description="Shared Browser execution role for agents-on-aws.",
        )
        browser_role.add_to_policy(_logs_policy())
        browser_role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["s3:PutObject", "s3:GetObject"],
            resources=[f"arn:aws:s3:::*agents-on-aws*/*"],
        ))

        # ── 5. Code Interpreter Execution Role ────────────────────────────
        # Assumed by: bedrock-agentcore.amazonaws.com (Code Interpreter service)
        # Used by: guides 042–045
        ci_role = iam.Role(
            self,
            "CodeInterpreterExecutionRole",
            role_name="agents-on-aws-code-interpreter-role",
            assumed_by=iam.ServicePrincipal("bedrock-agentcore.amazonaws.com"),
            description="Shared Code Interpreter execution role for agents-on-aws.",
        )
        ci_role.add_to_policy(_logs_policy())
        ci_role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["s3:GetObject", "s3:PutObject", "s3:ListBucket"],
            resources=["*"],
        ))

        # ── 6. SSM Parameters — guides import these instead of creating roles ──
        params = {
            "agentcore-role-arn":         agentcore_role.role_arn,
            "agentcore-role-name":        agentcore_role.role_name,
            "lambda-role-arn":            lambda_role.role_arn,
            "lambda-role-name":           lambda_role.role_name,
            "gateway-role-arn":           gateway_role.role_arn,
            "browser-role-arn":           browser_role.role_arn,
            "code-interpreter-role-arn":  ci_role.role_arn,
            "account-id":                 ACCOUNT_ID,
            "region":                     REGION,
        }

        for key, value in params.items():
            ssm.StringParameter(
                self,
                f"Param-{key}",
                parameter_name=f"/agents-on-aws/{key}",
                string_value=value,
                description=f"agents-on-aws shared config: {key}",
            )

        # ── 7. Shared CloudWatch Log Group (optional per-guide logs go here) ─
        logs.LogGroup(
            self,
            "SharedLogGroup",
            log_group_name="/aws/agents-on-aws",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )

        # ── Outputs ───────────────────────────────────────────────────────
        cdk.CfnOutput(self, "AgentCoreRoleArn",  value=agentcore_role.role_arn,
                      description="Use in CfnRuntime(role_arn=...)")
        cdk.CfnOutput(self, "LambdaRoleArn",     value=lambda_role.role_arn,
                      description="Use in lambda_.Function(role=...)")
        cdk.CfnOutput(self, "GatewayRoleArn",    value=gateway_role.role_arn,
                      description="Use in CfnGateway(role_arn=...)")
        cdk.CfnOutput(self, "BrowserRoleArn",    value=browser_role.role_arn,
                      description="Use in CfnBrowserCustom(execution_role_arn=...)")
        cdk.CfnOutput(self, "CodeInterpreterRoleArn", value=ci_role.role_arn,
                      description="Use in CfnCodeInterpreterCustom(execution_role_arn=...)")
