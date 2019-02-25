#!/bin/bash

dotnet test sample-clients/csharp/client.tests
ERR=$?
if [ $ERR -ne 0 ]
then
    exit $ERR
fi
source /usr/share/miniconda/etc/profile.d/conda.sh

conda env create -f environment.yml
conda activate amlrealtimeai
conda install -y pytest pytest-cov
python -m pytest --cov=pythonlib/amlrealtimeai pythonlib/tests/unit_tests
ERR=$?
conda activate base
conda env remove -y -n amlrealtimeai
if [ $ERR -ne 0 ]
then
    exit $ERR
fi
