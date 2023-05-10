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


class NodeMetricQueryGenerator(MetricQueryGenerator):
    """Concrete implementation of the Node specific Metric Query Generator class."""

    QUERY_TEMPLATE = (
        "fields {metric}, "
        "{% for node_name in node_names %}"
        '(NodeName = \\"{{ node_name }}\\") as node{{ loop.index }}{{ ", " if not loop.last else " " }}'
        "{% endfor %}"
        '| filter (Type = \\"Node\\" or Type = \\"NodeNet\\" or Type = \\"NodeFS\\" or Type = \\"NodeDiskIO\\") and ispresent({metric}) '
        "| stats "
        "{% for node_name in node_names %}"
        'sum({metric} * node{{ loop.index }}) / sum(node{{ loop.index }}) as `{{ node_name }}`{{ ", " if not loop.last else " " }}'
        "{% endfor %}"
        "by bin({{ period }})"
    )

    def generate_lookup_query(self, event) -> str:
        """The Node lookup query is about retrieving all the node names."""

        return 'fields NodeName | filter Type = "Node" | stats count() by NodeName'

    def generate_metric_query(self, event, response) -> str:
        """
        Thanks to the results collected via the lookup query, we can render the Node metric
        query.
        This query is not metric-specific but it is specific to node metrics.
        The query will be formatted for a specific node metric at a later stage thanks to
        the Custom::ContainerInsights-MetricQueryFormatter resource.
        """

        node_names = [
            field["value"]
            for result in response["results"]
            for field in result
            if field["field"] == "NodeName"
        ]

        query_template = Environment(loader=BaseLoader()).from_string(
            NodeMetricQueryGenerator.QUERY_TEMPLATE
        )
        return query_template.render(
            node_names=node_names,
            aggregation_function="max",
            period="1m",
        )
