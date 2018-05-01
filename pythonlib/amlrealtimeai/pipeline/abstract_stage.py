# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
from abc import ABC, abstractmethod
import json


class AbstractStage(ABC):

    @abstractmethod
    def write_data(self, base_path:str):
        raise NotImplementedError

    @property
    @abstractmethod
    def json_dict(self):
        raise NotImplementedError

    @classmethod
    def __subclasshook__(cls, C):
        return True


class StageEncoder(json.JSONEncoder):
    def default(self, obj): # pylint: disable=E0202
        if issubclass(obj, AbstractStage):
            return {k: v for k, v in obj.json_dict().items() if v is not None}
        return json.JSONEncoder.default(self, obj)
