from aws_cdk import (
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_rds as rds,
    aws_sqs as sqs,
    aws_ecs_patterns as ecs_patterns,
    aws_cloudwatch as cloudwatch,
)
from constructs import Construct
import aws_cdk as core

DATABASE_USER = 'postgres'
DATABASE_NAME = 'logsdb'

FASTAPI_CPU = 256
FASTAPI_MEMORY = 512
FASTAPI_N_TASKS = 1

WORKER_CPU = 256
WORKER_MEMORY = 512
WORKER_N_TASKS = 1

class LogsAppStack(core.Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # VPC
        vpc = ec2.Vpc(self, "MyVpc", max_azs=3)

        # RDS Database
        db = rds.DatabaseInstance(
            self, "MyDB",
            engine=rds.DatabaseInstanceEngine.POSTGRES,
            allocated_storage=20,
            max_allocated_storage=100,
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.T3, ec2.InstanceSize.MICRO),
            multi_az=False,
            publicly_accessible=False,
            vpc=vpc,
            vpc_subnets={
                "subnet_type": ec2.SubnetType.PUBLIC,
            },
            removal_policy=core.RemovalPolicy.DESTROY,
            database_name=DATABASE_NAME,
            credentials=rds.Credentials.from_generated_secret(DATABASE_USER)
        )

        # SQS Queue
        queue = sqs.Queue(
            self, "MyQueue",
            visibility_timeout=core.Duration.seconds(300),
        )

        # ECS Cluster
        cluster = ecs.Cluster(self, "MyCluster", vpc=vpc)

        # Define common settings for containers using the app's Dockerfile
        fastapi_n_vcpus = min(FASTAPI_CPU // 1024, 1)
        app_container_kwargs = dict(
            image=ecs.ContainerImage.from_asset(".."),
            environment={
                "SQS_QUEUE_URL": queue.queue_url,
                "WEB_CONCURRENCY": f"{fastapi_n_vcpus}",
            },
            secrets={
                "DATABASE_USER": ecs.Secret.from_secrets_manager(db.secret, field="username"),
                "DATABASE_PASS": ecs.Secret.from_secrets_manager(db.secret, field="password"),
                "DATABASE_HOST": ecs.Secret.from_secrets_manager(db.secret, field="host"),
                "DATABASE_NAME": ecs.Secret.from_secrets_manager(db.secret, field="dbname"),
            }
        )

        # Task Definition for FastAPI
        fastapi_task_definition = ecs.FargateTaskDefinition(
            self, "FastAPITaskDefinition",
            memory_limit_mib=FASTAPI_MEMORY,
            cpu=FASTAPI_CPU,
        )

        # Container for FastAPI
        fastapi_container = fastapi_task_definition.add_container(
            "FastAPIContainer",
            logging=ecs.LogDriver.aws_logs(stream_prefix="FastAPI"),
            **app_container_kwargs,
        )
        fastapi_container.add_port_mappings(
            ecs.PortMapping(container_port=80, host_port=80)
        )
        # Fargate Service for FastAPI
        ecs_fastapi = ecs_patterns.ApplicationLoadBalancedFargateService(
            self, "FastAPIService",
            cluster=cluster,
            task_definition=fastapi_task_definition,
            desired_count=FASTAPI_N_TASKS,
            assign_public_ip=True,
        )
        ecs_fastapi.target_group.configure_health_check(
            path="/health",
        )

        # Task Definition for Worker service
        worker_task_definition = ecs.FargateTaskDefinition(
            self, "WorkerTaskDefinition",
            memory_limit_mib=WORKER_MEMORY,
            cpu=WORKER_CPU,
        )

        worker_container = worker_task_definition.add_container(
            "WorkerContainer",
            logging=ecs.LogDriver.aws_logs(stream_prefix="Worker"),
            command=["python", "worker.py"],
            **app_container_kwargs,
        )

        # Fargate Service for Worker
        ecs_worker = ecs.FargateService(
            self, "WorkerService",
            cluster=cluster,
            task_definition=worker_task_definition,
            desired_count=WORKER_N_TASKS,
        )

        # Grant SQS permissions
        queue.grant_consume_messages(worker_task_definition.task_role)
        queue.grant_send_messages(fastapi_task_definition.task_role)
        # Grant DB permissions
        db.secret.grant_read(worker_task_definition.task_role)
        db.secret.grant_read(fastapi_task_definition.task_role)
        db.connections.allow_default_port_from(ecs_fastapi.service)
        db.connections.allow_default_port_from(ecs_worker)


        
        # Create CloudWatch Dashboard
        dashboard = cloudwatch.Dashboard(self, "LogsAppDashboard",
            dashboard_name="LogsAppDashboard"
        )

        # Add widgets to the dashboard
        dashboard.add_widgets(
            cloudwatch.TextWidget(markdown="# Database", width=24),
            cloudwatch.GraphWidget(
                title="CPU Utilization",
                left=[db.metric_cpu_utilization()],
                width=12
            ),
            cloudwatch.GraphWidget(
                title="Freeable Memory",
                left=[db.metric_freeable_memory()],
                width=12
            ),
            cloudwatch.GraphWidget(
                title="Database Connections",
                left=[db.metric_database_connections()],
                width=12
            ),
            cloudwatch.GraphWidget(
                title="Read IOPS",
                left=[db.metric_read_iops()],
                width=12
            ),
            cloudwatch.GraphWidget(
                title="Write IOPS",
                left=[db.metric_write_iops()],
                width=12
            ),
            cloudwatch.GraphWidget(
                title="Free Storage Space",
                left=[db.metric_free_storage_space()],
                width=12
            ),
            cloudwatch.TextWidget(markdown="# API", width=24),
            cloudwatch.GraphWidget(
                title="CPU Utilization",
                left=[
                    ecs_fastapi.service.metric_cpu_utilization(statistic="Average"),
                    ecs_fastapi.service.metric_cpu_utilization(statistic="Minimum"),
                    ecs_fastapi.service.metric_cpu_utilization(statistic="Maximum"),
                ],
                width=12
            ),
            cloudwatch.GraphWidget(
                title="Memory Utilization",
                left=[
                    ecs_fastapi.service.metric_memory_utilization(statistic="Average"),
                    ecs_fastapi.service.metric_memory_utilization(statistic="Minimum"),
                    ecs_fastapi.service.metric_memory_utilization(statistic="Maximum"),
                ],
                width=12
            ),
            cloudwatch.TextWidget(markdown="# Worker", width=24),
            cloudwatch.GraphWidget(
                title="CPU Utilization",
                left=[
                    ecs_worker.metric_cpu_utilization(statistic="Average"),
                    ecs_worker.metric_cpu_utilization(statistic="Minimum"),
                    ecs_worker.metric_cpu_utilization(statistic="Maximum"),
                ],
                width=12
            ),
            cloudwatch.GraphWidget(
                title="Memory Utilization",
                left=[
                    ecs_worker.metric_memory_utilization(statistic="Average"),
                    ecs_worker.metric_memory_utilization(statistic="Minimum"),
                    ecs_worker.metric_memory_utilization(statistic="Maximum"),
                ],
                width=12
            ),
            cloudwatch.TextWidget(markdown="# Queue", width=24),
            cloudwatch.GraphWidget(
                title="Messages in Queue",
                left=[queue.metric_approximate_number_of_messages_visible()],
                width=12
            )
        )

app = core.App()
LogsAppStack(app, "LogsAppStack")
app.synth()
