# Microsoft Azure Machine Learning Hardware Accelerated Models Powered by Project Brainwave

Easily create and train a model using various deep neural networks (DNNs) as a featurizer for deployment on Azure for ultra-low latency inferencing.

## How to get access

Azure ML Hardware Accelerated Models is currently in preview.

### Step 1: Create an Azure ML workspace

Follow the instructions in the 00.configuration.ipynb notebook in the [Azure ML MachineLearningNotebooks](https://aka.ms/aml-notebooks) repo.  You will create an Azure Machine Learning workspace, which is required for the next step.

Once you have set up your environment, install the contrib extras:

```sh
pip install --upgrade azureml-sdk[contrib]
```
**Note:** Only workspaces in the **East US 2** region are currently supported.

Go to the [documentation](https://docs.microsoft.com/en-us/azure/machine-learning/service/how-to-deploy-fpga-web-service) page for any questions.

### Step 2: Deploy your service

Check out the sample notebooks [here](https://aka.ms/aml-notebooks) under project-brainwave.

**Note:** If you want to deploy more than one service, you must [request quota](https://aka.ms/aml-real-time-ai-request) by submitting the form.  You will need information from your workspace created in Step 1 ([learn how to get workspace information](docs/README.md)).  You will receive an email if your quota request has been successful.

## Support
Read the [docs](docs) or visit the [forum](https://aka.ms/aml-forum).

# Contributing

This project welcomes contributions and suggestions.  Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit https://cla.microsoft.com.

When you submit a pull request, a CLA-bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., label, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

## Build Status

System | Unit tests | Integration Tests
--- | --- | ---
Ubuntu 16.04 | [![Build Status](https://msdata.visualstudio.com/_apis/public/build/definitions/3adb301f-9ede-41f2-933b-fcd1a486ff7f/2908/badge)](https://msdata.visualstudio.com/Vienna/_build/index?definitionId=2908) | [![Build Status](https://msdata.visualstudio.com/_apis/public/build/definitions/3adb301f-9ede-41f2-933b-fcd1a486ff7f/2916/badge)](https://msdata.visualstudio.com/Vienna/_build/index?definitionId=2916)
