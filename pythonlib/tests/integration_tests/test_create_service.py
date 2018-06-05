# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License
import pytest
import os
import uuid
import tensorflow as tf
import numpy as np
import time

from tests.integration_tests.test_utils import get_service_principal, get_test_config, cleanup_old_test_services

from amlrealtimeai.resnet50.model import LocalQuantizedResNet50
from amlrealtimeai.resnet50.utils import preprocess_array
from amlrealtimeai.pipeline import ServiceDefinition, TensorflowStage, BrainWaveStage
from amlrealtimeai.deployment_client import DeploymentClient
from amlrealtimeai.client import PredictionClient

def test_create_update_and_delete_service():
    test_config = get_test_config()

    deployment_client = DeploymentClient(test_config['test_subscription_id'], test_config['test_resource_group'], test_config['test_model_management_account'], get_service_principal())
    cleanup_old_test_services(deployment_client)