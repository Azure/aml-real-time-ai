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
    using System;
    using System.Collections.Generic;
    using System.Runtime.CompilerServices;

    using Google.Protobuf.Collections;

    public class FloatRequest : IScoringRequest
    {
        private readonly PredictRequest _proto;

        public FloatRequest(IDictionary<string, float[]> floats)
            : this(
                floats.ToDictionary(
                    kvp => kvp.Key,
                    kvp => new Tuple<float[], int[]>(kvp.Value, new[] { kvp.Value.Length })))
        {
        }

        public FloatRequest(IDictionary<string, Tuple<float[], int[]>> inputs)
        {
            _proto = new PredictRequest { ModelSpec = new ModelSpec() };
            foreach (var (key, value) in inputs)
            {
                _proto.Inputs[key] = makeProto(value);
            }
        }

        private static TensorProto makeProto(Tuple<float[], int[]> input)
        {
            var proto = new TensorProto { Dtype = DataType.DtFloat };
            proto.FloatVal.AddRange(input.Item1);
            var dims = input.Item2.Select(dim => new TensorShapeProto.Types.Dim { Size = dim });
            proto.TensorShape = new TensorShapeProto();
            proto.TensorShape.Dim.AddRange(dims);
            return proto;
        }

        public PredictRequest MakePredictRequest()
        {
            return this._proto;
        }
    }
}