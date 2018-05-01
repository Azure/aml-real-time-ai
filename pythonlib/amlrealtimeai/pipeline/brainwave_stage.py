# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
from . import AbstractStage

import numpy as np
import os
import uuid

class BrainWaveStage(AbstractStage):
    def __init__(self, model, name = None):
        super().__init__()

        self.type = "brainwave"
        self.model_ref = model.model_ref()
        self.model_version = model.model_version()
        self.output_dims = model.output_dims()
        self.name = name        
        

    def json_dict(self):
        return {"type": self.type, "model_ref": self.model_ref, "model_version": self.model_version,
         "output_tensor_dims": self.output_dims, "name": self.name}


    def write_data(self, base_path:str):
        # nothing to do
        pass