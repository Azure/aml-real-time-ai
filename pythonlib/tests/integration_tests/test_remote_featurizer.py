# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License
import pytest
import tensorflow as tf
import numpy as np
import os
import uuid

from tests.integration_tests.test_utils import get_service_principal, get_test_config

from amlrealtimeai.deployment_client import store_refresh_token
from amlrealtimeai.resnet50.model import RemoteQuantizedResNet50
from amlrealtimeai.pipeline import ServiceDefinition, TensorflowStage, BrainWaveStage
from amlrealtimeai.resnet50.utils import preprocess_array
from amlrealtimeai.deployment_client import DeploymentClient
from amlrealtimeai.client import PredictionClient

def read_file():
    file_name = "/tmp/share1/shark.jpg"
    if os.path.isfile(file_name):
        file = open(file_name, "rb")
        data = file.read()
        file.close()
        return data
    return None
    
def test_remote_featurizer_local_usage():
    test_config = get_test_config()

    in_images = tf.placeholder(tf.string)
    image_tensors = preprocess_array(in_images)

    remote_service_name = ("int-test-featurizer-svc-" + str(uuid.uuid4()))[:30]
    featurizer = RemoteQuantizedResNet50(test_config['test_subscription_id'], test_config['test_resource_group'],
                                         test_config['test_model_management_account'], os.path.expanduser("~/models"),
                                         remote_service_name, use_service_principal = True,
                                         service_principal_params = get_service_principal())
    featurizer.import_graph_def(include_top=True, include_featurizer=True, input_tensor=image_tensors)

    try:
        with tf.Session() as sess:
           result = sess.run([featurizer.featurizer_output], feed_dict={in_images: [read_file()]})
           np_result = np.array(result[0])
           assert all([x == y for x, y in zip(np_result.shape, [1, 1, 1, 2048])])
           assert np_result.dtype == np.dtype('float32')

           result = sess.run([featurizer.featurizer_output], feed_dict={in_images: [read_file(), read_file()]})
           np_result = np.array(result[0])
           assert all([x == y for x, y in zip(np_result.shape, [2, 1, 1, 2048])])
           assert np_result.dtype == np.dtype('float32')

           result = sess.run([featurizer.classifier_output], feed_dict={in_images: [read_file()]})
           np_result = np.array(result[0])
           assert all([x == y for x, y in zip(np_result.shape, [1, 1000])])
           assert np_result.dtype == np.dtype('float32')

           result = sess.run([featurizer.classifier_output], feed_dict={in_images: [read_file(), read_file()]})
           np_result = np.array(result[0])
           assert all([x == y for x, y in zip(np_result.shape, [2, 1000])])
           assert np_result.dtype == np.dtype('float32')
    finally:
        featurizer.cleanup_remote_service()


def test_remote_featurizer_create_package_and_service():
    test_config = get_test_config()

    deployment_client = DeploymentClient(test_config['test_subscription_id'], test_config['test_resource_group'],
                                         test_config['test_model_management_account'],
                                         use_service_principal = True, service_principal_params = get_service_principal())

    id = uuid.uuid4().hex[:5]
    model_name = "int-test-rf-model-" + id
    service_name = "int-test-rf-service-" + id

    service_def_path = "/tmp/modelrf"

    in_images = tf.placeholder(tf.string)
    image_tensors = preprocess_array(in_images)

    remote_service_name = ("int-test-featurizer-svc-" + str(uuid.uuid4()))[:30]
    
    model = RemoteQuantizedResNet50(test_config['test_subscription_id'], test_config['test_resource_group'], test_config['test_model_management_account'], os.path.expanduser("~/models"), remote_service_name)
    model.import_graph_def(include_featurizer=True, input_tensor=image_tensors)

    service_def = ServiceDefinition()
    service_def.pipeline.append(TensorflowStage(tf.Session(), in_images, image_tensors))
    service_def.pipeline.append(BrainWaveStage(model))
    service_def.pipeline.append(TensorflowStage(tf.Session(), model.classifier_input, model.classifier_output))
    service_def.save(service_def_path)

    # create service
    model_id = deployment_client.register_model(model_name, service_def_path)
    service = deployment_client.create_service(service_name, model_id)

    prediction_client = PredictionClient(service.ipAddress, service.port)
    top_result = sorted(enumerate(prediction_client.score_image("/tmp/share1/shark.jpg")), key=lambda x: x[1], reverse=True)[:1]
    # 'tiger shark' is class 3
    assert top_result[0][0] == 3

    deployment_client.delete_service(service.id)
    deployment_client.delete_model(model_id)