# SSL/TLS and Authentication

Machine Learning models are assets, created by experienced professionals using valuable data and compute time. 
It is important to secure customer data and company assets.
Azure Machine Learning enables you to do this by providing SSL support and key authentication.
This document provides an overview of:
 * enabling SSL/TLS and Authentication in the Azure Machine Learning hardware accelerated inference service
 * consuming the services with authentication from Python and C# using the demo clients
 * adding authentication to other generated gRPC clients
 * consuming the services with self signed certificates for dev/test purposes   

> [!Note]
> The contents of this document are only applicable to Azure Machine Learning Real-Time AI (FPGA) models. For standard Azure Machine Learning services, refer to the document [here](https://docs.microsoft.com/en-us/azure/machine-learning/preview/how-to-setup-ssl-on-mlc).
## Enabling SSL/TLS and Authentication

> [!IMPORTANT] 
> Authentication is only enabled for services that have enabled SSL by providing a certificate and key.
> If you do not enable SSL, any user on the internet will be able make calls on the service.
> If you enable SSL, an authentication key will be required to consume the service.

SSL ensures that a client is connected to the server it expects, as well as ensures that communication between the server and client is secure.

You can either deploy a service with SSL enabled, or update an already deployed service to enable it. 
Either way you will follow the same basic steps:

1. Acquire an SSL certificate
2. Deploy or update the service with SSL enabled
3. Update your DNS to point to the service

### 1. Acquire an SSL certificate
Acquire an SSL certificate for the web address you expect the service to be located at. The certificate's common name must be a Fully Qualified Domain Name, not an IP address.  

[//]: # (TODO: coverste - determine if we support wildcard certs, if not remove the below.)
> [!NOTE]
> You can use a wildcard certificate for development and testing, however you should not use it for any production services. 

The certificate and key should be in two pem-encoded files:
* A file for the certificate, for example, cert.pem. Make sure the file has the full certificate chain.
* A file for the key, for example, key.pem

Other formats can generally be converted to pem using tools like *openssl*.

> [!Note]
> If using a self-signed certificate, you'll need to do some extra work to consume the service. See [below](#consuming-services-secured-with-self-signed-certificates).
### 2. Deploy or update the service with SSL enabled
To deploy with SSL enabled, you make a call like you would for any other service, but pass `ssl_enabled=True`, and the contents of `cert.pem` to `ssl_certificate` and `key.pem` to `ssl_key`.
For example:
```python
from amlrealtimeai import DeploymentClient

subscription_id = "<Your Azure Subscription ID>"
resource_group = "<Your Azure Resource Group Name>"
model_management_account = "<Your AzureML Model Management Account Name>"
location = "eastus2"

model_name = "resnet50-model"
service_name = "quickstart-service"

deployment_client = DeploymentClient(subscription_id, resource_group, model_management_account, location)

with open('cert.pem','r') as cert_file:
    with open('key.pem','r') as key_file:
        cert = cert_file.read()
        key = key_file.read()
        service = deployment_client.create_service(service_name, model_id, ssl_enabled=True, ssl_certificate=cert, ssl_key=key)
```
Make note of the response to the call. You'll need the IP address to finish setting up SSL, and the Primary Key and Secondary Key to consume the service.
### 3. Update DNS
Update the DNS record for your domain name to resolve to the IP address of your service. Remember that the DNS name must match the certificate common name.

## Consuming authenticated services using Sample Clients
### Consuming authenticated services using Python
Example:
```python
from amlrealtimeai import PredictionClient
client = PredictionClient(service.ipAddress, service.port, use_ssl=True, access_token="authKey")
image_file = R'C:\path_to_file\image.jpg'
results = client.score_image(image_file)
```
### Consuming authenticated services using C#
```csharp
var client = new ScoringClient(host, 50051, useSSL, "authKey");
float[,] result;
using (var content = File.OpenRead(image))
    {
        IScoringRequest request = new ImageRequest(content);
        result = client.Score<float[,]>(request);
    }
```
## Consuming authenticated services using other gRPC clients
Azure Machine Learning authenticates clients by checking that the request contains a valid authorization header.

The general approach is to create a ChannelCredentials (or your language's equivalent), that combines SslCredentials with a CallCredentials that adds the authorization header to the metadata. 

For example, in C#:
```csharp
creds = ChannelCredentials.Create(baseCreds, CallCredentials.FromInterceptor(
                      async (context, metadata) =>
                      {
                          metadata.Add(new Metadata.Entry("authorization", "authKey"));
                          await Task.CompletedTask;
                      }));

```
or in Go:
```go
conn, err := grpc.Dial(serverAddr, 
    grpc.WithTransportCredentials(credentials.NewClientTLSFromCert(nil, "")),
    grpc.WithPerRPCCredentials(&authCreds{
    Key: "authKey"}))

type authCreds struct {
    Key string
}

func (c *authCreds) GetRequestMetadata(context.Context, uri ...string) (map[string]string, error) {
    return map[string]string{
        "authorization": c.Key,
    }, nil
}

func (c *authCreds) RequireTransportSecurity() bool {
    return true
}
```
See the [grpc docs](https://grpc.io/docs/guides/auth.html) for more information on how to implement support for your specific headers. Generally, you're looking for information about how to attach authentication metadata.

## Consuming services secured with self-signed certificates
> [!IMPORTANT]
> You should not use services secured with self-signed certificates in production.

gRPC provides a couple of ways to tell it which certificates are valid:
1. Set the `GRPC_DEFAULT_SSL_ROOTS_FILE_PATH` to point to the `cert.pem` file you used to deploy the service.
2. When constructing an SslCredentials object, pass the contents of the `cert.pem` file to the constructor.

Note that using either of these will cause GRPC to use that as the root cert instead of your normal root cert.   

gRPC will not accept untrusted certificates, and your client will fail with an Unavailable status code and the details "Connect Failed".