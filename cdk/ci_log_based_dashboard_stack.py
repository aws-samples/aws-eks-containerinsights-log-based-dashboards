# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import os
from datetime import datetime
from typing import List

import aws_cdk as cdk
import aws_cdk.aws_lambda as lambda_
from aws_cdk.aws_cloudwatch import Dashboard, LogQueryVisualizationType, LogQueryWidget
from aws_cdk.aws_iam import PolicyStatement
from aws_cdk.aws_lambda_python_alpha import PythonFunction
from cdk_nag import NagPackSuppression, NagSuppressions
from cloudcomponents.cdk_temp_stack import TempStack
from constructs import Construct


class ContainerInsightsLogBasedDashboardStack(TempStack):
    """
    Main stack for the Container Insights Log Based Dashboard.
    This stack provisions the temporary investigation dashboards based on the configuration
    provided via the "dashboard_configuration.yaml" file.
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        NagSuppressions.add_resource_suppressions_by_path(
            stack=self,
            path=f"{construct_id}/TimeToLive",  # TempStack internals
            suppressions=[
                NagPackSuppression(
                    id="AwsSolutions-IAM5",
                    reason="Allow IAM policy wildcard permissions int this specific context",
                ),
                NagPackSuppression(
                    id="AwsSolutions-L1",
                    reason="Allow IAM policy wildcard permissions int this specific context",
                ),
            ],
            apply_to_children=True,
        )

        dashboard_configuration = self.node.try_get_context("dashboardConfiguration")
        log_group_name = f"/aws/containerinsights/{dashboard_configuration['clusterName']}/performance"

        # ======================================
        # Custom Resource
        # ======================================
        log_insights_handler_function = PythonFunction(
            scope=self,
            id="LogInsightsHandlerFunction",
            description="Lambda function for Container Insights log based dashboard custom resources",
            timeout=cdk.Duration.minutes(1),
            runtime=lambda_.Runtime.PYTHON_3_9,
            entry=os.path.join(
                os.getcwd(),
                "assets",
                "serverless",
                "code",
                "logs_insights_handler",
            ),
            index="index.py",
            handler="handler",
            initial_policy=[
                # CR helper polling
                PolicyStatement(
                    actions=[
                        "lambda:AddPermission",
                        "lambda:RemovePermission",
                        "events:PutRule",
                        "events:DeleteRule",
                        "events:PutTargets",
                        "events:RemoveTargets",
                    ],
                    resources=["*"],
                ),
                # Log Insights
                PolicyStatement(
                    actions=["logs:StartQuery"],
                    resources=[
                        f"arn:{self.partition}:logs:{self.region}:{self.account}:log-group:{log_group_name}:*",
                    ],
                ),
                PolicyStatement(
                    actions=["logs:GetQueryResults"],
                    resources=[
                        f"arn:{self.partition}:logs:{self.region}:{self.account}:*",
                    ],
                ),
            ],
        )
        NagSuppressions.add_resource_suppressions(
            log_insights_handler_function,
            suppressions=[
                NagPackSuppression(
                    id="AwsSolutions-IAM5",
                    reason="Allow IAM policy wildcard permissions int this specific context",
                )
            ],
            apply_to_children=True,
        )

        # ======================================
        # Dynamic dashboard generation
        # ======================================
        for content in dashboard_configuration["contents"]:
            content_configuration = dashboard_configuration["contents"][content]
            if content_configuration["enabled"]:
                content = content.capitalize()
                for namespace in content_configuration.get("namespaces", [""]):
                    metric_query = cdk.CustomResource(
                        scope=self,
                        id=f"{content}MetricQuery{namespace}",
                        resource_type=f"Custom::ContainerInsights-{content}MetricQuery",
                        service_token=log_insights_handler_function.function_arn,
                        properties={
                            "iNamespace": namespace,
                            "iLogGroupName": log_group_name,
                            "iStartTime": dashboard_configuration[
                                "investigationWindow"
                            ]["from"],
                            "iEndTime": dashboard_configuration["investigationWindow"][
                                "to"
                            ],
                        },
                    )
                    dashboard = Dashboard(
                        scope=self,
                        id=f"{content}Dashboard{namespace}",
                        dashboard_name="-".join(
                            filter(
                                None,
                                [
                                    dashboard_configuration["name"],
                                    f"{content}Metrics",
                                    namespace,
                                ],
                            )
                        ),
                        start=datetime.strptime(
                            dashboard_configuration["investigationWindow"]["from"],
                            "%Y-%m-%dT%H:%M:%S",
                        ).strftime("%Y-%m-%dT%H:%M:%SZ"),
                        end=datetime.strptime(
                            dashboard_configuration["investigationWindow"]["to"],
                            "%Y-%m-%dT%H:%M:%S",
                        ).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    )

                    widgets: List[LogQueryWidget] = []
                    for metric in content_configuration["metrics"]:
                        formatted_widget_query = cdk.CustomResource(
                            scope=self,
                            id=f"{content}{namespace}{metric}",
                            resource_type="Custom::ContainerInsights-MetricQueryFormatter",
                            service_token=log_insights_handler_function.function_arn,
                            properties={
                                "iQuery": metric_query.get_att_string("oQuery"),
                                "iMetric": metric,
                            },
                        )

                        widgets.append(
                            LogQueryWidget(
                                title=metric,
                                log_group_names=[log_group_name],
                                view=LogQueryVisualizationType.LINE,
                                query_string=formatted_widget_query.get_att_string(
                                    "oFormattedQuery"
                                ),
                                # In a 24-column grid, this means 3 widgets per row
                                width=8,
                                height=8,
                            )
                        )

                    dashboard.add_widgets(*widgets)

                    cdk.CfnOutput(
                        scope=self,
                        id=":".join(
                            filter(
                                None,
                                [
                                    f"{content}Metrics",
                                    namespace,
                                ],
                            )
                        ),
                        value=f"https://{cdk.Stack.of(self).region}.console.aws.amazon.com/cloudwatch/home?region={cdk.Stack.of(self).region}#dashboards:name={dashboard.dashboard_name}",
                    )
