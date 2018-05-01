# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
from . import AbstractStage
from .tensorflow.graph_util_impl import convert_variables_to_constants
import tensorflow as tf
import numpy as np
import os
import uuid

class TensorflowStage(AbstractStage):
    def __init__(self, session, input_tensor = None, output_tensor = None, name = None):
        super().__init__()

        self.type = "tensorflow"
        self.input_tensor = input_tensor
        self.output_tensor = output_tensor
        self.name = name
        self.input_tensor_name = self.input_tensor.name
        self.output_tensor_name = self.output_tensor.name
        self.file_name = self.name if self.name is not None else str(uuid.uuid4())
        self.session = session
        

    def json_dict(self):
        return {"type": self.type, "input_tensor": self.input_tensor_name, "output_tensor": self.output_tensor_name,
         "model_path": self.file_name, "name": self.name}


    def write_data(self, base_path:str):

        model_path = os.path.join(base_path, self.file_name)

        frozen_graph_def = convert_variables_to_constants(
            self.session,
            self.session.graph_def,
            [self.input_tensor.op.name],
            [self.output_tensor.op.name]
        )

        with tf.gfile.GFile(model_path, "wb") as f:
            f.write(frozen_graph_def.SerializeToString())