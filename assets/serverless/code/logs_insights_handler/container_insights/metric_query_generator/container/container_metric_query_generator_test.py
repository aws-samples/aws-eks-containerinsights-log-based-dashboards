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

import copy
from typing import Any, Dict, List, Optional

import pytest
from container_insights.metric_query_generator.container import (
    ContainerMetricQueryGenerator,
)

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
                "field": "PodName",
                "value": "csi-secrets-store-provider-aws-secrets-store-csi-driver",
            },
            {"field": "kubernetes.container_name", "value": "secrets-store"},
            {"field": "count()", "value": "58"},
        ],
        [
            {
                "field": "PodName",
                "value": "cluster-autoscaler-aws-cluster-autoscaler",
            },
            {
                "field": "kubernetes.container_name",
                "value": "aws-cluster-autoscaler",
            },
            {"field": "count()", "value": "58"},
        ],
        [
            {"field": "PodName", "value": "csi-secrets-store-provider-aws"},
            {
                "field": "kubernetes.container_name",
                "value": "provider-aws-installer",
            },
            {"field": "count()", "value": "57"},
        ],
        [
            {
                "field": "PodName",
                "value": "csi-secrets-store-provider-aws-secrets-store-csi-driver",
            },
            {
                "field": "kubernetes.container_name",
                "value": "node-driver-registrar",
            },
            {"field": "count()", "value": "57"},
        ],
        [
            {
                "field": "PodName",
                "value": "csi-secrets-store-provider-aws-secrets-store-csi-driver",
            },
            {"field": "kubernetes.container_name", "value": "liveness-probe"},
            {"field": "count()", "value": "57"},
        ],
        [
            {"field": "PodName", "value": "aws-for-fluent-bit"},
            {
                "field": "kubernetes.container_name",
                "value": "aws-for-fluent-bit",
            },
            {"field": "count()", "value": "57"},
        ],
        [
            {
                "field": "PodName",
                "value": "container-insights-metrics-opentelemetry-collector-agent",
            },
            {
                "field": "kubernetes.container_name",
                "value": "opentelemetry-collector",
            },
            {"field": "count()", "value": "57"},
        ],
    ],
    "statistics": {
        "recordsMatched": 28760.0,
        "recordsScanned": 232956.0,
        "bytesScanned": 346272125.0,
    },
    "status": "Complete",
    "ResponseMetadata": {
        "HTTPStatusCode": 200,
    },
}


def test_generate_lookup_query(mocker):
    container_metric_query_generator = ContainerMetricQueryGenerator()

    assert (
        container_metric_query_generator.generate_lookup_query(EVENT)
        == 'fields PodName, kubernetes.container_name | filter Type = "Container" and Namespace = "eks-baseline-services" | stats count() by PodName, kubernetes.container_name'
    )


def test_generate_metric_query(mocker):
    container_metric_query_generator = ContainerMetricQueryGenerator()

    assert container_metric_query_generator.generate_metric_query(
        EVENT, LOOKUP_QUERY_RESPONSE
    ) == (
        "fields {metric}, "
        '(PodName = \\"csi-secrets-store-provider-aws-secrets-store-csi-driver\\") as pod1, '
        '(PodName = \\"cluster-autoscaler-aws-cluster-autoscaler\\") as pod2, '
        '(PodName = \\"csi-secrets-store-provider-aws\\") as pod3, '
        '(PodName = \\"aws-for-fluent-bit\\") as pod4, '
        '(PodName = \\"container-insights-metrics-opentelemetry-collector-agent\\") as pod5, '
        '(kubernetes.container_name = \\"aws-cluster-autoscaler\\") as container1, '
        '(kubernetes.container_name = \\"aws-for-fluent-bit\\") as container2, '
        '(kubernetes.container_name = \\"liveness-probe\\") as container3, '
        '(kubernetes.container_name = \\"node-driver-registrar\\") as container4, '
        '(kubernetes.container_name = \\"opentelemetry-collector\\") as container5, '
        '(kubernetes.container_name = \\"provider-aws-installer\\") as container6, '
        '(kubernetes.container_name = \\"secrets-store\\") as container7 '
        '| filter (Type = \\"Container\\" or Type = \\"ContainerFS\\") and Namespace = \\"eks-baseline-services\\" and ispresent({metric}) '
        "| stats "
        "sum({metric} * pod1 * container7) / sum(pod1 * container7) as `csi-secrets-store-provider-aws-secrets-store-csi-driver secrets-store`, "
        "sum({metric} * pod1 * container4) / sum(pod1 * container4) as `csi-secrets-store-provider-aws-secrets-store-csi-driver node-driver-registrar`, "
        "sum({metric} * pod1 * container3) / sum(pod1 * container3) as `csi-secrets-store-provider-aws-secrets-store-csi-driver liveness-probe`, "
        "sum({metric} * pod2 * container1) / sum(pod2 * container1) as `cluster-autoscaler-aws-cluster-autoscaler aws-cluster-autoscaler`, "
        "sum({metric} * pod3 * container6) / sum(pod3 * container6) as `csi-secrets-store-provider-aws provider-aws-installer`, "
        "sum({metric} * pod4 * container2) / sum(pod4 * container2) as `aws-for-fluent-bit aws-for-fluent-bit`, "
        "sum({metric} * pod5 * container5) / sum(pod5 * container5) as `container-insights-metrics-opentelemetry-collector-agent opentelemetry-collector` "
        "by bin(1m)"
    )
