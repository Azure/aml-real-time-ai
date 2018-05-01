# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
import tensorflow as tf

def preprocess_array(in_images):
    return tf.map_fn(_decode, in_images, tf.float32, name="map_normalize_jpeg")

def _preprocess_tensor(tensor):
    jpeg_decoded = tf.image.decode_png(tensor,3)
    float_caster = tf.cast(jpeg_decoded, dtype=tf.float32)
    dims_expander = tf.expand_dims(float_caster, 0)
    resizer = tf.image.resize_images(dims_expander, [224, 224], method=tf.image.ResizeMethod.NEAREST_NEIGHBOR)

    slice_red = tf.slice(resizer, [0, 0, 0, 0], [1, 224, 224, 1])
    slice_green = tf.slice(resizer, [0, 0, 0, 1], [1, 224, 224, 1])
    slice_blue = tf.slice(resizer, [0, 0, 0, 2], [1, 224, 224, 1])

    sub_red = tf.subtract(slice_red, 123.68)
    sub_green = tf.subtract(slice_green, 116.779)
    sub_blue = tf.subtract(slice_blue, 103.939)

    return tf.concat([sub_blue, sub_green, sub_red], 3)

def _decode(tensor):
    return tf.squeeze(_preprocess_tensor(tensor))
