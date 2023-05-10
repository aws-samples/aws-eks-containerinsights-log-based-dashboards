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

import boto3
from crhelper import CfnResource

LOGGER = logging.getLogger(__name__)

LOGS_CLIENT = boto3.client("logs")

helper = CfnResource(
    log_level="DEBUG",
    boto_level="CRITICAL",
)


@helper.create
@helper.update
def format_query(event, context):
    """
    Format the query with a specific metric name during CloudFormation Create and Update
    events.
    """
    helper.Data["oFormattedQuery"] = str(event["ResourceProperties"]["iQuery"]).format(
        metric=event["ResourceProperties"]["iMetric"]
    )

    LOGGER.info(f'Formatted query: {helper.Data["oFormattedQuery"]}')

    return True


@helper.update
@helper.delete
def no_op(_, __):
    return True


def handler(event, context):
    helper(event, context)
