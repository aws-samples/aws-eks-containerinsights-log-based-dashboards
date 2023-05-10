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

from container_insights.metric_query_generator import MetricQueryGenerator
from jinja2 import BaseLoader, Environment


class ContainerMetricQueryGenerator(MetricQueryGenerator):
    """Concrete implementation of the Container specific Metric Query Generator class."""

    QUERY_TEMPLATE = (
        "fields {metric}, "
        "{% for pod_name in pod_container_mapping.keys() %}"
        '(PodName = \\"{{ pod_name }}\\") as pod{{ loop.index }}, '
        "{% endfor %}"
        "{% for container_name in container_names %}"
        '(kubernetes.container_name = \\"{{ container_name }}\\") as container{{ loop.index }}{{ ", " if not loop.last else " " }}'
        "{% endfor %}"
        '| filter (Type = \\"Container\\" or Type = \\"ContainerFS\\") and Namespace = \\"{{ namespace }}\\" and ispresent({metric}) '
        "| stats "
        "{% for pod_name in pod_container_mapping.keys() %}"
        "{% set outer_loop = loop %}"
        "{% for container_name in pod_container_mapping[pod_name] %}"
        'sum({metric} * pod{{ outer_loop.index }} * container{{ container_names.index(container_name) + 1 }}) / sum(pod{{ outer_loop.index }} * container{{ container_names.index(container_name) + 1 }}) as `{{ pod_name }} {{ container_name }}`{{ ", " if not (loop.last and outer_loop.last) else " " }}'
        "{% endfor %}"
        "{% endfor %}"
        "by bin({{ period }})"
    )

    def generate_lookup_query(self, event) -> str:
        """
        The Container lookup query is about retrieving all the container names as well as
        their mapping with pod names.
        """

        return (
            'fields PodName, kubernetes.container_name | filter Type = "Container" and Namespace = "{namespace}" | stats count() by PodName, kubernetes.container_name'
        ).format(namespace=event["ResourceProperties"]["iNamespace"])

    def generate_metric_query(self, event, response) -> str:
        """
        Thanks to the results collected via the lookup query, we can render the Container
        metric query.
        This query is not metric-specific but it is specific to container metrics.
        The query will be formatted for a specific container metric at a later stage
        thanks to the Custom::ContainerInsights-MetricQueryFormatter resource.
        """

        pod_container_mapping = dict()

        for result in response["results"]:
            pod_name = next(
                field["value"] for field in result if field["field"] == "PodName"
            )
            pod_container_mapping[pod_name] = pod_container_mapping.get(
                pod_name, list()
            )

            container_name = next(
                field["value"]
                for field in result
                if field["field"] == "kubernetes.container_name"
            )
            pod_container_mapping[pod_name].append(container_name)

        query_template = Environment(loader=BaseLoader()).from_string(
            ContainerMetricQueryGenerator.QUERY_TEMPLATE
        )
        return query_template.render(
            namespace=event["ResourceProperties"]["iNamespace"],
            container_names=sorted(
                {
                    container
                    for containers in pod_container_mapping.values()
                    for container in containers
                }
            ),
            pod_container_mapping=pod_container_mapping,
            aggregation_function="max",
            period="1m",
        )
