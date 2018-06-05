# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License
import os
import json
import glob
import requests
import zipfile

from collections import namedtuple
from datetime import datetime, timezone
from dateutil.parser import parse

from amlrealtimeai import deployment_client

def cleanup_old_test_services(client):
    msg = "SVC: "

    for service in client.list_services():
        msg = msg + service.name + "; "
        print(service.name)

        # if(not service.name.startswith('int-test-')):
        #     continue
        # service = client.get_service_by_id(service.id)
        # offset = datetime.now(timezone.utc) - parse(service.createdAt)
        # if(offset.seconds > 3600):
        #     try:
        #         client.delete_service(service.id)
        #         client.delete_model(service.model_id)
        #     except:
        #         pass

    raise ValueError(msg)

def get_test_config():
    result = {'test_subscription_id': os.getenv('TEST_SUBSCRIPTION_ID'),
              'test_resource_group' : os.getenv('TEST_RESOURCE_GROUP'),
              'test_model_management_account' : os.getenv('TEST_MODEL_MANAGEMENT_ACCOUNT')
              }

    return result

def get_service_principal():
    sp_id = os.getenv('TEST_SERVICE_PRINCIPAL_ID')
    sp_key = os.getenv('TEST_SERVICE_PRINCIPAL_KEY')
    tenant = os.getenv('TEST_TENANT')

    if (not sp_id):
        raise Exception("Service Principal Id not found")
    if (not sp_key):
        raise Exception("Service Principal Key not found")
    if (not tenant):
        raise Exception("Tenant not found")
    Aad_Record = namedtuple("AadRecord", ['tenant','service_principal_id', 'service_principal_key'])
    return Aad_Record(tenant, sp_id, sp_key)

def download_kaggle_test_data():
    datadir = os.path.expanduser('~/catsanddogs')
    cat_files = glob.glob(os.path.join(datadir, 'PetImages', 'Cat', '*.jpg'))
    dog_files = glob.glob(os.path.join(datadir, 'PetImages', 'Dog', '*.jpg'))

    if(not len(cat_files) or not len(dog_files)):
        os.makedirs(datadir)
        uri = os.getenv('TEST_KAGGLE_DATA_URI')
        r = requests.get(uri)
        zip_path = os.path.join(datadir, 'data.zip')
        with open(zip_path,'wb') as output:
            output.write(r.content)
        zip_ref = zipfile.ZipFile(zip_path, 'r')
        zip_ref.extractall(datadir)
        zip_ref.close()
        os.remove(zip_path)