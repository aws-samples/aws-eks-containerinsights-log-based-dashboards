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

from datetime import datetime

import aws_cdk as cdk
import yaml
from cdk_nag import AwsSolutionsChecks, NagPackSuppression, NagSuppressions
from cerberus import Validator

from cdk.ci_log_based_dashboard_stack import ContainerInsightsLogBasedDashboardStack


def _load_dashboard_configuration():
    """
    Validate the "dashboard_configuration.yaml" schema
    """

    dashboard_conf_filename = "dashboard_configuration.yaml"
    coerce_date = lambda d: datetime.strptime(d, "%Y-%m-%dT%H:%M:%S")
    with open(dashboard_conf_filename, "r", encoding="utf8") as dashboard_conf_yaml:
        schema = {
            "name": {"type": "string", "regex": "[A-Za-z0-9-_]+"},
            "clusterName": {"type": "string", "regex": "^[0-9A-Za-z][A-Za-z0-9\-_]+$"},
            "timeToLiveInMinutes": {"min": 1, "max": 43800},
            "investigationWindow": {
                "type": "dict",
                "schema": {
                    "from": {
                        "type": "datetime",
                        "coerce": coerce_date,
                    },
                    "to": {
                        "type": "datetime",
                        "coerce": coerce_date,
                    },
                },
            },
            "contents": {
                "type": "dict",
                "schema": {
                    "node": {
                        "type": "dict",
                        "schema": {
                            "enabled": {"type": "boolean"},
                            "metrics": {
                                "type": "list",
                                "schema": {
                                    "type": "string",
                                    "regex": "^node_.*",
                                },
                            },
                        },
                    },
                    "pod": {
                        "type": "dict",
                        "schema": {
                            "enabled": {"type": "boolean"},
                            "namespaces": {"type": "list"},
                            "metrics": {
                                "type": "list",
                                "schema": {
                                    "type": "string",
                                    "regex": "^pod_.*",
                                },
                            },
                        },
                    },
                    "container": {
                        "type": "dict",
                        "schema": {
                            "enabled": {"type": "boolean"},
                            "namespaces": {"type": "list"},
                            "metrics": {
                                "type": "list",
                                "schema": {
                                    "type": "string",
                                    "regex": "^[container_|number_of_container_restarts].*",
                                },
                            },
                        },
                    },
                },
            },
        }
        dashboard_conf = yaml.safe_load(dashboard_conf_yaml)
        validator = Validator(schema)
        if not validator.validate(dashboard_conf):
            raise Exception(
                f'Dashboards configuration file "{dashboard_conf_filename}" is invalid: {validator.errors}'
            )

    return dashboard_conf


dashboard_conf = _load_dashboard_configuration()

app = cdk.App(context={"dashboardConfiguration": dashboard_conf})
stack = ContainerInsightsLogBasedDashboardStack(
    app,
    "ContainerInsightsLogBasedDashboardStack",
    ttl=cdk.Duration.minutes(
        app.node.try_get_context("dashboardConfiguration")["timeToLiveInMinutes"]
    ),
    stack_name=app.node.try_get_context("dashboardConfiguration")["name"].replace(
        "_", "-"
    ),
)

cdk.Aspects.of(app).add(AwsSolutionsChecks(verbose=True))

NagSuppressions.add_stack_suppressions(
    stack,
    suppressions=[
        NagPackSuppression(
            id="AwsSolutions-IAM4",
            reason="Allow AWS Managed policies",
        )
    ],
)

app.synth()
