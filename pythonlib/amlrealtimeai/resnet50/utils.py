# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
import tensorflow as tf

def preprocess_array(in_images):
    return tf.map_fn(_decode, in_images, tf.float32, name="map_normalize_jpeg")

def _decode(tensor):
    return tf.squeeze(_preprocess_tensor(tensor))

    
def _preprocess_tensor(tensor):
    jpeg_decoded = tf.image.decode_png(tensor, 3)
    float_caster = tf.cast(jpeg_decoded, dtype=tf.float32)
    dims_expander = tf.expand_dims(float_caster, 0)
    # resizer = tf.image.resize_images(dims_expander, [224, 224], method=tf.image.ResizeMethod.NEAREST_NEIGHBOR)

    output_width = 224
    output_height = 224

    resize_side = tf.random_uniform([], minval=256, maxval=513, dtype=tf.int32)

    image = _aspect_preserving_resize(dims_expander, resize_side)
    image = _central_crop(image, output_height, output_width)
    image.set_shape([output_height, output_width, 3])
    image = tf.to_float(image)

    slice_red = tf.slice(image, [0, 0, 0, 0], [1, 224, 224, 1])
    slice_green = tf.slice(image, [0, 0, 0, 1], [1, 224, 224, 1])
    slice_blue = tf.slice(image, [0, 0, 0, 2], [1, 224, 224, 1])

    sub_red = tf.subtract(slice_red, 123.68)
    sub_green = tf.subtract(slice_green, 116.779)
    sub_blue = tf.subtract(slice_blue, 103.939)

    return tf.concat([sub_blue, sub_green, sub_red], 3)

def _aspect_preserving_resize(image, smallest_side):
    """Resize images preserving the original aspect ratio.

    Args:
    image: A 3-D image `Tensor`.
    smallest_side: A python integer or scalar `Tensor` indicating the size of
      the smallest side after resize.

    Returns:
    resized_image: A 3-D tensor containing the resized image.
    """
    smallest_side = tf.convert_to_tensor(smallest_side, dtype=tf.int32)

    shape = tf.shape(image)
    height = shape[0]
    width = shape[1]
    new_height, new_width = _smallest_size_at_least(height, width, smallest_side)
    image = tf.expand_dims(image, 0)
    resized_image = tf.image.resize_bilinear(image, [new_height, new_width],
                                           align_corners=False)
    resized_image = tf.squeeze(resized_image)
    resized_image.set_shape([None, None, 3])

    return resized_image

def _central_crop(image, crop_height, crop_width):
    """Performs central crops of the given image list.

    Args:
    image_list: a list of image tensors of the same dimension but possibly
      varying channel.
    crop_height: the height of the image following the crop.
    crop_width: the width of the image following the crop.

    Returns:
    the list of cropped images.
    """
    image_height = tf.shape(image)[0]
    image_width = tf.shape(image)[1]

    offset_height = (image_height - crop_height) / 2
    offset_width = (image_width - crop_width) / 2

    return _crop(image, offset_height, offset_width, crop_height, crop_width)
  
def _crop(image, offset_height, offset_width, crop_height, crop_width):
    """Crops the given image using the provided offsets and sizes.

    Note that the method doesn't assume we know the input image size but it does
    assume we know the input image rank.

    Args:
    image: an image of shape [height, width, channels].
    offset_height: a scalar tensor indicating the height offset.
    offset_width: a scalar tensor indicating the width offset.
    crop_height: the height of the cropped image.
    crop_width: the width of the cropped image.

    Returns:
    the cropped (and resized) image.

    Raises:
    InvalidArgumentError: if the rank is not 3 or if the image dimensions are
      less than the crop size.
    """
    original_shape = tf.shape(image)

    rank_assertion = tf.Assert(
      tf.equal(tf.rank(image), 3),
      ['Rank of image must be equal to 3.'])
    with tf.control_dependencies([rank_assertion]):
        cropped_shape = tf.stack([crop_height, crop_width, original_shape[2]])

    size_assertion = tf.Assert(
      tf.logical_and(
          tf.greater_equal(original_shape[0], crop_height),
          tf.greater_equal(original_shape[1], crop_width)),
      ['Crop size greater than the image size.'])

    offsets = tf.to_int32(tf.stack([offset_height, offset_width, 0]))

    # Use tf.slice instead of crop_to_bounding box as it accepts tensors to
    # define the crop size.
    with tf.control_dependencies([size_assertion]):
        image = tf.slice(image, offsets, cropped_shape)

    return tf.reshape(image, cropped_shape)