#!/bin/bash

dotnet test sample-clients/csharp/client.tests
ERR=$?
if [ $ERR -ne 0 ]
then
    exit $ERR
fi


conda env create -f environment.yml
source /etc/conda/bin/activate amlrealtimeai
conda install pytest
pytest pythonlib/tests/unit_tests
ERR=$?
source /etc/conda/bin/activate base
conda env remove -y -n amlrealtimeai
if [ $ERR -ne 0 ]
then
    exit $ERR
fi
