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

import logging
from abc import ABC, abstractmethod
from datetime import datetime

import boto3
from crhelper import CfnResource

LOGGER = logging.getLogger(__name__)

LOGS_CLIENT = boto3.client("logs")

helper = CfnResource(
    log_level="INFO",
    boto_level="CRITICAL",
)

METRIC_QUERY_GENERATOR = None


class MetricQueryGenerator(ABC):
    """Abstract Metric Query Generator class"""

    @abstractmethod
    def generate_lookup_query(self, event) -> str:
        """Generate the lookup query"""
        pass

    @abstractmethod
    def generate_metric_query(self, event, response) -> str:
        """Generate the metric query"""
        pass


@helper.create
@helper.update
def create_query(event, context):
    """
    Implementation for the CloudFormation create events for resources
        1. Custom::ContainerInsights-NodeMetricQuery
        2. Custom::ContainerInsights-PodMetricQuery
        3. Custom::ContainerInsights-ContainerMetricQuery

    The lookup query is started against the given LogGroup.
    """

    logs_insights_query = METRIC_QUERY_GENERATOR.generate_lookup_query(event)

    try:
        return LOGS_CLIENT.start_query(
            logGroupName=event["ResourceProperties"]["iLogGroupName"],
            startTime=int(
                datetime.strptime(
                    event["ResourceProperties"]["iStartTime"], "%Y-%m-%dT%H:%M:%S"
                ).timestamp()
            ),
            endTime=int(
                datetime.strptime(
                    event["ResourceProperties"]["iEndTime"], "%Y-%m-%dT%H:%M:%S"
                ).timestamp()
            ),
            queryString=logs_insights_query,
        )["queryId"]
    except Exception as ex:
        error_msg = f'Could not start query "{logs_insights_query}", against log group "{event["ResourceProperties"]["iLogGroupName"]}"'
        LOGGER.exception(error_msg)
        raise Exception(error_msg) from ex


@helper.poll_create
@helper.poll_update
def poll_create_query(event, context):
    """
    Implementation for the CloudFormation POLL create events for resources
        1. Custom::ContainerInsights-NodeMetricQuery
        2. Custom::ContainerInsights-PodMetricQuery
        3. Custom::ContainerInsights-ContainerMetricQuery

    The lookup query resuls are collected and the final generic metric query is assembled.
    """

    query_id = event["CrHelperData"]["PhysicalResourceId"]

    try:
        response = LOGS_CLIENT.get_query_results(queryId=query_id)
    except Exception as ex:
        error_msg = f'Could not get query results for query ID "{query_id}"'
        LOGGER.exception(error_msg)
        raise Exception(error_msg) from ex

    if (query_status := response.get("status", None)) not in ["Running", "Complete"]:
        raise Exception(
            f'Unexpected query status "{query_status}" for query ID "{query_id}"'
        )
    elif query_status == "Complete" and not response.get("results", None):
        raise Exception(
            f'Query ID "{query_id}" didnt return any result, please double check the correctness of the provided investigation window'
        )

    if query_status == "Running":
        return False  # Continue polling

    helper.Data["oQuery"] = METRIC_QUERY_GENERATOR.generate_metric_query(
        event, response
    )

    return True


@helper.delete
def no_op(_, __):
    return True


def handler(event, context, metric_query_generator: MetricQueryGenerator):
    global METRIC_QUERY_GENERATOR
    METRIC_QUERY_GENERATOR = metric_query_generator
    helper(event, context)
