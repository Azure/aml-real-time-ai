# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
import tempfile
import os
import json
import shutil
from . import AbstractStage, StageEncoder

# TODO download this value from some public blob
aml_runtime_version = "1.1"

class ServiceDefinition(object):
    def __init__(self):
        self.pipeline = [] # type: List[AbstractStage]
        

    def json_dict(self):
        return {"aml_runtime_version": aml_runtime_version, "pipeline": self.pipeline}


    def save(self, service_def_path:str):
        with tempfile.TemporaryDirectory() as tmpdir:
            for stage in self.pipeline:
                stage.write_data(tmpdir)
            with open(os.path.join(tmpdir,'service_def.json'),'w') as f:
                json.dump(self,f,cls=StageEncoder,sort_keys=True)
            shutil.make_archive(service_def_path, format='zip', root_dir=tmpdir)
            shutil.move(service_def_path+".zip",service_def_path)
