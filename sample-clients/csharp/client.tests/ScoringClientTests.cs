using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Grpc.Core;
using Moq;
using Tensorflow;
using Tensorflow.Serving;
using Xunit;

namespace CSharpClient.Tests
{
    public class ScoringClientTests
    {
        [Fact]
        public async Task Invokes_predict_async_call()
        {
            var expectedResultValues = new[] { 1f, 2f, 3f };

            var outputTensorProto = new TensorProto { Dtype = DataType.DtFloat };
            outputTensorProto.FloatVal.Add(expectedResultValues);

            outputTensorProto.TensorShape = new TensorShapeProto();
            outputTensorProto.TensorShape.Dim.Add(new TensorShapeProto.Types.Dim());
            outputTensorProto.TensorShape.Dim[0].Size = 3;

            var predictRequest = new PredictRequest();
            var predictResponse = new PredictResponse();
            predictResponse.Outputs.Add("output_alias", outputTensorProto);

            var predictionServiceClientMock = new Mock<IPredictionServiceClient>();
            predictionServiceClientMock.Setup(x => x.PredictAsync(predictRequest)).ReturnsAsync(predictResponse).Verifiable();

            var scoringRequestMock = new Mock<IScoringRequest>();
            scoringRequestMock.Setup(x => x.MakePredictRequest()).Returns(() => predictRequest);

            var scoringClient = new ScoringClient(predictionServiceClientMock.Object);
            var result = await scoringClient.ScoreAsync(scoringRequestMock.Object);

            Assert.Equal(expectedResultValues, result);

            scoringRequestMock.Verify(x => x.MakePredictRequest(), Times.Exactly(1));
            predictionServiceClientMock.Verify(x => x.PredictAsync(predictRequest), Times.Exactly(1));
        }

        [Fact]
        public async Task Invokes_predict_async_call_float_input()
        {
            var expectedResultValues = new[] { 1f, 2f, 3f };

            var outputTensorProto = new TensorProto { Dtype = DataType.DtFloat };
            outputTensorProto.FloatVal.Add(expectedResultValues);

            outputTensorProto.TensorShape = new TensorShapeProto();
            outputTensorProto.TensorShape.Dim.Add(new TensorShapeProto.Types.Dim());
            outputTensorProto.TensorShape.Dim[0].Size = 3;

            var predictResponse = new PredictResponse();
            predictResponse.Outputs.Add("output_alias", outputTensorProto);

            var predictionServiceClientMock = new Mock<IPredictionServiceClient>();
            predictionServiceClientMock.Setup(x => x.PredictAsync(It.IsAny<PredictRequest>())).ReturnsAsync(predictResponse).Verifiable();

            var scoringRequestMock = new FloatRequest(new Dictionary<string, float[]>() { { "x:0", new[] { 1.0f } } });

            var scoringClient = new ScoringClient(predictionServiceClientMock.Object);
            var result = await scoringClient.ScoreAsync(scoringRequestMock);

            Assert.Equal(expectedResultValues, result);

            predictionServiceClientMock.Verify(x => x.PredictAsync(It.IsAny<PredictRequest>()), Times.Exactly(1));
        }

        [Theory]
        [InlineData(StatusCode.DeadlineExceeded)]
        [InlineData(StatusCode.Unavailable)]
        [InlineData(StatusCode.Aborted)]
        [InlineData(StatusCode.Internal)]
        public async Task Retries_transient_exceptions(StatusCode transientStatusCode)
        {
            var exception = new RpcException(new Status(transientStatusCode, string.Empty));

            var expectedResultValues = new[] { 1f, 2f, 3f };

            var outputTensorProto = new TensorProto { Dtype = DataType.DtFloat };
            outputTensorProto.FloatVal.Add(expectedResultValues);

            outputTensorProto.TensorShape = new TensorShapeProto();
            outputTensorProto.TensorShape.Dim.Add(new TensorShapeProto.Types.Dim());
            outputTensorProto.TensorShape.Dim[0].Size = 3;

            var predictRequest = new PredictRequest();
            var predictResponse = new PredictResponse();
            predictResponse.Outputs.Add("output_alias", outputTensorProto);

            var predictionServiceClientMock = new Mock<IPredictionServiceClient>();
            predictionServiceClientMock.Setup(x => x.PredictAsync(predictRequest)).Returns(async () =>
            {
                await Task.CompletedTask;

                if (exception != null)
                {
                    var x = exception;
                    exception = null;
                    throw x;
                }

                return predictResponse;
            }).Verifiable();

            var scoringRequestMock = new Mock<IScoringRequest>();
            scoringRequestMock.Setup(x => x.MakePredictRequest()).Returns(() => predictRequest);

            var scoringClient = new ScoringClient(predictionServiceClientMock.Object);
            var result = await scoringClient.ScoreAsync(scoringRequestMock.Object);

            Assert.Equal(expectedResultValues, result);

            scoringRequestMock.Verify(x => x.MakePredictRequest(), Times.Exactly(1));
            predictionServiceClientMock.Verify(x => x.PredictAsync(predictRequest), Times.Exactly(2));
        }

        [Theory]
        [InlineData(StatusCode.DeadlineExceeded, 3)]
        [InlineData(StatusCode.Unavailable, 1)]
        [InlineData(StatusCode.Aborted, 4)]
        [InlineData(StatusCode.Internal, 2)]
        public async Task Retries_transient_exceptions_until_retries_exhausted(StatusCode transientStatusCode, int retryCount)
        {
            var exception = new RpcException(new Status(transientStatusCode, string.Empty));

            var expectedResultValues = new[] { 1f, 2f, 3f };

            var outputTensorProto = new TensorProto { Dtype = DataType.DtFloat };
            outputTensorProto.FloatVal.Add(expectedResultValues);

            outputTensorProto.TensorShape = new TensorShapeProto();
            outputTensorProto.TensorShape.Dim.Add(new TensorShapeProto.Types.Dim());
            outputTensorProto.TensorShape.Dim[0].Size = 3;

            var predictRequest = new PredictRequest();
            var predictResponse = new PredictResponse();
            predictResponse.Outputs.Add("output_alias", outputTensorProto);

            var predictionServiceClientMock = new Mock<IPredictionServiceClient>();
            predictionServiceClientMock.Setup(x => x.PredictAsync(predictRequest)).ThrowsAsync(exception).Verifiable();

            var scoringRequestMock = new Mock<IScoringRequest>();
            scoringRequestMock.Setup(x => x.MakePredictRequest()).Returns(() => predictRequest);

            var scoringClient = new ScoringClient(predictionServiceClientMock.Object);
            var resultException = await Assert.ThrowsAsync<RpcException>(() => scoringClient.ScoreAsync(scoringRequestMock.Object, retryCount));

            Assert.Equal(exception, resultException);

            scoringRequestMock.Verify(x => x.MakePredictRequest(), Times.Exactly(1));
            predictionServiceClientMock.Verify(x => x.PredictAsync(predictRequest), Times.Exactly(retryCount));
        }

        public static IEnumerable<object[]> NonTransientExceptions =>
            new[]
            {
                new [] { (Exception)new RpcException(new Status(StatusCode.Unauthenticated, string.Empty)) },
                new [] { (Exception)new InvalidOperationException("some error")  }
            };

        [Theory]
        [MemberData(nameof(NonTransientExceptions))]
        public async Task Rethrows_non_transient_exception(Exception exception)
        {
            var expectedResultValues = new[] { 1f, 2f, 3f };

            var outputTensorProto = new TensorProto { Dtype = DataType.DtFloat };
            outputTensorProto.FloatVal.Add(expectedResultValues);

            outputTensorProto.TensorShape = new TensorShapeProto();
            outputTensorProto.TensorShape.Dim.Add(new TensorShapeProto.Types.Dim());
            outputTensorProto.TensorShape.Dim[0].Size = 3;

            var predictRequest = new PredictRequest();
            var predictResponse = new PredictResponse();
            predictResponse.Outputs.Add("output_alias", outputTensorProto);

            var predictionServiceClientMock = new Mock<IPredictionServiceClient>();
            predictionServiceClientMock.Setup(x => x.PredictAsync(predictRequest)).Returns(async () =>
            {
                await Task.CompletedTask;
                throw exception;
            }).Verifiable();

            var scoringRequestMock = new Mock<IScoringRequest>();
            scoringRequestMock.Setup(x => x.MakePredictRequest()).Returns(() => predictRequest);

            var scoringClient = new ScoringClient(predictionServiceClientMock.Object);
            var actualException = await Assert.ThrowsAnyAsync<Exception>(async () => await scoringClient.ScoreAsync(scoringRequestMock.Object));

            Assert.Same(exception, actualException);

            scoringRequestMock.Verify(x => x.MakePredictRequest(), Times.Exactly(1));
            predictionServiceClientMock.Verify(x => x.PredictAsync(predictRequest), Times.Exactly(1));
        }
    }
}