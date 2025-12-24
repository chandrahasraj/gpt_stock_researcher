import aws_cdk as cdk
from aws_cdk import Duration, Stack
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_ecs_patterns as ecs_patterns
from aws_cdk import aws_events as events
from aws_cdk import aws_events_targets as events_targets
from aws_cdk import aws_iam as iam
from aws_cdk import aws_logs as logs
from aws_cdk import aws_s3 as s3
from constructs import Construct


class StockAnalysisStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        runs_bucket = s3.Bucket(
            self,
            "RunsBucket",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
        )

        vpc = ec2.Vpc(self, "StockAnalysisVpc", max_azs=2)

        cluster = ecs.Cluster(self, "StockAnalysisCluster", vpc=vpc)

        container_image = cdk.CfnParameter(
            self,
            "ContainerImage",
            type="String",
            description="Container image URI for the MCP server and pipeline runner.",
            default="public.ecr.aws/docker/library/python:3.11-slim",
        )

        server_command = cdk.CfnParameter(
            self,
            "ServerCommand",
            type="String",
            description="Command for starting the MCP server container.",
            default="uvicorn services.mcp_server.main:app --host 0.0.0.0 --port 8000",
        )

        pipeline_command = cdk.CfnParameter(
            self,
            "PipelineCommand",
            type="String",
            description="Command for executing the stock pipeline runner.",
            default="python -m src.pipelines.stock_pipeline --ticker ASTS --mode batch",
        )

        pipeline_schedule = cdk.CfnParameter(
            self,
            "PipelineSchedule",
            type="String",
            description="EventBridge schedule expression for the pipeline run.",
            default="rate(1 day)",
        )

        task_role = iam.Role(
            self,
            "TaskRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
        )
        runs_bucket.grant_read_write(task_role)

        server_task_definition = ecs.FargateTaskDefinition(
            self,
            "ServerTaskDefinition",
            cpu=256,
            memory_limit_mib=512,
            task_role=task_role,
        )

        server_log_group = logs.LogGroup(
            self,
            "ServerLogs",
            retention=logs.RetentionDays.ONE_WEEK,
        )

        server_container = server_task_definition.add_container(
            "McpServer",
            image=ecs.ContainerImage.from_registry(container_image.value_as_string),
            logging=ecs.LogDriver.aws_logs(
                stream_prefix="mcp-server",
                log_group=server_log_group,
            ),
            environment={
                "RUNS_BUCKET": runs_bucket.bucket_name,
            },
            command=cdk.Fn.split(" ", server_command.value_as_string),
        )
        server_container.add_port_mappings(ecs.PortMapping(container_port=8000))

        server_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "McpServerService",
            cluster=cluster,
            task_definition=server_task_definition,
            desired_count=1,
            public_load_balancer=True,
            health_check_grace_period=Duration.seconds(60),
            capacity_provider_strategies=[
                ecs.CapacityProviderStrategy(
                    capacity_provider="FARGATE_SPOT",
                    weight=1,
                )
            ],
        )

        server_service.target_group.configure_health_check(
            path="/healthz",
            healthy_http_codes="200",
        )

        pipeline_task_definition = ecs.FargateTaskDefinition(
            self,
            "PipelineTaskDefinition",
            cpu=256,
            memory_limit_mib=512,
            task_role=task_role,
        )

        pipeline_log_group = logs.LogGroup(
            self,
            "PipelineLogs",
            retention=logs.RetentionDays.ONE_WEEK,
        )

        pipeline_task_definition.add_container(
            "PipelineRunner",
            image=ecs.ContainerImage.from_registry(container_image.value_as_string),
            logging=ecs.LogDriver.aws_logs(
                stream_prefix="pipeline",
                log_group=pipeline_log_group,
            ),
            environment={
                "RUNS_BUCKET": runs_bucket.bucket_name,
            },
            command=cdk.Fn.split(" ", pipeline_command.value_as_string),
        )

        events.Rule(
            self,
            "PipelineScheduleRule",
            schedule=events.Schedule.expression(pipeline_schedule.value_as_string),
            targets=[
                events_targets.EcsTask(
                    cluster=cluster,
                    task_definition=pipeline_task_definition,
                    subnet_selection=ec2.SubnetSelection(
                        subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
                    ),
                    assign_public_ip=False,
                    capacity_provider_strategies=[
                        ecs.CapacityProviderStrategy(
                            capacity_provider="FARGATE_SPOT",
                            weight=1,
                        )
                    ],
                )
            ],
        )

        cdk.CfnOutput(self, "RunsBucketName", value=runs_bucket.bucket_name)
        cdk.CfnOutput(
            self,
            "McpServerEndpoint",
            value=server_service.load_balancer.load_balancer_dns_name,
        )
