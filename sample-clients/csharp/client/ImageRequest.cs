// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.
using System.IO;
using System.Linq;
using Google.Protobuf;
using Tensorflow;
using Tensorflow.Serving;
using DataType = Tensorflow.DataType;

namespace CSharpClient
{
    public class ImageRequest : IScoringRequest
    {
        private readonly ModelSpec _modelSpec;
        private readonly Stream[] _images;

        public ImageRequest(params Stream[] images)
        {
            _modelSpec = new ModelSpec();
            _images = images;
        }

        public PredictRequest MakePredictRequest()
        {
            var request = new PredictRequest { ModelSpec = _modelSpec };
            var proto = new TensorProto { Dtype = DataType.DtString };

            var bytes = _images.Select(ByteString.FromStream);
            proto.StringVal.AddRange(bytes);
            proto.TensorShape = new TensorShapeProto();
            proto.TensorShape.Dim.Add(new TensorShapeProto.Types.Dim());
            proto.TensorShape.Dim[0].Size = _images.Length;

            request.Inputs["images"] = proto;
            return request;
        }
    }
}