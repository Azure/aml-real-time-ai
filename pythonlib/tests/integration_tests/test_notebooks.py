# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License
import pytest
import os
import nbformat
import json

from nbconvert.preprocessors import ExecutePreprocessor
from tests.integration_tests.test_utils import get_service_principal, get_test_config

def test_quickstart_notebook():
    os.chdir(os.path.join(os.getcwd(), 'notebooks/resnet50'))
    file = os.path.join(os.getcwd(), '00_QuickStart.ipynb')
    lines = None
    with open(file) as f:
        lines = f.read()
        f.close()
    
    lines = replace_auth_values(lines)
    nb = nbformat.reads(lines, as_version=4)
    ep = ExecutePreprocessor(timeout=1800, kernel_name='python3')
    out = ep.preprocess(nb, {'metadata': {'path': 'notebooks/'}})
    print(out)

def replace_auth_values(str):
    test_config = get_test_config()
    service_principal = get_service_principal()

    str = str.replace(
        'deployment_client = DeploymentClient(subscription_id, resource_group, model_management_account)', 
        'from collections import namedtuple\\nAad_Record = namedtuple(\\"AadRecord\\", [\\"tenant\\",\\"service_principal_id\\",\\"service_principal_key\\"])\\nservice_principal=Aad_Record(\\"{}\\", \\"{}\\", \\"{}\\")\\ndeployment_client = DeploymentClient(\\"{}\\", \\"{}\\", \\"{}\\", service_principal)'.format(service_principal.tenant, service_principal.service_principal_id, service_principal.service_principal_key, test_config['test_subscription_id'], test_config['test_resource_group'], test_config['test_model_management_account']))

    return str