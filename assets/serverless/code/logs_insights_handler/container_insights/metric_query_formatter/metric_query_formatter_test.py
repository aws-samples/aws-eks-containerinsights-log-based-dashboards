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

from . import format_query, helper

EVENT = {
    "RequestType": "Create",
    "ResourceProperties": {
        "iQuery": """fields Type, {metric}, (PodName like "cert-manager-webhook") as pod1, (PodName like "cluster-autoscaler-aws-cluster-autoscaler") as pod2, (PodName like "coredns") as pod3, (PodName like "kube-proxy") as pod4, (PodName like "opentelemetry-operator-controller-manager") as pod5, (PodName like "gatekeeper-controller-manager") as pod6, (PodName like "aws-load-balancer-controller") as pod7, (PodName like "cert-manager") as pod8, (PodName like "aws-for-fluent-bit") as pod9, (PodName like "container-insights-metrics-opentelemetry-collector-agent") as pod10, (PodName like "cert-manager-cainjector") as pod11, (PodName like "metrics-server") as pod12, (PodName like "csi-secrets-store-provider-aws") as pod13, (PodName like "csi-secrets-store-provider-aws-secrets-store-csi-driver") as pod14, (PodName like "aws-node") as pod15, (PodName like "gatekeeper-audit") as pod16
| filter Type = "Pod" and Namespace = "eks-baseline-services"
| stats max({metric} * pod1) as `cert-manager-webhook`, max({metric} * pod2) as `cluster-autoscaler-aws-cluster-autoscaler`, max({metric} * pod3) as `coredns`, max({metric} * pod4) as `kube-proxy`, max({metric} * pod5) as `opentelemetry-operator-controller-manager`, max({metric} * pod6) as `gatekeeper-controller-manager`, max({metric} * pod7) as `aws-load-balancer-controller`, max({metric} * pod8) as `cert-manager`, max({metric} * pod9) as `aws-for-fluent-bit`, max({metric} * pod10) as `container-insights-metrics-opentelemetry-collector-agent`, max({metric} * pod11) as `cert-manager-cainjector`, max({metric} * pod12) as `metrics-server`, max({metric} * pod13) as `csi-secrets-store-provider-aws`, max({metric} * pod14) as `csi-secrets-store-provider-aws-secrets-store-csi-driver`, max({metric} * pod15) as `aws-node`, max({metric} * pod16) as `gatekeeper-audit` by bin(1m)""",
        "iMetric": "pod_network_total_bytes",
    },
}


def test_format_query(mocker):
    assert format_query(EVENT, {}) == True
    assert (
        helper.Data["oFormattedQuery"]
        == """fields Type, pod_network_total_bytes, (PodName like "cert-manager-webhook") as pod1, (PodName like "cluster-autoscaler-aws-cluster-autoscaler") as pod2, (PodName like "coredns") as pod3, (PodName like "kube-proxy") as pod4, (PodName like "opentelemetry-operator-controller-manager") as pod5, (PodName like "gatekeeper-controller-manager") as pod6, (PodName like "aws-load-balancer-controller") as pod7, (PodName like "cert-manager") as pod8, (PodName like "aws-for-fluent-bit") as pod9, (PodName like "container-insights-metrics-opentelemetry-collector-agent") as pod10, (PodName like "cert-manager-cainjector") as pod11, (PodName like "metrics-server") as pod12, (PodName like "csi-secrets-store-provider-aws") as pod13, (PodName like "csi-secrets-store-provider-aws-secrets-store-csi-driver") as pod14, (PodName like "aws-node") as pod15, (PodName like "gatekeeper-audit") as pod16
| filter Type = "Pod" and Namespace = "eks-baseline-services"
| stats max(pod_network_total_bytes * pod1) as `cert-manager-webhook`, max(pod_network_total_bytes * pod2) as `cluster-autoscaler-aws-cluster-autoscaler`, max(pod_network_total_bytes * pod3) as `coredns`, max(pod_network_total_bytes * pod4) as `kube-proxy`, max(pod_network_total_bytes * pod5) as `opentelemetry-operator-controller-manager`, max(pod_network_total_bytes * pod6) as `gatekeeper-controller-manager`, max(pod_network_total_bytes * pod7) as `aws-load-balancer-controller`, max(pod_network_total_bytes * pod8) as `cert-manager`, max(pod_network_total_bytes * pod9) as `aws-for-fluent-bit`, max(pod_network_total_bytes * pod10) as `container-insights-metrics-opentelemetry-collector-agent`, max(pod_network_total_bytes * pod11) as `cert-manager-cainjector`, max(pod_network_total_bytes * pod12) as `metrics-server`, max(pod_network_total_bytes * pod13) as `csi-secrets-store-provider-aws`, max(pod_network_total_bytes * pod14) as `csi-secrets-store-provider-aws-secrets-store-csi-driver`, max(pod_network_total_bytes * pod15) as `aws-node`, max(pod_network_total_bytes * pod16) as `gatekeeper-audit` by bin(1m)"""
    )
