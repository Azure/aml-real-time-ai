# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
import time
import hashlib
import urllib
import os
from datetime import datetime, timedelta

from amlrealtimeai.authentication.aad_authentication import AADAuthentication
from amlrealtimeai.common.http_client import HttpClient
from azure.storage import CloudStorageAccount
from azure.storage.blob import BlockBlobService, BlobPermissions
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.storage.models import StorageAccountCreateParameters, Sku, Kind, SkuName
from msrest.authentication import BasicTokenAuthentication

_mgmnt_uri = "https://management.azure.com"

class DeploymentClient:
    def __init__(self, subscription_id, resource_group, account, http_client = None, discovery_http_client = None):
        self.__subscription_id = subscription_id
        self.__resource_group = resource_group
        self.__account = account
        self.__uri, self.__location = self.__discover_mms_endpoint(subscription_id, resource_group, account, discovery_http_client)
        self.__http_client = http_client if http_client is not None else HttpClient(self.__uri, token_refresh_fn)
        id = subscription_id + '_' + resource_group + '_' + account + '_' + self.__location
        self.__storage_account_name = ('fpga' + hashlib.md5(id.encode("utf-8")).hexdigest())[:24]
        self.__api_version = "2018-04-01-preview"

    def register_model(self, model_name, service_def):
        storage_account_key = self.__create_storage_account_and_get_key()
        cloud_storage_account = CloudStorageAccount(self.__storage_account_name, storage_account_key)

        print("Registering model " + model_name)
        url = self.__upload_model(model_name, service_def, cloud_storage_account)
        register_model_result = self.__register_model_with_mms(model_name, url)
        print("Successfully registered model " + model_name)
        return register_model_result['id']

    def create_service(self, service_name, model_id, ssl_enabled = False, ssl_certificate = None, ssl_key = None,
                       primary_key = None, secondary_key=None):
        """
        Create a service with a given name and model_id
        :param service_name: The name of the service to create.
        :param model_id: The id of the model to use to create the service.
        :param ssl_enabled: If the service should have ssl_enabled.
        :param ssl_certificate: A PEM encoded string which contains the full certificate chain.
        :param ssl_key: A PEM encoded string which contains the full certificate chain.
        :param primary_key: A string which will become the primary authentication key. If None, Azure ML will
        generate one for you.
        :param secondary_key: A string which will become the seondary authentication key. If None, Azure ML will
        generate one for you.
        :return: The created service.
        """
        print("Creating service " + service_name)

        # only single node deployments supported for now
        scale_units = 1

        service = self.__deploy_service(service_name, model_id, scale_units, ssl_enabled, ssl_certificate , ssl_key,
                                        primary_key, secondary_key)
        print("Successfully created service " + service_name)
        return service

    def update_service(self, service_id, model_id, ssl_enabled = None, ssl_certificate = None, ssl_key = None,
                       primary_key = None, secondary_key=None):
        """
        Update Service
        :param service_id: The id of the service to update
        :param model_id:  The id of the model to update the service to use
        :param ssl_enabled: If the service should use SSL. If None, the service will keep it's previous ssl behavior.
        ssl_certificate and ssl_key are required if True.
        :param ssl_certificate: A PEM encoded string which contains the full certificate chain. Required if ssl_enabled
        is True, does nothing if ssl_enabled is False
        :param ssl_key: A PEM encoded string which contains the certificate's private key. Required if ssl_enabled is
        True, does nothing if ssl_enabled is false
        :param primary_key: A string which will become the primary authentication key. If None, Azure ML will
        generate one for you.
        :param secondary_key: A string which will become the seondary authentication key. If None, Azure ML will
        generate one for you.
        :return: The updated service
        """
        print("Update service", service_id)

        num_replicas = 1

        if ssl_enabled and (ssl_certificate is None or ssl_key is None):
            raise ValueError("Must provide certificate and key if SSL is enabled")

        if ssl_certificate is None:
            ssl_certificate = ""

        if ssl_key is None:
            ssl_key = ""

        if primary_key is not None or secondary_key is not None:
            auth_keys = {"primaryKey":primary_key, "secondaryKey":secondary_key}
        else:
            auth_keys = None

        update_service_body = {
            "computeType": "FPGA",
            "modelId": model_id,
            "numReplicas": num_replicas,
        }

        if auth_keys is not None:
            update_service_body["keys"] = auth_keys

        # To update the ssl to be true, we need all 3. If we want to update the certificate or key, we again need all 3.
        # If we don't want to change the SSL behavior, the user passes None.

        if ssl_enabled is not None:
            update_service_body["sslEnabled"]=ssl_enabled
            update_service_body["sslCertificate"]=ssl_certificate
            update_service_body["sslKey"]=ssl_key

        update_response = self.__http_client.put(self.__get_operation_uri('services', service_id), json=update_service_body)
        request_id = update_response.headers["x-ms-client-request-id"]
        operation_location = update_response.headers["Operation-Location"]
        service_uri = self.__wait_for_async_operation("Update service", request_id, operation_location)
        service_get_response = self.__http_client.get(service_uri)
        print("Updated service", service_id)

        return Service(**service_get_response.json())


    def list_models(self):
        return self.__list_items('models', lambda x: Model(**x))


    def list_services(self):
        return self.__list_items('services', lambda x: Service(**x))


    def __list_items(self, operation, factory_fn):
        response_body = self.__http_client.get(self.__get_operation_uri(operation)).json()
        while(True):
            for x in response_body['value']:
                yield factory_fn(x)
            if('nextLink' in response_body):
                url = response_body['nextLink']
                if(not url.startswith(self.__http_client.host)):
                    raise RuntimeError(url + " invalid for pagination")
                res = url[len(self.__http_client.host):]
                response_body = self.__http_client.get(res).json()
            else:
                break


    def get_service_by_id(self, service_id):
        get_service_by_id_response = self.__http_client.get(self.__get_operation_uri('services', service_id))
        return Service(**get_service_by_id_response.json())


    def get_service_by_name(self, service_name):
        get_services_by_name_response = self.__http_client.get(self.__get_operation_uri('services', query_parameters={'serviceName': service_name}))
        services = [Service(**x) for x in get_services_by_name_response.json()['value']]
        if(any(services)):
            return self.get_service_by_id(services[0].id)
        else:
            return None


    def get_services_by_name(self, service_name):
        get_services_by_name_response = self.__http_client.get(self.__get_operation_uri('services', query_parameters={'serviceName': service_name}))
        return [Service(**x) for x in get_services_by_name_response.json()['value']]


    def delete_model(self, model_id):
        self.__http_client.delete(self.__get_operation_uri('models', model_id))


    def delete_service(self, service_id):
        delete_response = self.__http_client.delete(self.__get_operation_uri('services', service_id))
        request_id = delete_response.headers["x-ms-client-request-id"]
        operation_location = delete_response.headers["Operation-Location"]
        self.__wait_for_async_operation("Delete service", request_id, operation_location)

    def get_auth_keys(self, service_id):
        response = self.__http_client.get(self.__get_operation_uri('services', "{0}/keys".format(service_id)))
        return response.json()

    def regenerate_auth_keys(self, service_id, key_type:str=None):
        if key_type is not None:
            body = {"keyType": key_type}
        else:
            body = None
        response = self.__http_client.post(self.__get_operation_uri('services', "{0}/regenerateKeys".format(service_id)), json=body)
        return response.json()

    def __get_operation_uri(self, operation, resource_id = None, query_parameters = None):
        resource = operation if resource_id == None else operation + '/' + resource_id

        query = ''
        if(query_parameters != None):
            for k, v in query_parameters.items():
                query += '&' + k + '=' + v

        return '/api/subscriptions/' + self.__subscription_id + '/resourcegroups/' + self.__resource_group + '/accounts/' + self.__account + '/' + resource + '?api-version=' + self.__api_version + query

    def __upload_model(self, model_name, service_def, storage_account: CloudStorageAccount):
        if not os.path.isfile(service_def):
            raise FileNotFoundError(service_def + ' not found')

        storage_service = storage_account.create_block_blob_service()
        container_name = "models"
        storage_service.create_container(container_name)
        hash = self.__md5(service_def)
        blob_name = urllib.parse.quote(model_name) + "_" + hash
        storage_service.create_blob_from_path(container_name, blob_name, service_def)
        sas_token = storage_service.generate_blob_shared_access_signature(container_name, blob_name, BlobPermissions.READ, datetime.utcnow() + timedelta(days=365 * 5))
        return storage_service.make_blob_url(container_name, blob_name, sas_token=sas_token)

    def __register_model_with_mms(self, model_name, url):
        body = {
            "name": model_name,
            "mimeType": "application/zip",
            "url": url,
            "unpack": False
        }

        response = self.__http_client.post(self.__get_operation_uri('models'), json=body)
        return response.json()


    def __wait_for_async_operation(self, operation_friendly_name, original_request_id, operation_location):
        while True:
            operation_status_response = self.__http_client.get(operation_location + "?api-version=" + self.__api_version).json()
            if operation_status_response['state'] == 'Succeeded':
                print("")
                return operation_status_response['resourceLocation'] + "?api-version=" + self.__api_version
            if operation_status_response['state'] == 'Failed':
                print("")
                error_message = ""
                if 'error' in operation_status_response:
                    if 'message' in operation_status_response['error']:
                        error_message = operation_status_response['error']['message']
                    if 'details' in operation_status_response['error']:
                        error_details = json.dump(operation_status_response['error']['details'])
                raise AsyncOperationFailedException(operation_friendly_name, original_request_id, operation_status_response['operationType'], error_message, error_details, operation_status_response['id'], operation_status_response['resourceLocation'])
            print(". ", end="")
            time.sleep(5)


    def __create_storage_account_and_get_key(self):
        basic_token_auth = BasicTokenAuthentication({'access_token': token_refresh_fn()})
        client = StorageManagementClient(basic_token_auth, self.__subscription_id)

        storage_accounts = list(client.storage_accounts.list_by_resource_group(self.__resource_group))
        if(not any([x.name == self.__storage_account_name for x in storage_accounts])):
            print("Creating storage account", self.__storage_account_name)
            client.storage_accounts.create(
                self.__resource_group,
                self.__storage_account_name,
                StorageAccountCreateParameters(
                    sku=Sku(SkuName.standard_ragrs),
                    kind=Kind.storage,
                    location=self.__location
                )).result()
            print("Created storage account", self.__storage_account_name)

        storage_keys = client.storage_accounts.list_keys(self.__resource_group, self.__storage_account_name)
        storage_keys = {v.key_name: v.value for v in storage_keys.keys}

        return storage_keys['key1']


    def __deploy_service(self, name, model_id, num_replicas: int, ssl_enabled = False, ssl_certificate:str = None,
                         ssl_key:str = None, primary_key:str = None, secondary_key:str = None):

        if ssl_enabled and (ssl_certificate is None or ssl_key is None):
            raise ValueError("Must provide certificate and key if SSL is enabled")

        if ssl_certificate is None:
            ssl_certificate = ""

        if ssl_key is None:
            ssl_key = ""

        if primary_key is not None or secondary_key is not None:
            auth_keys = {
                "primaryKey" : primary_key,
                "secondaryKey" : secondary_key
            }
        else:
            auth_keys = None

        create_service_body = {
            "computeType": "FPGA",
            "modelId": model_id,
            "name": name,
            "numReplicas": num_replicas,
            "sslEnabled": ssl_enabled,
            "sslCertificate": ssl_certificate,
            "sslKey": ssl_key,
        }

        if auth_keys is not None:
            create_service_body["keys"] = auth_keys

        create_response = self.__http_client.post(self.__get_operation_uri('services'), json=create_service_body)
        request_id = create_response.headers["x-ms-client-request-id"]
        operation_location = create_response.headers["Operation-Location"]
        service_uri = self.__wait_for_async_operation("Create service", request_id, operation_location)
        service_get_response = self.__http_client.get(service_uri)
        service = Service(**service_get_response.json())
        
        if(service is None or service.state != 'Succeeded'):
            raise RuntimeError("Creating service failed")

        return service

    def __md5(self, file):
        hash_md5 = hashlib.md5()
        with open(file, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def __discover_mms_endpoint(self, subscription_id, resource_group, account, http_client):
        http_client = http_client if http_client is not None else HttpClient(_mgmnt_uri, token_refresh_fn)
        endpoint_lookup_response = http_client.get('/subscriptions/' + subscription_id + '/resourcegroups/' + resource_group + '/providers/Microsoft.MachineLearningModelManagement/accounts/' + account + '?api-version=2017-09-01-preview').json()
        mms_location = endpoint_lookup_response['properties']['modelManagementSwaggerLocation']
        end_pos = mms_location.index('/', len('https://'))
        return mms_location[:end_pos], endpoint_lookup_response['location']


class Service:
    def __init__(self, **entries):
        self.__dict__.update(entries)

class Model:
    def __init__(self, **entries):
        self.__dict__.update(entries)


class AsyncOperationFailedException(Exception):

    def __init__(self, friendly_operation_name, request_id, operation_type, error_message, error_details, operation_id, resource_location):
        self.__friendly_operation_name = friendly_operation_name
        self.__request_id = request_id
        self.__operation_type = operation_type
        self.__error_message = error_message
        self.__error_details = error_details
        self.__operation_id = operation_id
        self.__resource_location = resource_location

    def __str__(self):
        return format("{} failed with error {} ({}); Original request id: {}; {}; operation_id: {}; resource_location: {}", self.__friendly_operation_name, self.__error_message, self.__error_details, self.__request_id, self.__operation_type, self.__operation_id, self.__resource_location)
        

# Keep copy of refresh token in global memory for the entire process
refresh_token = None

def store_refresh_token(new_token):
    global refresh_token
    refresh_token = new_token

def load_refresh_token():
    global refresh_token
    return refresh_token

def token_refresh_fn():
    options = {
        "authuri": "https://login.microsoftonline.com",
        "tenant": "common",
        "clientid": "04b07795-8ddb-461a-bbee-02f9e1bf7b46",
        "resource": "https://management.core.windows.net/"
    }

    auth = AADAuthentication(options, lambda m: print(m), store_refresh_token, load_refresh_token)
    token = auth.acquire_token()

    return token
