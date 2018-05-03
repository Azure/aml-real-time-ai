# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License
import os
import json
from collections import namedtuple

from datetime import datetime, timezone
from dateutil.parser import parse

from amlrealtimeai import deployment_client

def cleanup_old_test_services(client):
    for service in client.list_services():
        if(not service.name.startswith('int-test-')):
            continue
        service = client.get_service_by_id(service.id)
        offset = datetime.now(timezone.utc) - parse(service.createdAt)
        if(offset.seconds > 3600):
            try:
                client.delete_service(service.id)
                client.delete_model(service.model_id)
            except:
                pass

def get_test_config():
    return json.load(open("/tmp/share1/test_config"))

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