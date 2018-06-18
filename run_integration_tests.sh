#!/bin/bash

conda env create -f environment.yml
source /etc/conda/bin/activate amlrealtimeai
conda install -y pytest
export TEST_SERVICE_PRINCIPAL_KEY=$1
pytest pythonlib/tests/integration_tests
ERR=$?
source /etc/conda/bin/activate base
conda env remove -y -n amlrealtimeai
exit $ERR
