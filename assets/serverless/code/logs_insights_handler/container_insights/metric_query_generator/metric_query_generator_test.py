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

import container_insights.metric_query_generator
import pytest
from botocore.stub import ANY, Stubber

EVENT = {
    "RequestType": "Create",
    "ResourceProperties": {
        "iLogGroupName": "/aws/containerinsights/eks-cluster/performance",
        "iNamespace": "eks-baseline-services",
        "iStartTime": "2022-12-19T12:00:00",
        "iEndTime": "2022-12-19T23:00:00",
    },
}

POLL_EVENT = {
    "RequestType": "Create",
    "ResourceProperties": {
        "iLogGroupName": "/aws/containerinsights/eks-cluster/performance",
        "iNamespace": "eks-baseline-services",
        "iStartTime": "2022-12-19T12:00:00",
        "iEndTime": "2022-12-19T23:00:00",
    },
    "CrHelperData": {"PhysicalResourceId": "ca588a23-3279-4341-adcf-87d39ea4fac3"},
}


def test_create_query(mocker):
    dummy_log_insights_lookup_query = "dummy log insights lookup query"

    metric_query_generator_mock = mocker.MagicMock()
    metric_query_generator_mock.generate_lookup_query.return_value = (
        dummy_log_insights_lookup_query
    )

    container_insights.metric_query_generator.METRIC_QUERY_GENERATOR = (
        metric_query_generator_mock
    )

    logs_stubber = Stubber(container_insights.metric_query_generator.LOGS_CLIENT)
    logs_stubber.add_response(
        "start_query",
        {
            "ResponseMetadata": {
                "HTTPStatusCode": 200,
            },
            "queryId": "ca588a23-3279-4341-adcf-87d39ea4fac3",
        },
        {
            "logGroupName": "/aws/containerinsights/eks-cluster/performance",
            "queryString": dummy_log_insights_lookup_query,
            "startTime": ANY,
            "endTime": ANY,
        },
    )

    with logs_stubber:
        assert (
            container_insights.metric_query_generator.create_query(EVENT, {})
            == "ca588a23-3279-4341-adcf-87d39ea4fac3"
        )

    logs_stubber.assert_no_pending_responses()

    metric_query_generator_mock.generate_lookup_query.assert_called_once_with(EVENT)


def test_create_query_error(mocker):
    dummy_log_insights_lookup_query = "dummy log insights lookup query"

    metric_query_generator_mock = mocker.MagicMock()
    metric_query_generator_mock.generate_lookup_query.return_value = (
        dummy_log_insights_lookup_query
    )

    container_insights.metric_query_generator.METRIC_QUERY_GENERATOR = (
        metric_query_generator_mock
    )

    logs_stubber = Stubber(container_insights.metric_query_generator.LOGS_CLIENT)
    logs_stubber.add_client_error("start_query")

    with logs_stubber, pytest.raises(Exception) as ex_info:
        container_insights.metric_query_generator.create_query(EVENT, {})

    logs_stubber.assert_no_pending_responses()
    assert (
        f'Could not start query "{dummy_log_insights_lookup_query}", against log group "{EVENT["ResourceProperties"]["iLogGroupName"]}"'
        in str(ex_info.value)
    )


def test_poll_create_query(mocker):
    dummy_get_query_result_response = {
        "results": [[{"field": "dummy"}]],
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
    dummy_log_insights_metric_query = "dummy log insights metric query"

    metric_query_generator_mock = mocker.MagicMock()
    metric_query_generator_mock.generate_metric_query.return_value = (
        dummy_log_insights_metric_query
    )

    container_insights.metric_query_generator.METRIC_QUERY_GENERATOR = (
        metric_query_generator_mock
    )

    logs_stubber = Stubber(container_insights.metric_query_generator.LOGS_CLIENT)
    logs_stubber.add_response(
        "get_query_results",
        dummy_get_query_result_response,
        {
            "queryId": POLL_EVENT["CrHelperData"]["PhysicalResourceId"],
        },
    )

    with logs_stubber:
        assert (
            container_insights.metric_query_generator.poll_create_query(POLL_EVENT, {})
            == True
        )

    logs_stubber.assert_no_pending_responses()

    metric_query_generator_mock.generate_metric_query.assert_called_once_with(
        POLL_EVENT, dummy_get_query_result_response
    )

    assert (
        container_insights.metric_query_generator.helper.Data["oQuery"]
        == dummy_log_insights_metric_query
    )


def test_poll_create_query_status_running(mocker):
    dummy_get_query_result_response = {
        "statistics": {
            "recordsMatched": 28760.0,
            "recordsScanned": 232956.0,
            "bytesScanned": 346272125.0,
        },
        "status": "Running",
        "ResponseMetadata": {
            "HTTPStatusCode": 200,
        },
    }
    dummy_log_insights_metric_query = "dummy log insights metric query"

    metric_query_generator_mock = mocker.MagicMock()
    metric_query_generator_mock.generate_metric_query.return_value = (
        dummy_log_insights_metric_query
    )

    container_insights.metric_query_generator.METRIC_QUERY_GENERATOR = (
        metric_query_generator_mock
    )

    logs_stubber = Stubber(container_insights.metric_query_generator.LOGS_CLIENT)
    logs_stubber.add_response(
        "get_query_results",
        dummy_get_query_result_response,
        {
            "queryId": POLL_EVENT["CrHelperData"]["PhysicalResourceId"],
        },
    )

    with logs_stubber:
        assert (
            container_insights.metric_query_generator.poll_create_query(POLL_EVENT, {})
            == False
        )

    logs_stubber.assert_no_pending_responses()

    assert not metric_query_generator_mock.generate_metric_query.called


def test_poll_create_query_error(mocker):
    dummy_log_insights_metric_query = "dummy log insights metric query"

    metric_query_generator_mock = mocker.MagicMock()
    metric_query_generator_mock.generate_metric_query.return_value = (
        dummy_log_insights_metric_query
    )

    container_insights.metric_query_generator.METRIC_QUERY_GENERATOR = (
        metric_query_generator_mock
    )

    logs_stubber = Stubber(container_insights.metric_query_generator.LOGS_CLIENT)
    logs_stubber.add_client_error("get_query_results")

    with logs_stubber, pytest.raises(Exception) as ex_info:
        container_insights.metric_query_generator.poll_create_query(POLL_EVENT, {})

    logs_stubber.assert_no_pending_responses()

    assert not metric_query_generator_mock.generate_metric_query.called
    assert (
        f'Could not get query results for query ID "{POLL_EVENT["CrHelperData"]["PhysicalResourceId"]}"'
        in str(ex_info.value)
    )


def test_poll_create_query_status_failed(mocker):
    dummy_get_query_result_response = {
        "results": [[{"field": "dummy"}]],
        "statistics": {
            "recordsMatched": 28760.0,
            "recordsScanned": 232956.0,
            "bytesScanned": 346272125.0,
        },
        "status": "Failed",
        "ResponseMetadata": {
            "HTTPStatusCode": 200,
        },
    }
    dummy_log_insights_metric_query = "dummy log insights metric query"

    metric_query_generator_mock = mocker.MagicMock()
    metric_query_generator_mock.generate_metric_query.return_value = (
        dummy_log_insights_metric_query
    )

    container_insights.metric_query_generator.METRIC_QUERY_GENERATOR = (
        metric_query_generator_mock
    )

    logs_stubber = Stubber(container_insights.metric_query_generator.LOGS_CLIENT)
    logs_stubber.add_response(
        "get_query_results",
        dummy_get_query_result_response,
        {
            "queryId": POLL_EVENT["CrHelperData"]["PhysicalResourceId"],
        },
    )

    with logs_stubber, pytest.raises(Exception) as ex_info:
        container_insights.metric_query_generator.poll_create_query(POLL_EVENT, {})

    logs_stubber.assert_no_pending_responses()

    assert not metric_query_generator_mock.generate_metric_query.called
    assert (
        f'Unexpected query status "Failed" for query ID "{POLL_EVENT["CrHelperData"]["PhysicalResourceId"]}"'
        in str(ex_info.value)
    )


def test_poll_create_query_no_results(mocker):
    dummy_get_query_result_response = {
        "results": [],
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
    dummy_log_insights_metric_query = "dummy log insights metric query"

    metric_query_generator_mock = mocker.MagicMock()
    metric_query_generator_mock.generate_metric_query.return_value = (
        dummy_log_insights_metric_query
    )

    container_insights.metric_query_generator.METRIC_QUERY_GENERATOR = (
        metric_query_generator_mock
    )

    logs_stubber = Stubber(container_insights.metric_query_generator.LOGS_CLIENT)
    logs_stubber.add_response(
        "get_query_results",
        dummy_get_query_result_response,
        {
            "queryId": POLL_EVENT["CrHelperData"]["PhysicalResourceId"],
        },
    )

    with logs_stubber, pytest.raises(Exception) as ex_info:
        container_insights.metric_query_generator.poll_create_query(POLL_EVENT, {})

    logs_stubber.assert_no_pending_responses()

    assert not metric_query_generator_mock.generate_metric_query.called
    assert (
        f'Query ID "{POLL_EVENT["CrHelperData"]["PhysicalResourceId"]}" didnt return any result, please double check the correctness of the provided investigation window'
        in str(ex_info.value)
    )
