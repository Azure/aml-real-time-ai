#!/bin/bash

dotnet test sample-clients/csharp/client.tests
ERR=$?
if [ $ERR -ne 0 ]
then
    exit $ERR
fi


conda env create -f environment.yml
source conda activate amlrealtimeai
conda install -y pytest pytest-cov
pytest --cov=pythonlib/amlrealtimeai pythonlib/tests/unit_tests
ERR=$?
source conda activate base
conda env remove -y -n amlrealtimeai
if [ $ERR -ne 0 ]
then
    exit $ERR
fi
