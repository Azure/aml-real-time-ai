#!/bin/bash

dotnet test --project sample-clients/csharp/client.tests
ERR=$?
if [ $ERR -ne 0 ]
then
    exit $ERR
fi


conda env create -f environment.yml
source /etc/conda/bin/activate azureml_fpga
pip install pytest
pip install -e $(dirname "$0")/pythonlib --user
pytest pythonlib/tests/unit_tests
ERR=$?
source /etc/conda/bin/activate base
conda env remove -y -n azureml_fpga
if [ $ERR -ne 0 ]
then
    exit $ERR
fi


