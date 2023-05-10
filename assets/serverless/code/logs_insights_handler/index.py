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

from container_insights import metric_query_formatter, metric_query_generator
from container_insights.metric_query_generator.container import (
    ContainerMetricQueryGenerator,
)
from container_insights.metric_query_generator.node import NodeMetricQueryGenerator
from container_insights.metric_query_generator.pod import PodMetricQueryGenerator


def handler(event, context):
    """
    This Lambda handler serves four distinct CloudFormation custom resources:
        1. Custom::ContainerInsights-NodeMetricQuery
        2. Custom::ContainerInsights-PodMetricQuery
        3. Custom::ContainerInsights-ContainerMetricQuery
        4. Custom::ContainerInsights-MetricQueryFormatter
    """

    resource_type = event.get("ResourceType", None)

    # Execute node specific lookup query to generate a generic node metric query
    if resource_type == "Custom::ContainerInsights-NodeMetricQuery":
        return metric_query_generator.handler(
            event, context, NodeMetricQueryGenerator()
        )

    # Execute pod specific lookup query to generate a generic pod metric query
    if resource_type == "Custom::ContainerInsights-PodMetricQuery":
        return metric_query_generator.handler(event, context, PodMetricQueryGenerator())

    # Execute container specific lookup query to generate a generic container metric query
    if resource_type == "Custom::ContainerInsights-ContainerMetricQuery":
        return metric_query_generator.handler(
            event, context, ContainerMetricQueryGenerator()
        )

    # Turns a node, pod or container generic query into a metric specific query
    if resource_type == "Custom::ContainerInsights-MetricQueryFormatter":
        return metric_query_formatter.handler(event, context)

    raise Exception(f"Unknown resource type: {resource_type}")
