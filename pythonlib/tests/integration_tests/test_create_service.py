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
    if True:
        return

    test_config = get_test_config()

    deployment_client = DeploymentClient(test_config['test_subscription_id'], test_config['test_resource_group'], test_config['test_model_management_account'], get_service_principal())
    cleanup_old_test_services(deployment_client)

    id = uuid.uuid4().hex[:5]
    model_name = "int-test-model-" + id
    service_name = "int-test-service-" + id

    service_def_path = "/tmp/model"

    in_images = tf.placeholder(tf.string)
    image_tensors = preprocess_array(in_images)

    model = LocalQuantizedResNet50(os.path.expanduser("~/models"))
    model.import_graph_def(include_featurizer=False)

    service_def = ServiceDefinition()
    service_def.pipeline.append(TensorflowStage(tf.Session(), in_images, image_tensors))
    service_def.pipeline.append(BrainWaveStage(model))
    service_def.pipeline.append(TensorflowStage(tf.Session(), model.classifier_input, model.classifier_output))
    service_def.save(service_def_path)

    # create service
    first_model_id = deployment_client.register_model(model_name, service_def_path)
    service = deployment_client.create_service(service_name, first_model_id)

    service_list = deployment_client.list_services()
    assert any(x.name == service_name for x in service_list)

    prediction_client = PredictionClient(service.ipAddress, service.port)
    top_result = sorted(enumerate(prediction_client.score_image("/tmp/share1/shark.jpg")), key=lambda x: x[1], reverse=True)[:1]
    # 'tiger shark' is class 3
    assert top_result[0][0] == 3

    # update service, remove classifier
    service_def = ServiceDefinition()
    service_def.pipeline.append(TensorflowStage(tf.Session(), in_images, image_tensors))
    service_def.pipeline.append(BrainWaveStage(model))
    service_def.save(service_def_path)

    second_model_id = deployment_client.register_model(model_name, service_def_path)
    deployment_client.update_service(service.id, second_model_id)

    result = prediction_client.score_image("/tmp/share1/shark.jpg")
    assert all([x == y for x, y in zip(np.array(result).shape, [1, 1, 2048])])

    # wait for timeout of Azure LB
    time.sleep(4 * 60 + 10)

    result = prediction_client.score_image("/tmp/share1/shark.jpg")
    assert all([x == y for x, y in zip(np.array(result).shape, [1, 1, 2048])])

    deployment_client.delete_service(service.id)
    deployment_client.delete_model(first_model_id)
    deployment_client.delete_model(second_model_id)