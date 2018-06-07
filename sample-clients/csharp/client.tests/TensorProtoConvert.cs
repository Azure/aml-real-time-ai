using System.Linq;
using Tensorflow;
using Xunit;

namespace CSharpClient.Tests
{
    public class TensorProtoConvert
    {
        [Fact]
        public void Converts_tensor_proto_to_float_array()
        {
            var tensorProto = new TensorProto { Dtype = DataType.DtFloat };
            tensorProto.FloatVal.Add(Enumerable.Range(1, 300).Select(x => (float)x));

            tensorProto.TensorShape = new TensorShapeProto();
            tensorProto.TensorShape.Dim.Add(new TensorShapeProto.Types.Dim());
            tensorProto.TensorShape.Dim.Add(new TensorShapeProto.Types.Dim());
            tensorProto.TensorShape.Dim.Add(new TensorShapeProto.Types.Dim());

            tensorProto.TensorShape.Dim[0].Size = 10;
            tensorProto.TensorShape.Dim[1].Size = 10;
            tensorProto.TensorShape.Dim[2].Size = 3;

            var floats = tensorProto.Convert<float[,,]>();
            var value = 1;

            for (var i1 = 0; i1 < floats.GetLength(0); i1++)
            {
                for (var i2 = 0; i2 < floats.GetLength(1); i2++)
                {
                    for (var i3 = 0; i3 < floats.GetLength(2); i3++)
                    {
                        Assert.Equal(value++, floats[i1, i2, i3]);
                    }
                }
            }
        }
    }
}