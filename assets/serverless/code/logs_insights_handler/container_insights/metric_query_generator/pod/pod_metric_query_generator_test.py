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

from container_insights.metric_query_generator.pod import PodMetricQueryGenerator

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
            {"field": "PodName", "value": "cert-manager-webhook"},
            {"field": "count()", "value": "1438"},
        ],
        [
            {
                "field": "PodName",
                "value": "cluster-autoscaler-aws-cluster-autoscaler",
            },
            {"field": "count()", "value": "1438"},
        ],
        [
            {"field": "PodName", "value": "coredns"},
            {"field": "count()", "value": "2876"},
        ],
        [
            {"field": "PodName", "value": "kube-proxy"},
            {"field": "count()", "value": "1438"},
        ],
        [
            {
                "field": "PodName",
                "value": "opentelemetry-operator-controller-manager",
            },
            {"field": "count()", "value": "1438"},
        ],
        [
            {"field": "PodName", "value": "gatekeeper-controller-manager"},
            {"field": "count()", "value": "4314"},
        ],
        [
            {"field": "PodName", "value": "aws-load-balancer-controller"},
            {"field": "count()", "value": "2876"},
        ],
        [
            {"field": "PodName", "value": "cert-manager"},
            {"field": "count()", "value": "1438"},
        ],
        [
            {"field": "PodName", "value": "aws-for-fluent-bit"},
            {"field": "count()", "value": "1438"},
        ],
        [
            {
                "field": "PodName",
                "value": "container-insights-metrics-opentelemetry-collector-agent",
            },
            {"field": "count()", "value": "1438"},
        ],
        [
            {"field": "PodName", "value": "cert-manager-cainjector"},
            {"field": "count()", "value": "1438"},
        ],
        [
            {"field": "PodName", "value": "metrics-server"},
            {"field": "count()", "value": "1438"},
        ],
        [
            {"field": "PodName", "value": "csi-secrets-store-provider-aws"},
            {"field": "count()", "value": "1438"},
        ],
        [
            {
                "field": "PodName",
                "value": "csi-secrets-store-provider-aws-secrets-store-csi-driver",
            },
            {"field": "count()", "value": "1438"},
        ],
        [
            {"field": "PodName", "value": "aws-node"},
            {"field": "count()", "value": "1438"},
        ],
        [
            {"field": "PodName", "value": "gatekeeper-audit"},
            {"field": "count()", "value": "1438"},
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
    pod_metric_query_generator = PodMetricQueryGenerator()

    assert (
        pod_metric_query_generator.generate_lookup_query(EVENT)
        == 'fields PodName | filter Type = "Pod" and Namespace = "eks-baseline-services" | stats count() by PodName'
    )


def test_generate_metric_query(mocker):
    pod_metric_query_generator = PodMetricQueryGenerator()

    assert pod_metric_query_generator.generate_metric_query(
        EVENT, LOOKUP_QUERY_RESPONSE
    ) == (
        "fields {metric}, "
        '(PodName = \\"cert-manager-webhook\\") as pod1, '
        '(PodName = \\"cluster-autoscaler-aws-cluster-autoscaler\\") as pod2, '
        '(PodName = \\"coredns\\") as pod3, '
        '(PodName = \\"kube-proxy\\") as pod4, '
        '(PodName = \\"opentelemetry-operator-controller-manager\\") as pod5, '
        '(PodName = \\"gatekeeper-controller-manager\\") as pod6, '
        '(PodName = \\"aws-load-balancer-controller\\") as pod7, '
        '(PodName = \\"cert-manager\\") as pod8, '
        '(PodName = \\"aws-for-fluent-bit\\") as pod9, '
        '(PodName = \\"container-insights-metrics-opentelemetry-collector-agent\\") as pod10, '
        '(PodName = \\"cert-manager-cainjector\\") as pod11, '
        '(PodName = \\"metrics-server\\") as pod12, '
        '(PodName = \\"csi-secrets-store-provider-aws\\") as pod13, '
        '(PodName = \\"csi-secrets-store-provider-aws-secrets-store-csi-driver\\") as pod14, '
        '(PodName = \\"aws-node\\") as pod15, '
        '(PodName = \\"gatekeeper-audit\\") as pod16 '
        '| filter (Type = \\"Pod\\" or Type = \\"PodNet\\") and Namespace = \\"eks-baseline-services\\" and ispresent({metric}) '
        "| stats "
        "sum({metric} * pod1) / sum(pod1) as `cert-manager-webhook`, "
        "sum({metric} * pod2) / sum(pod2) as `cluster-autoscaler-aws-cluster-autoscaler`, "
        "sum({metric} * pod3) / sum(pod3) as `coredns`, "
        "sum({metric} * pod4) / sum(pod4) as `kube-proxy`, "
        "sum({metric} * pod5) / sum(pod5) as `opentelemetry-operator-controller-manager`, "
        "sum({metric} * pod6) / sum(pod6) as `gatekeeper-controller-manager`, "
        "sum({metric} * pod7) / sum(pod7) as `aws-load-balancer-controller`, "
        "sum({metric} * pod8) / sum(pod8) as `cert-manager`, "
        "sum({metric} * pod9) / sum(pod9) as `aws-for-fluent-bit`, "
        "sum({metric} * pod10) / sum(pod10) as `container-insights-metrics-opentelemetry-collector-agent`, "
        "sum({metric} * pod11) / sum(pod11) as `cert-manager-cainjector`, "
        "sum({metric} * pod12) / sum(pod12) as `metrics-server`, "
        "sum({metric} * pod13) / sum(pod13) as `csi-secrets-store-provider-aws`, "
        "sum({metric} * pod14) / sum(pod14) as `csi-secrets-store-provider-aws-secrets-store-csi-driver`, "
        "sum({metric} * pod15) / sum(pod15) as `aws-node`, "
        "sum({metric} * pod16) / sum(pod16) as `gatekeeper-audit` "
        "by bin(1m)"
    )
