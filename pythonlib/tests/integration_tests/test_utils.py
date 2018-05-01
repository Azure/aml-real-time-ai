# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License
import os
import json

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

def override_token_funcs():
    deployment_client.store_refresh_token = lambda t: __save_refresh_token(t)
    deployment_client.load_refresh_token = lambda: __load_refresh_token()

def __save_refresh_token(token):
    file_name = "/tmp/share1/refresh_token"
    file = open(file_name, "w")
    file.write(token)
    file.close()

def __load_refresh_token():
    file_name = "/tmp/share1/refresh_token"
    if os.path.isfile(file_name):
        file = open(file_name, "r")
        token = file.read()
        file.close()
        return token
    return None