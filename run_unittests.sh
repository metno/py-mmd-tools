#!/bin/bash

nosetests --with-coverage --cover-package=py_mmd_tools

#if [[ -n "$CODECOV_TOKEN" ]]; then
bash <(curl -s https://codecov.io/bash)
#fi
