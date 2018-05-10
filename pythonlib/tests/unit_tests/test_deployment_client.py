# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License
import pytest
from unittest import mock

from amlrealtimeai.deployment_client import DeploymentClient, Service, Model
from amlrealtimeai.common.http_client import HttpClient


discovery_get_results = {
    "/subscriptions/test_subscription_id/resourcegroups/test_resource_group/providers/Microsoft.MachineLearningModelManagement/accounts/test_mma?api-version=2017-09-01-preview":
    { 'location': 'eastus2', 'properties': { 'modelManagementSwaggerLocation': 'http://management.azure.com/swagger.json' } }
}

discovery_http_client_mock = mock.Mock()
discovery_http_client_mock.get = mock.MagicMock(side_effect=lambda uri: get_response_mock(discovery_get_results[uri]))


def get_response_mock(obj):
    response_mock = mock.Mock()
    response_mock.json = mock.MagicMock(side_effect=lambda: obj)
    return response_mock


def get_operation_location_mock(location):
    response_mock = mock.Mock()
    response_mock.headers = {"Operation-Location":location}


def test_list_services():
    get_results = {
        "/api/subscriptions/test_subscription_id/resourcegroups/test_resource_group/accounts/test_mma/services?api-version=2018-04-01-preview":
            { 'value': [ { 'id': 1, 'name': 'my-service1'}, { 'id': 2, 'name': 'my-service2'} ], 'nextLink': "https://testhost.com/api/subscriptions/test_subscription_id/resourcegroups/test_resource_group/accounts/test_mma/services?api-version=2018-04-01-preview&$skipToken=123" },
        "/api/subscriptions/test_subscription_id/resourcegroups/test_resource_group/accounts/test_mma/services?api-version=2018-04-01-preview&$skipToken=123":
            { 'value': [ { 'id': 3, 'name': 'my-service3'} ] }
    }

    http_client_mock = mock.Mock()
    http_client_mock.host = "https://testhost.com"
    http_client_mock.get = mock.MagicMock(side_effect=lambda uri: get_response_mock(get_results[uri]))

    DeploymentClient._create_http_client = lambda self, uri: discovery_http_client_mock if uri is deployment_client._mgmnt_uri else http_client_mock
    client = DeploymentClient("test_subscription_id", "test_resource_group", "test_mma")

    service_list = list(client.list_services())

    assert len(service_list) == 3
    assert service_list[0].id == 1
    assert service_list[0].name == "my-service1"
    assert service_list[1].id == 2
    assert service_list[1].name == "my-service2"
    assert service_list[2].id == 3
    assert service_list[2].name == "my-service3"


def test_deploy_service_with_no_ssl_has_expected_json():
    client, http_client_mock = setup_mock_client_for_deploy()

    client.create_service("name","model_id")

    create_service_body = {
        "computeType": "FPGA",
        "modelId": "model_id",
        "name": "name",
        "numReplicas": 1,
        "sslEnabled": False,
        "sslCertificate": "",
        "sslKey": ""
    }

    assert_deploy_json(create_service_body, http_client_mock.post)


def test_deploy_service_with_ssl_has_expected_json():
    client, http_client_mock = setup_mock_client_for_deploy()

    client.create_service("name","model_id", True, "cert", "key")

    create_service_body = {
        "computeType": "FPGA",
        "modelId": "model_id",
        "name": "name",
        "numReplicas": 1,
        "sslEnabled": True,
        "sslCertificate": "cert",
        "sslKey": "key"
    }

    assert_deploy_json(create_service_body, http_client_mock.post)


def test_deploy_service_with_ssl_no_cert_throws():
    client, http_client_mock = setup_mock_client_for_deploy()

    with pytest.raises(ValueError) as ex:
        client.create_service("name","model_id", True, None, "key")

    assert "Must provide certificate and key" in str(ex.value)


def test_deploy_service_with_ssl_no_key_throws():
    client, http_client_mock = setup_mock_client_for_deploy()

    with pytest.raises(ValueError) as ex:
        client.create_service("name", "model_id", True, "cert", None)

    assert "Must provide certificate and key" in str(ex.value)


def test_deploy_service_with_ssl_no_cert_or_key_throws():
    client, http_client_mock = setup_mock_client_for_deploy()

    with pytest.raises(ValueError) as ex:
        client.create_service("name", "model_id", True)

    assert "Must provide certificate and key" in str(ex.value)


def assert_deploy_json(json, mock):
    mock.assert_called_with(
        "/api/subscriptions/test_subscription_id/resourcegroups/test_resource_group/accounts/test_mma/services?api"
        "-version=2018-04-01-preview",
        json=json)

def assert_update_json(json, mock):
    mock.assert_called_with(
        "/api/subscriptions/test_subscription_id/resourcegroups/test_resource_group/accounts/test_mma/services/name?api"
        "-version=2018-04-01-preview",
        json=json)

keys_uri="/api/subscriptions/test_subscription_id/resourcegroups/test_resource_group/accounts/test_mma/services/name/keys?api-version=2018-04-01-preview"
regenerate_keys_uri="/api/subscriptions/test_subscription_id/resourcegroups/test_resource_group/accounts/test_mma/services/name/regenerateKeys?api-version=2018-04-01-preview"


def setup_mock_client_for_deploy():
    http_client_mock = mock.Mock()
    http_client_mock.host = "https://testhost.com"
    http_client_mock.post = mock.MagicMock(get_operation_location_mock("service-id"))
    http_client_mock.put = mock.MagicMock(get_operation_location_mock("service-id"))
    http_client_mock.get = mock.MagicMock(
        return_value=get_response_mock({"state": "Succeeded", "resourceLocation": "location"}))

    DeploymentClient._create_http_client = lambda self, uri: discovery_http_client_mock if uri is deployment_client._mgmnt_uri else http_client_mock
    client = DeploymentClient("test_subscription_id", "test_resource_group", "test_mma")
    return client, http_client_mock


def test_update_service_with_unchanged_ssl_has_expected_json():
    client, http_client_mock = setup_mock_client_for_deploy()

    client.update_service("name","model_id")

    create_service_body = {
        "computeType": "FPGA",
        "modelId": "model_id",
        "numReplicas": 1
    }

    assert_update_json(create_service_body, http_client_mock.put)

def test_update_service_with_ssl_has_expected_json():
    client, http_client_mock = setup_mock_client_for_deploy()

    client.update_service("name","model_id", True, "cert", "key")

    create_service_body = {
        "computeType": "FPGA",
        "modelId": "model_id",
        "numReplicas": 1,
        "sslEnabled": True,
        "sslCertificate": "cert",
        "sslKey": "key"
    }

    assert_update_json(create_service_body, http_client_mock.put)


def test_update_service_disabling_ssl_has_expected_json():
    client, http_client_mock = setup_mock_client_for_deploy()

    client.update_service("name","model_id", False)

    create_service_body = {
        "computeType": "FPGA",
        "modelId": "model_id",
        "numReplicas": 1,
        "sslEnabled": False,
        "sslCertificate": "",
        "sslKey": ""
    }

    assert_update_json(create_service_body, http_client_mock.put)

def test_update_service_disabling_ssl_has_expected_json_with_cert_key():
    client, http_client_mock = setup_mock_client_for_deploy()

    client.update_service("name","model_id", False, "Cert", "Key")

    create_service_body = {
        "computeType": "FPGA",
        "modelId": "model_id",
        "numReplicas": 1,
        "sslEnabled": False,
        "sslCertificate": "Cert",
        "sslKey": "Key"
    }

    assert_update_json(create_service_body, http_client_mock.put)


def test_update_service_with_unchanged_ssl_has_expected_json_with_cert_key():
    client, http_client_mock = setup_mock_client_for_deploy()

    client.update_service("name","model_id", ssl_certificate="cert", ssl_key="key")

    create_service_body = {
        "computeType": "FPGA",
        "modelId": "model_id",
        "numReplicas": 1
    }

    assert_update_json(create_service_body, http_client_mock.put)


def test_update_service_with_ssl_no_cert_throws():
    client, http_client_mock = setup_mock_client_for_deploy()

    with pytest.raises(ValueError) as ex:
        client.update_service("name","model_id", True, None, "key")

    assert "Must provide certificate and key" in str(ex.value)


def test_update_service_with_ssl_no_key_throws():
    client, http_client_mock = setup_mock_client_for_deploy()

    with pytest.raises(ValueError) as ex:
        client.update_service("name", "model_id", True, "cert", None)

    assert "Must provide certificate and key" in str(ex.value)


def test_update_service_with_ssl_no_cert_or_key_throws():
    client, http_client_mock = setup_mock_client_for_deploy()

    with pytest.raises(ValueError) as ex:
        client.update_service("name", "model_id", True)

    assert "Must provide certificate and key" in str(ex.value)


def test_update_service_primary_key_has_expected_json():
    client, http_client_mock = setup_mock_client_for_deploy()

    client.update_service("name","model_id", primary_key="key1")

    create_service_body = {
        "computeType": "FPGA",
        "modelId": "model_id",
        "numReplicas": 1,
        "keys" : {"primaryKey": "key1",
                 "secondaryKey": None}
    }

    assert_update_json(create_service_body, http_client_mock.put)

def test_update_service_secondary_key_has_expected_json():
    client, http_client_mock = setup_mock_client_for_deploy()

    client.update_service("name","model_id", secondary_key="key2")

    create_service_body = {
        "computeType": "FPGA",
        "modelId": "model_id",
        "numReplicas": 1,
        "keys" : {"secondaryKey": "key2",
                 "primaryKey": None}
    }

    assert_update_json(create_service_body, http_client_mock.put)

def test_update_service_both_keys_has_expected_json():
    client, http_client_mock = setup_mock_client_for_deploy()

    client.update_service("name","model_id", primary_key="key1", secondary_key="key2")

    create_service_body = {
        "computeType": "FPGA",
        "modelId": "model_id",
        "numReplicas": 1,
        "keys" : {"secondaryKey": "key2",
                 "primaryKey": "key1"}
    }

    assert_update_json(create_service_body, http_client_mock.put)

def test_deploy_service_with_primary_key_has_expected_json():
    client, http_client_mock = setup_mock_client_for_deploy()

    client.create_service("name","model_id", True, "cert", "key", "key1")

    create_service_body = {
        "computeType": "FPGA",
        "modelId": "model_id",
        "name": "name",
        "numReplicas": 1,
        "sslEnabled": True,
        "sslCertificate": "cert",
        "sslKey": "key",
        "keys":{"primaryKey":"key1",
                "secondaryKey":None}
    }

    assert_deploy_json(create_service_body, http_client_mock.post)

def test_deploy_service_with_secondary_key_has_expected_json():
    client, http_client_mock = setup_mock_client_for_deploy()

    client.create_service("name","model_id", True, "cert", "key", secondary_key="key2")

    create_service_body = {
        "computeType": "FPGA",
        "modelId": "model_id",
        "name": "name",
        "numReplicas": 1,
        "sslEnabled": True,
        "sslCertificate": "cert",
        "sslKey": "key",
        "keys":{"primaryKey":None,
                "secondaryKey": "key2"}
    }

    assert_deploy_json(create_service_body, http_client_mock.post)

def test_deploy_service_with_both_keys_has_expected_json():
    client, http_client_mock = setup_mock_client_for_deploy()

    client.create_service("name","model_id", True, "cert", "key", "key1","key2")

    create_service_body = {
        "computeType": "FPGA",
        "modelId": "model_id",
        "name": "name",
        "numReplicas": 1,
        "sslEnabled": True,
        "sslCertificate": "cert",
        "sslKey": "key",
        "keys":{"primaryKey":"key1",
                "secondaryKey": "key2"}
    }

    assert_deploy_json(create_service_body, http_client_mock.post)


def test_get_keys_has_expected_response():
    client, http_client_mock = setup_mock_client_for_deploy()
    client.get_auth_keys("name")

    http_client_mock.get.assert_called_with(keys_uri)


def test_regenerate_keys_has_expected_json():
    client, http_client_mock = setup_mock_client_for_deploy()
    client.regenerate_auth_keys("name","Primary")

    http_client_mock.post.assert_called_with(regenerate_keys_uri,json={"keyType":"Primary"})

def test_regenerate_keys_has_sends_empty_if_called_with_none():
    client, http_client_mock = setup_mock_client_for_deploy()
    client.regenerate_auth_keys("name")

    http_client_mock.post.assert_called_with(regenerate_keys_uri,json=None)


def test_print_service():
    service = Service(id="id", state="Success", ip="0.0.0.0", port=80)
    assert r'{"id": "id", "state": "Success", "ip": "0.0.0.0", "port": 80}' == service.__str__()

def test_repr_service():
    service = Service(id="id", state="Success", ip="0.0.0.0", port=80)
    assert r"Service({'id': 'id', 'state': 'Success', 'ip': '0.0.0.0', 'port': 80})" == service.__repr__()

def test_print_model():
    model = Model(id="id", state="Success", name="new_model")
    assert r'{"id": "id", "state": "Success", "name": "new_model"}' == model.__str__()

def test_repr_model():
    model = Model(id="id", state="Success", name="new_model")
    assert r"Model({'id': 'id', 'state': 'Success', 'name': 'new_model'})" == model.__repr__()
