#!/bin/bash

dotnet test sample-clients/csharp/client.tests
ERR=$?
if [ $ERR -ne 0 ]
then
    exit $ERR
fi


sudo conda env create -f environment.yml
conda activate amlrealtimeai
sudo conda install -y pytest pytest-cov
pytest --cov=pythonlib/amlrealtimeai pythonlib/tests/unit_tests
ERR=$?
conda activate base
conda env remove -y -n amlrealtimeai
if [ $ERR -ne 0 ]
then
    exit $ERR
fi
