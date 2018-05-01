// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.
using System.Threading.Tasks;
using Grpc.Core;
using Tensorflow.Serving;

namespace CSharpClient
{
    public class ScoringClient
    {
        private readonly PredictionService.PredictionServiceClient _client;

        public ScoringClient(PredictionService.PredictionServiceClient client)
        {
            _client = client;
        }

        public ScoringClient(Channel channel) : this(new PredictionService.PredictionServiceClient(channel))
        {
        }

        public ScoringClient(string host, int port, bool useSsl = false, string authKey = null)
        {
            ChannelCredentials baseCreds, creds;
            baseCreds = useSsl ? new SslCredentials() : ChannelCredentials.Insecure;
            if (authKey != null && useSsl)
            {
                creds = ChannelCredentials.Create(baseCreds, CallCredentials.FromInterceptor(
                      async (context, metadata) =>
                      {
                          metadata.Add(new Metadata.Entry("authorization", authKey));
                          await Task.CompletedTask;
                      }));
            }
            else
            {
                creds = baseCreds;
            }
            var channel = new Channel(host, port, creds);
            _client = new PredictionService.PredictionServiceClient(channel);
        }

        public async Task<float[]> ScoreAsync(IScoringRequest request)
        {
            return await ScoreAsync<float[]>(request);
        }

        public async Task<T> ScoreAsync<T>(IScoringRequest request) where T : class
        {
            var result = await _client.PredictAsync(request.MakePredictRequest());
            return result.Outputs["output_alias"].Convert<T>();
        }

        public float[] Score(IScoringRequest request)
        {
            return Score<float[]>(request);
        }

        public T Score<T>(IScoringRequest request) where T : class
        {
            var requestGrpc = request.MakePredictRequest();
            var result = _client.Predict(requestGrpc);
            return result.Outputs["output_alias"].Convert<T>();
        }
    }
}