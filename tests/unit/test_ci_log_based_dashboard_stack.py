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

import json
import os
from typing import Any, Dict

import aws_cdk as cdk
import aws_cdk.assertions as assertions
import pytest
import yaml

from cdk.ci_log_based_dashboard_stack import ContainerInsightsLogBasedDashboardStack


def test_snapshot(mocker):
    stack = _init_stack(mocker)

    template = assertions.Template.from_stack(stack)

    _dump_json_snapshot(stack.stack_name, template.to_json())

    template.template_matches(_load_json_snapshot(stack.stack_name))


@pytest.mark.parametrize(
    "node_conf",
    [
        {"metrics": []},
        {"enabled": False},
        {"metrics": ["node_metric_1"]},
        {
            "metrics": [
                "node_metric_1",
                "node_metric_2",
                "node_metric_3",
                "node_metric_4",
                "node_metric_5",
            ]
        },
    ],
)
@pytest.mark.parametrize(
    "pod_conf",
    [
        {"metrics": []},
        {"enabled": False},
        {"namespaces": []},
        {"metrics": ["pod_metric_1"], "namespaces": ["kube-system"]},
        {
            "metrics": [
                "pod_metric_1",
                "pod_metric_2",
                "pod_metric_3",
                "pod_metric_4",
                "pod_metric_5",
            ],
            "namespaces": ["kube-system"],
        },
        {"metrics": ["pod_metric_1"], "namespaces": ["kube-system", "amazon-metrics"]},
        {
            "metrics": [
                "pod_metric_1",
                "pod_metric_2",
                "pod_metric_3",
                "pod_metric_4",
                "pod_metric_5",
            ],
            "namespaces": ["kube-system", "amazon-metrics"],
        },
    ],
)
@pytest.mark.parametrize(
    "container_conf",
    [
        {"metrics": []},
        {"enabled": False},
        {"namespaces": []},
        {"metrics": ["container_metric_1"], "namespaces": ["kube-system"]},
        {
            "metrics": [
                "container_metric_1",
                "container_metric_2",
                "container_metric_3",
                "container_metric_4",
                "container_metric_5",
            ],
            "namespaces": ["kube-system"],
        },
        {
            "metrics": ["container_metric_1"],
            "namespaces": ["kube-system", "amazon-metrics"],
        },
        {
            "metrics": [
                "container_metric_1",
                "container_metric_2",
                "container_metric_3",
                "container_metric_4",
                "container_metric_5",
            ],
            "namespaces": ["kube-system", "amazon-metrics"],
        },
    ],
)
def test_configuration(mocker, node_conf, pod_conf, container_conf):
    stack = _init_stack(
        mocker,
        {
            "dashboardConfiguration": {
                "contents": {
                    "node": node_conf,
                    "pod": pod_conf,
                    "container": container_conf,
                }
            }
        },
    )

    node_conf = stack.node.try_get_context("dashboardConfiguration")["contents"]["node"]
    pod_conf = stack.node.try_get_context("dashboardConfiguration")["contents"]["pod"]
    container_conf = stack.node.try_get_context("dashboardConfiguration")["contents"][
        "container"
    ]

    template = assertions.Template.from_stack(stack)
    template.resource_count_is(
        "Custom::ContainerInsights-NodeMetricQuery",
        0 if not node_conf["enabled"] else 1,
    )
    template.resource_count_is(
        "Custom::ContainerInsights-PodMetricQuery",
        0 if not pod_conf["enabled"] else len(pod_conf["namespaces"]),
    )
    template.resource_count_is(
        "Custom::ContainerInsights-ContainerMetricQuery",
        0 if not container_conf["enabled"] else len(container_conf["namespaces"]),
    )
    template.resource_count_is(
        "Custom::ContainerInsights-MetricQueryFormatter",
        (0 if not node_conf["enabled"] else 1) * len(node_conf["metrics"])
        + (0 if not pod_conf["enabled"] else 1)
        * len(pod_conf["namespaces"])
        * len(pod_conf["metrics"])
        + (0 if not container_conf["enabled"] else 1)
        * len(container_conf["namespaces"])
        * len(container_conf["metrics"]),
    )
    template.resource_count_is(
        "AWS::CloudWatch::Dashboard",
        (0 if not node_conf["enabled"] else 1)
        + (0 if not pod_conf["enabled"] else len(pod_conf["namespaces"]))
        + (0 if not container_conf["enabled"] else len(container_conf["namespaces"])),
    )


# ======================================
# Test tools
# ======================================
def _init_stack(mocker, cdk_context_override: Dict[Any, str] = {}) -> cdk.Stack:
    def create_lambda_function(**kwargs):
        """
        The PythonFunction construct required Docker which is heavyweigh for unit testing.
        Let's mock it with a plain Function construct for mere testability purposes.
        """
        return cdk.aws_lambda.Function(
            scope=kwargs["scope"],
            id=kwargs["id"],
            description=kwargs["description"],
            timeout=kwargs["timeout"],
            runtime=kwargs["runtime"],
            code=cdk.aws_lambda.Code.from_asset(kwargs["entry"]),
            handler=kwargs["handler"],
            initial_policy=kwargs["initial_policy"],
        )

    mocker.patch(
        "cdk.ci_log_based_dashboard_stack.PythonFunction",
        side_effect=create_lambda_function,
    )
    app = cdk.App(context=_load_cdk_context(cdk_context_override=cdk_context_override))
    return ContainerInsightsLogBasedDashboardStack(
        scope=app,
        construct_id="ContainerInsightsLogBasedDashboardStack",
        ttl=cdk.Duration.minutes(5),
    )


def _load_cdk_context(cdk_context_override: Dict[Any, str] = {}) -> Dict[Any, str]:
    with open(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..",
            "resources",
            "dashboard_configuration.yaml",
        ),
        "r",
        encoding="utf8",
    ) as dashboard_conf_yaml:
        dashboard_conf = yaml.safe_load(dashboard_conf_yaml)

    return _deep_merge({"dashboardConfiguration": dashboard_conf}, cdk_context_override)


def _deep_merge(a: Dict, b: Dict, path: str = None):
    if path is None:
        path = []
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                _deep_merge(a[key], b[key], path + [str(key)])
            else:
                a[key] = b[key]
        else:
            a[key] = b[key]
    return a


def _load_json_snapshot(snapshot_name: str) -> Dict[str, Any]:
    with open(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..",
            "resources",
            f"{snapshot_name}.snapshot.json",
        ),
        encoding="utf-8",
    ) as json_file:
        snapshot = json.load(json_file)

    # S3Key cannot be statically asserted, it is OK to match any value there.
    _deep_update("S3Key", assertions.Match.any_value(), snapshot)

    return snapshot


def _deep_update(target_key: str, new_value: Any, to_be_updated_dict: Dict[str, Any]):
    """Recursively replace a given target key in a dictionary in-place"""
    for k, v in to_be_updated_dict.items():
        if k == target_key:
            to_be_updated_dict[k] = new_value
        elif isinstance(v, dict):
            _deep_update(target_key, new_value, v)


def _dump_json_snapshot(snapshot_name: str, template: Dict[str, Any]) -> str:
    path_to_new_snapshot = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "resources",
        f"{snapshot_name}.snapshot.new.json",
    )
    with open(
        path_to_new_snapshot,
        "w",
        encoding="utf-8",
    ) as json_file:
        json_file.write(json.dumps(template, indent=4))

    return path_to_new_snapshot
