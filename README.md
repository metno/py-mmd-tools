# Py-MMD-Tools

[![pytest](https://github.com/metno/py-mmd-tools/actions/workflows/tests.yml/badge.svg)](https://github.com/metno/py-mmd-tools/actions/workflows/tests.yml)
[![codecov](https://codecov.io/gh/metno/py-mmd-tools/branch/master/graph/badge.svg)](https://codecov.io/gh/metno/py-mmd-tools)

Python tools for MMD. The package contains tools for generating MMD files from netCDF-CF files with ACDD attributes, for documenting netCDF-CF files from MMD information, and for updating the https://metno.github.io/data-management-handbook/[Data Management Handbook] with information about the translation from ACDD to MMD. Command line tools are available in the `scripts/` folder. For example,

```
./script/nc2mmd.py -i tests/data/reference_nc.nc -o .
```

generates an output MMD file called `reference_nc.xml`.

# Tests and syntax checking

Install pytest and pytest-cov

```
pip install pytest pytest-cov
```

To run the tests locally:
```
export MMD_PATH=<PATH TO MMD REPO>
python -m pytest -v --cov=py_mmd_tools --cov=script --cov-report=term --cov-report=xml
```

Or:
```
./run_tests.sh
```

## Syntax testing

Install flake8:
```
pip install flake8
```

Syntax error check:
```
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
```

Code style check:
```
flake8 . --count --max-line-length=99 --ignore E221,E226,E228,E241 --show-source --statistics
```
