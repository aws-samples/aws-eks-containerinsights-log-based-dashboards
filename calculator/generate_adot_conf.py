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

import argparse
import json
import os

import jinja2
import pandas
import yaml

METRICS_TABLE_ROW_ID = 39
DIMENSIONS_COLUMN_IDS = list(range(3, 8))
DIMENSIONS_ROW_IDS = list(range(40, 178))
METRIC_TYPE_FILTERS = {
    "Node": ["node_cpu", "node_memory", "node_network", "node_number"],
    "NodeFS": ["node_filesystem"],
    "NodeDiskIO": ["node_diskio"],
    "NodeNet": ["node_interface_network"],
    "Pod": ["pod_cpu", "pod_memory", "pod_network", "pod_number", "pod_status"],
    "PodNet": ["pod_interface_network"],
    "Container": [
        "container_cpu",
        "container_memory",
        "container_status",
        "number_of_container",
    ],
    "ContainerFS": ["container_filesystem"],
    "Cluster": ["cluster"],
    "ClusterService": ["service"],
    "ClusterNamespace": ["namespace"],
}

parser = argparse.ArgumentParser(
    prog="generate_adot_conf",
    description="Generate ContainerInsights ADOT configuration from a calculator xls spreadsheet",
)
parser.add_argument(
    "-r",
    "--region",
    required=True,
    help="Name of the AWS region where the EKS cluster has been provisioned. (eg. eu-central-1)",
)
parser.add_argument(
    "-c",
    "--cluster-name",
    required=True,
    help="Name of the EKS cluster where the ADOT configuration will be installed.",
)
parser.add_argument(
    "-f",
    "--calculator-file",
    required=True,
    help="Path to the ContainerInsights calculator xls spreadsheet.",
)
args = parser.parse_args()

container_insights_calculator: pandas.DataFrame = pandas.read_excel(
    args.calculator_file, skiprows=list(range(0, METRICS_TABLE_ROW_ID))
)

# Select the metric types to be filtered
filter_metric_types = container_insights_calculator.loc[
    container_insights_calculator["EMF"] == "No", "Type"
].values

# Forward fill merged cells
container_insights_calculator.loc[:, "Type"].fillna(method="ffill", inplace=True)
container_insights_calculator.loc[:, "EMF"].fillna(method="ffill", inplace=True)
# Replace N/A values with "No"
container_insights_calculator.fillna(value="No", inplace=True)
# Disable metrics where EMF raw data has been disabled as a whole
container_insights_calculator.iloc[
    container_insights_calculator["EMF"] == "No", DIMENSIONS_COLUMN_IDS
] = "No"

# replace "Yes" values echoing the column header
container_insights_calculator.iloc[
    :, DIMENSIONS_COLUMN_IDS
] = container_insights_calculator.iloc[:, DIMENSIONS_COLUMN_IDS].replace(
    "Yes",
    pandas.Series(
        container_insights_calculator.columns, container_insights_calculator.columns
    ),
)

# Create an additional "Dimensions" column to the dataset where the single applicable
# dimensions are aggregated in JSON format
container_insights_calculator["Dimensions"] = container_insights_calculator.iloc[
    :, DIMENSIONS_COLUMN_IDS
].apply(
    lambda row: f"[{', '.join([v for v in row.values if v != 'No'])}]",
    axis=1,
)

# Filter out metrics that have no associated dimensions
container_insights_calculator = container_insights_calculator[
    (container_insights_calculator["Dimensions"] != "[]")
]

# Group By type and aggregated dimensions
metric_declarations = container_insights_calculator.groupby(["Type", "Dimensions"])[
    "Metric"
].apply(list)


loader = jinja2.FileSystemLoader(os.path.dirname(os.path.realpath(__file__)))
env = jinja2.Environment(autoescape=False, loader=loader)
template = env.get_template("adot_conf.yaml.j2")

print(
    template.render(
        region=args.region,
        cluster_name=args.cluster_name,
        filter_metric_types=yaml.safe_dump(
            [f"^{f}.*" for t in filter_metric_types for f in METRIC_TYPE_FILTERS[t]]
        ),
        metric_declarations=yaml.safe_dump(
            [
                {"dimensions": json.loads(d[1]), "metric_name_selectors": m}
                for d, m in metric_declarations.to_dict().items()
            ],
        ),
    )
)
