# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License
import pytest
import tensorflow as tf
import numpy as np
import os

from amlrealtimeai.resnet50.model import LocalQuantizedResNet50
from amlrealtimeai.resnet50.utils import preprocess_array

def read_file():
    file_name = "/tmp/share1/shark.jpg"
    if os.path.isfile(file_name):
        file = open(file_name, "rb")
        data = file.read()
        file.close()
        return data
    return None
    

# def test_local_featurizer():
#     override_token_funcs()

#     in_images = tf.placeholder(tf.string)
#     image_tensors = preprocess_array(in_images)

#     featurizer = LocalQuantizedResNet50("~/models")
#     featurizer.import_graph_def(include_top=True, include_featurizer=True, input_tensor=image_tensors)

#     with tf.Session() as sess:
#         # result = sess.run([featurizer.classifier_output], feed_dict={in_images: [read_file()]})
#         # assert all([x == y for x, y in zip(np.array(result[0]).shape, [1, 1000])])

#         # result = sess.run([featurizer.featurizer_output], feed_dict={in_images: [read_file()]})
#         # assert all([x == y for x, y in zip(np.array(result[0]).shape, [1, 1, 2048])])

#         # result = sess.run([featurizer.classifier_output], feed_dict={in_images: [read_file(), read_file()]})
#         # assert all([x == y for x, y in zip(np.array(result[0]).shape, [2, 1000])])

#         result = sess.run([featurizer.featurizer_output], feed_dict={in_images: [read_file(), read_file()]})
#         assert all([x == y for x, y in zip(np.array(result[0]).shape, [2, 1, 2048])])