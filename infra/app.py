#!/usr/bin/env python3
import aws_cdk as cdk

from stock_analysis_infra.stack import StockAnalysisStack


app = cdk.App()
StockAnalysisStack(
    app,
    "StockAnalysisStack",
    env=cdk.Environment(
        account=app.node.try_get_context("account"),
        region=app.node.try_get_context("region"),
    ),
)
app.synth()
