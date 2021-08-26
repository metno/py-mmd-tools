#!/bin/bash

export MMD_PATH=/tmp/mmd
git clone https://github.com/metno/mmd $MMD_PATH
python -m pytest -v --cov=py_mmd_tools --cov-report=term --cov-report=xml
