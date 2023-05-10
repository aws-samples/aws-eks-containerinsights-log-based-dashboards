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

from container_insights.metric_query_generator.node import NodeMetricQueryGenerator

EVENT = {
    "RequestType": "Create",
    "ResourceProperties": {
        "iLogGroupName": "/aws/containerinsights/eks-cluster/performance",
        "iNamespace": "eks-baseline-services",
        "iStartTime": "2022-12-19T12:00:00",
        "iEndTime": "2022-12-19T23:00:00",
    },
}

LOOKUP_QUERY_RESPONSE = {
    "results": [
        [
            {
                "field": "NodeName",
                "value": "ip-192-168-10-213.eu-central-1.compute.internal",
            },
            {"field": "count()", "value": "360"},
        ]
    ],
    "statistics": {
        "recordsMatched": 360.0,
        "recordsScanned": 14760.0,
        "bytesScanned": 20302420.0,
    },
    "status": "Complete",
    "ResponseMetadata": {
        "RequestId": "e7ff6c7d-89d6-4bc9-b3f1-901d58ac6db8",
        "HTTPStatusCode": 200,
        "HTTPHeaders": {
            "x-amzn-requestid": "e7ff6c7d-89d6-4bc9-b3f1-901d58ac6db8",
            "content-type": "application/x-amz-json-1.1",
            "content-length": "237",
            "date": "Fri, 10 Feb 2023 08:39:30 GMT",
        },
        "RetryAttempts": 0,
    },
}


def test_generate_lookup_query(mocker):
    node_metric_query_generator = NodeMetricQueryGenerator()

    assert (
        node_metric_query_generator.generate_lookup_query(EVENT)
        == 'fields NodeName | filter Type = "Node" | stats count() by NodeName'
    )


def test_generate_metric_query(mocker):
    node_metric_query_generator = NodeMetricQueryGenerator()

    assert node_metric_query_generator.generate_metric_query(
        EVENT, LOOKUP_QUERY_RESPONSE
    ) == (
        "fields {metric}, "
        '(NodeName = \\"ip-192-168-10-213.eu-central-1.compute.internal\\") as node1 '
        '| filter (Type = \\"Node\\" or Type = \\"NodeNet\\" or Type = \\"NodeFS\\" or Type = \\"NodeDiskIO\\") and ispresent({metric}) '
        "| stats "
        "sum({metric} * node1) / sum(node1) as `ip-192-168-10-213.eu-central-1.compute.internal` "
        "by bin(1m)"
    )
