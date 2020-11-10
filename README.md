![tests](https://github.com/metno/py-mmd-tools/workflows/tests/badge.svg)
[![codecov](https://codecov.io/gh/metno/py-mmd-tools/branch/master/graph/badge.svg)](https://codecov.io/gh/metno/py-mmd-tools)

# py-mmd-tools

Python tools for MMD

To be able to request from FROST, one must have the environment variable FROST_ID set
`export FROST_ID='myfrostid'`


To run the tests locally:
```
nosetests --with-coverage --cover-xml --cover-package=py_mmd_tools
```

## script/oda_to_mmd.py

The access to `frost-staging.met.no` is restricted. So to be able to request ODA tags, one must be on met.no network.

