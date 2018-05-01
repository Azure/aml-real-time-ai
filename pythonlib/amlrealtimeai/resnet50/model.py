# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
import os
import requests
import zipfile
import hashlib
import tempfile
import tensorflow as tf
import uuid

from abc import ABC, abstractmethod

from amlrealtimeai.pipeline import BrainWaveStage
from amlrealtimeai.pipeline.service_definition import ServiceDefinition
from amlrealtimeai.deployment_client import DeploymentClient
from amlrealtimeai.client import PredictionClient

class QuantizedResNet50:
    version = '1.1.6-rc'
    model_name = 'resnet50'

    def __init__(self, model_base_path):
        self._featurizer_saver = None
        self.featurizer_input = None
        self.featurizer_output = None
        self._classifier_saver = None
        self.classifier_input = None
        self.classifier_output = None
        self.download(model_base_path)
        self._graph_prefix = 'rn_' + str(uuid.uuid4())[:5]

    def download(self, model_base_path):
        model_dir = os.path.join(model_base_path, self.model_name, self.version)
        self._featurizer_ckpt = os.path.join(model_dir, 'resnet50.pb')
        self._classifier_ckpt = os.path.join(model_dir, 'resnet50_classifier.pb')
        if not os.path.exists(self._featurizer_ckpt) or not os.path.exists(self._classifier_ckpt):
            if not os.path.exists(model_dir):
                os.makedirs(model_dir)
            r = requests.get("https://go.microsoft.com/fwlink/?linkid=873019")
            model_zip_path = os.path.join(model_base_path, 'model.zip')
            with open(model_zip_path,'wb') as output:
                output.write(r.content)
            zip_ref = zipfile.ZipFile(model_zip_path, 'r')
            zip_ref.extractall(model_dir)
            zip_ref.close()
            os.remove(model_zip_path)

    @abstractmethod
    def _import_featurizer_graph_def(self, input_map):
        raise NotImplementedError

    def _import_top_graph_def(self, include_featurizer, input_map):
        if include_featurizer:
            input_map = {'Input': self.featurizer_output}

        input_tensor_name = "Input:0"

        if not input_map is None:
            in_tensor = input_map['Input']
            wrap_in_tensor = tf.identity(in_tensor, name=self._graph_prefix + '/classifier_input')
            input_map = {'Input': wrap_in_tensor}
            input_tensor_name = 'classifier_input:0'      

        input_graph_def = tf.GraphDef()
        with tf.gfile.Open(self._classifier_ckpt, "rb") as f:
            data = f.read()
            input_graph_def.ParseFromString(data)
        tf.import_graph_def(input_graph_def, name=self._graph_prefix, input_map=input_map)
        return tf.get_default_graph().get_tensor_by_name(self._graph_prefix + '/' + input_tensor_name), tf.get_default_graph().get_tensor_by_name(self._graph_prefix + "/resnet_v1_50/logits/Softmax:0")


    def import_graph_def(self, include_featurizer=True, include_top=True, input_tensor=None):
        input_map = None
        if input_tensor is not None:
            input_map = {'InputImage': input_tensor}
        
        if include_featurizer:
            self.featurizer_input, self.featurizer_output = self._import_featurizer_graph_def(input_map)

        if include_top:
            self.classifier_input, self.classifier_output = self._import_top_graph_def(include_featurizer, input_map)    
            
    def model_ref(self):
        return self.model_name

    def model_version(self):
        return self.version

    def output_dims(self):
        return [1, 1, 2048]

class RemoteQuantizedResNet50(QuantizedResNet50):
    def __init__(self, subscription_id, resource_group, model_management_account, model_base_path, remote_service_name = None):
        super().__init__(model_base_path)
        self.__deployment_client = DeploymentClient(subscription_id, resource_group, model_management_account)
        self.__service_name = remote_service_name if remote_service_name is not None else "featurizer-service-" + hashlib.md5((self.model_name + "-" + self.version).encode("utf-8")).hexdigest()[:6]

    
    def _import_featurizer_graph_def(self, input_map):
        service = self.__deployment_client.get_service_by_name(self.__service_name)
        if(service is None):
            model_name = self.model_name + "-" + self.version + "-model"
            temp_dir = tempfile.mkdtemp()
            model_path = os.path.join(temp_dir, "model")
            service_def = ServiceDefinition()
            service_def.pipeline.append(BrainWaveStage(self))
            service_def.save(model_path)
            model_id = self.__deployment_client.register_model(model_name, model_path)
            service = self.__deployment_client.create_service(self.__service_name, model_id)

        self.__client = PredictionClient(service.ipAddress, service.port) #pylint: disable=E1101
        return input_map['InputImage'], tf.py_func(self._remote_service_call, [input_map['InputImage']], tf.float32)


    def _remote_service_call(self, data):
        return self.__client.score_numpy_array(data)

    def cleanup_remote_service(self):
        service = self.__deployment_client.get_service_by_name(self.__service_name)
        if service is not None:
            print("Deleting service", service.id)
            self.__deployment_client.delete_service(service.id)
            print("Deleted service", service.id)
            print("Deleting model", service.modelId)
            self.__deployment_client.delete_model(service.modelId)
            print("Deleted model", service.modelId)


class LocalQuantizedResNet50(QuantizedResNet50):
    def __init__(self, model_base_path):
        super().__init__(model_base_path)

    def _import_featurizer_graph_def(self, input_map):
        input_graph_def = tf.GraphDef()
        with tf.gfile.Open(self._featurizer_ckpt, "rb") as f:
            data = f.read()
            input_graph_def.ParseFromString(data)

        tf.import_graph_def(input_graph_def, name='', input_map=input_map)
        return tf.get_default_graph().get_tensor_by_name('InputImage:0'), tf.get_default_graph().get_tensor_by_name('resnet_v1_50/pool5:0')


if __name__== "__main__":
    model = LocalQuantizedResNet50('~/models')
    print(model.version)
