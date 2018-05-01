# Microsoft Azure Machine Learning Hardware Accelerated Models Powered by Project Brainwave

Easily create and train a model using ResNet 50 as a featurizer for deployment on Azure for ultra-low latency inferencing.

## How to get access

Azure ML Hardware Accelerated Models is currently in preview.

### Step 1: Create an Azure ML Model Management Account

Go to the [Azure Portal](https://aka.ms/aml-create-mma) and create an Azure ML Model Management Account (MMA).  [Learn how to create a MMA](docs/README.md#create-azure-ml-model-management-account).  If you already have an existing S1, S2, or S3 account in the East US 2 location, you may skip this step.  The DevTest tier is not supported.

**Note:** Only accounts in the **East US 2** region are currently supported.

### Step 2: Fill out the request form

[Request quota](https://forms.office.com/Pages/ResponsePage.aspx?id=v4j5cvGGr0GRqy180BHbR2nac9-PZhBDnNSV2ITz0LNURFJDR1NWMklTMU0xUTZUMjNWRkxHRzJOUC4u) by submitting the form.

You will need the name of your MMA from Step 1 ([learn how to get the MMA name](docs/README.md#get-mma-information)).

You will receive an email if your quota request has been successful.

### Step 3: Set up environment

Follow [these instructions](docs/README.md#set-up-environment) to set up your environment.

### Step 4: Deploy your service

Check out the sample notebooks [here](notebooks/resnet50).  You can easily deploy a ResNet 50 classifier by running the [Quickstart notebook](notebooks/resnet50/00_QuickStart.ipynb).

## Support
Read the [docs](docs) or email amlfpgafc@microsoft.com.

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