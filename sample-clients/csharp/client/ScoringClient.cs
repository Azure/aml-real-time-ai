﻿// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.

using System;
using System.Threading.Tasks;
using Grpc.Core;
using Tensorflow.Serving;

namespace CSharpClient
{
    public class ScoringClient
    {
        private const int RetryCount = 10;

        private readonly IPredictionServiceClient _client;

        public ScoringClient(IPredictionServiceClient client)
        {
            _client = client;
        }

        public ScoringClient(Channel channel) : this(new PredictionServiceClientWrapper(new PredictionService.PredictionServiceClient(channel)))
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
            _client = new PredictionServiceClientWrapper(new PredictionService.PredictionServiceClient(channel));
        }

        public async Task<float[]> ScoreAsync(IScoringRequest request, int retryCount = RetryCount)
        {
            return await ScoreAsync<float[]>(request, retryCount);
        }

        public async Task<T> ScoreAsync<T>(IScoringRequest request, int retryCount = RetryCount) where T : class
        {
            var predictRequest = request.MakePredictRequest();

            return await RetryAsync(async () =>
            {
                var result = await _client.PredictAsync(predictRequest);
                return result.Outputs["output_alias"].Convert<T>();
            }, retryCount);
        }

        private async Task<T> RetryAsync<T>(
            Func<Task<T>> operation, int retryCount = RetryCount
            )
        {
            while (true)
            {
                try
                {
                    return await operation();
                }
                catch (RpcException rpcException)
                {
                    if (!IsTransient(rpcException) || --retryCount <= 0)
                    {
                        throw;
                    }
                }
            }
        }

        private static bool IsTransient(RpcException rpcException)
        {
            return
                rpcException.Status.StatusCode == StatusCode.DeadlineExceeded ||
                rpcException.Status.StatusCode == StatusCode.Unavailable ||
                rpcException.Status.StatusCode == StatusCode.Aborted ||
                rpcException.Status.StatusCode == StatusCode.Internal;
        }
    }
}