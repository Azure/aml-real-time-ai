# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
import keras
import tensorflow as tf
import uuid
import os.path
import json

from . import AbstractStage
from . import TensorflowStage


class KerasStage(TensorflowStage):

    def __init__(self, model: keras.models.Sequential, name = None):
        super().__init__(keras.backend.get_session(), model.inputs[0], model.outputs[0], name)