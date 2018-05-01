#!/bin/bash

conda env create -f environment.yml
source /etc/conda/bin/activate amlrealtimeai
pip install pytest
pip install -e $(dirname "$0")/pythonlib --user
pytest pythonlib/tests/integration_tests
ERR=$?
source /etc/conda/bin/activate base
conda env remove -y -n amlrealtimeai
exit $ERR
