from pathlib import Path
import sys

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))


def test_stack_resources() -> None:
    pytest.importorskip("aws_cdk")
    from aws_cdk.assertions import Match, Template
    import aws_cdk as cdk

    from stock_analysis_infra.stack import StockAnalysisStack

    app = cdk.App()
    stack = StockAnalysisStack(app, "TestStack")
    template = Template.from_stack(stack)

    template.resource_count_is("AWS::S3::Bucket", 1)
    template.has_resource_properties(
        "AWS::S3::Bucket",
        {
            "BucketEncryption": {
                "ServerSideEncryptionConfiguration": [
                    {"ServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}
                ]
            },
            "PublicAccessBlockConfiguration": {
                "BlockPublicAcls": True,
                "BlockPublicPolicy": True,
                "IgnorePublicAcls": True,
                "RestrictPublicBuckets": True,
            },
        },
    )

    template.resource_count_is("AWS::ECS::Cluster", 1)
    template.resource_count_is("AWS::ECS::Service", 1)
    template.resource_count_is("AWS::ElasticLoadBalancingV2::LoadBalancer", 1)

    template.has_resource_properties(
        "AWS::Events::Rule",
        {
            "ScheduleExpression": Match.any_value(),
            "Targets": Match.array_with([Match.object_like({"Arn": Match.any_value()})]),
        },
    )
