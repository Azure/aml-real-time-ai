# Docs

## Set Up Environment

Set up your machine.

1. Download and install [Git](https://git-scm.com/downloads) 2.16 or later
1. Open a Git prompt and clone this repo:

   `git clone https://github.com/Azure/aml-real-time-ai`
1. Install conda (Python 3.6):

   https://conda.io/miniconda.html
1. Open an Anaconda Prompt and run the rest of the commands in the prompt. On Windows the prompt will look like:

   `(base) C:\>`
1. Create the environment:

   `conda env create -f aml-real-time-ai/environment.yml`
1. Activate the environment:

   `conda activate amlrealtimeai`
1. Launch the Jupyter notebook browser:

   `jupyter notebook` 
1. In the browser, open this notebook by navigating to examples/resnet50/00_QuickStart.ipynb.  (If you're using Chrome, copy and paste the URL with the notebook token into the address bar).

 ## Create Azure ML Model Management Account
1. Go to the Model Management Account (MMA) creation page in the [Azure Portal](https://aka.ms/aml-create-mma)

   If you have an existing MMA in the Azure **East US 2** region, you may skip this step.

   ![Create Model Management Account](media/azure-portal-create-mma.PNG)

1. Give your MMA a name, choose a subscription, and choose a resource group.

   **IMPORTANT:** For Location, you MUST choose **East US 2** as the region.  No other regions are currently available.

1. Choose a pricing tier (S1 is sufficient, but S2 and S3 also work).  The DevTest tier is not supported.  Click **Select** on the pricing tier blade and then click **Create** on the ML Model Management blade.

## Get MMA Information
When you need information about your MMA, click the MMA on the Azure Portal.

You will need these items:
1. MMA name (this is found on the upper left corner)
1. Resource group name
1. Subscription ID
1. Location (use "eastus2") in your code

![Model Management Account info](media/azure-portal-mma-info.PNG) 

