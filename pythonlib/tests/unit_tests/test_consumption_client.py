# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License
import pytest
import os
import tempfile
import grpc
import tensorflow as tf
import numpy as np
from unittest import mock
from datetime import datetime, timedelta

try:
    from tensorflow.core.framework import tensor_shape_pb2
    from tensorflow.core.framework import types_pb2
except ImportError:
    from .tensorflow.core.framework import tensor_shape_pb2
    from .tensorflow.core.framework import types_pb2

from amlrealtimeai.client import PredictionClient

def test_create_client():
    client = PredictionClient("localhost", 50051)
    assert client is not None

def test_create_client_with_auth():
    client = PredictionClient("localhost", 50051, True, "key1")
    assert client is not None

def test_create_client_raises_if_host_is_none():
    with pytest.raises(ValueError):
        PredictionClient(None, 50051)

def test_create_client_raises_if_port_is_none():
    with pytest.raises(ValueError):
        PredictionClient("localhost", None)

    
def test_score_image():

    def predict_mock(request, timeout):
        inputs = request.inputs['images'].string_val
        assert inputs[0].decode('utf-8') == "abc"
        return_data = np.asarray([[ 1, 2, 3 ]])
        return_tensor = tf.contrib.util.make_tensor_proto(return_data, types_pb2.DT_FLOAT, return_data.shape)
        result = mock.MagicMock()
        result.outputs = { "output_alias": return_tensor }
        return result

    stub_mock = mock.Mock()
    stub_mock.Predict = mock.MagicMock(side_effect=predict_mock)

    image_file_path = os.path.join(tempfile.mkdtemp(), "img.png")
    image_file = open(image_file_path, "w")
    image_file.write("abc")
    image_file.close()

    client = PredictionClient("localhost", 50051)
    client._get_grpc_stub = lambda: stub_mock

    result = client.score_image(image_file_path)
    assert all([x == y for x, y in zip(result, [1, 2, 3])])


def test_score_numpy_array():

    def predict_mock(request, timeout):
        inputs = tf.contrib.util.make_ndarray(request.inputs['images'])
        assert all([x == y for x, y in zip(inputs[0], [ 1, 2, 3 ])])
        assert all([x == y for x, y in zip(inputs[1], [ 4, 5, 6 ])])

        return_data = np.asarray([[ 11, 22, 33 ], [ 44, 55, 66 ]])
        return_tensor = tf.contrib.util.make_tensor_proto(return_data, types_pb2.DT_FLOAT, return_data.shape)
        result = mock.MagicMock()
        result.outputs = { "output_alias": return_tensor }
        return result

    stub_mock = mock.Mock()
    stub_mock.Predict = mock.MagicMock(side_effect=predict_mock)

    client = PredictionClient("localhost", 50051)
    client._get_grpc_stub = lambda: stub_mock

    result = client.score_numpy_array(np.asarray([[1, 2, 3], [4, 5, 6]], dtype='f'))
    assert all([x == y for x, y in zip(result[0], [ 11, 22, 33 ])])
    assert all([x == y for x, y in zip(result[1], [ 44, 55, 66 ])])


def test_retrying_rpc_exception():

    first_call = [ True ]

    channel_mock_loaded = { 'value': 0 }
    channel_mock_closed = { 'value': 0 }

    def unary_unary(id, request_serializer, response_deserializer):
        result = mock.MagicMock()
        if id == '/tensorflow.serving.PredictionService/Predict':
            if(first_call[0]):
                first_call[0] = False
                return lambda req, timeout: (_ for _ in ()).throw(grpc.RpcError())

            return_data = np.asarray([[ 11, 22 ]])
            return_tensor = tf.contrib.util.make_tensor_proto(return_data, types_pb2.DT_FLOAT, return_data.shape)
            result.outputs = { "output_alias": return_tensor }
        return lambda req, timeout: result

    def load_channel_mock():
        channel_mock_loaded['value'] += 1
        return channel_mock

    def close_channel_mock():
        channel_mock_closed['value'] += 1

    now = datetime.now()

    channel_mock = mock.Mock()
    channel_mock.unary_unary = mock.MagicMock(side_effect=unary_unary)
    channel_mock.close = close_channel_mock
    
    client = PredictionClient("localhost", 50051, channel_shutdown_timeout=timedelta(minutes=1))
    client._channel_func = load_channel_mock    
    client._get_datetime_now = lambda: now

    result = client.score_numpy_array(np.asarray([[1, 2]], dtype='f'))
    assert all([x == y for x, y in zip(result[0], [ 11, 22 ])])

    assert channel_mock_loaded['value'] == 2
    assert channel_mock_closed['value'] == 1

def test_create_new_channel_after_timeout_expires():

    channel_mock_loaded = { 'value': 0 }

    def unary_unary(id, request_serializer, response_deserializer):
        result = mock.MagicMock()
        if id == '/tensorflow.serving.PredictionService/Predict':
            return_data = np.asarray([[ 1, 2, 3 ]])
            return_tensor = tf.contrib.util.make_tensor_proto(return_data, types_pb2.DT_FLOAT, return_data.shape)
            result.outputs = { "output_alias": return_tensor }
        return lambda req, timeout: result

    def load_channel_mock():
        channel_mock_loaded['value'] += 1
        return channel_mock

    now = datetime.now()

    channel_mock = mock.Mock()
    channel_mock.unary_unary = mock.MagicMock(side_effect=unary_unary)

    image_file_path = os.path.join(tempfile.mkdtemp(), "img.png")
    image_file = open(image_file_path, "w")
    image_file.write("abc")
    image_file.close()

    client = PredictionClient("localhost", 50051, channel_shutdown_timeout=timedelta(minutes=1))
    client._channel_func = load_channel_mock    
    client._get_datetime_now = lambda: now

    result = client.score_image(image_file_path)
    assert all([x == y for x, y in zip(result, [1, 2, 3])])
    assert channel_mock_loaded['value'] == 1

    now = now + timedelta(seconds=50)
    result = client.score_image(image_file_path)
    assert all([x == y for x, y in zip(result, [1, 2, 3])])
    assert channel_mock_loaded['value'] == 1

    now = now + timedelta(seconds=20)
    result = client.score_image(image_file_path)
    assert all([x == y for x, y in zip(result, [1, 2, 3])])
    assert channel_mock_loaded['value'] == 1

    now = now + timedelta(seconds=70)
    result = client.score_image(image_file_path)
    assert all([x == y for x, y in zip(result, [1, 2, 3])])
    assert channel_mock_loaded['value'] == 2