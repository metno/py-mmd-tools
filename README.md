# Py-MMD-Tools

[![pytest](https://github.com/metno/py-mmd-tools/actions/workflows/tests.yml/badge.svg)](https://github.com/metno/py-mmd-tools/actions/workflows/tests.yml)
[![codecov](https://codecov.io/gh/metno/py-mmd-tools/branch/master/graph/badge.svg)](https://codecov.io/gh/metno/py-mmd-tools)

Python tools for MMD. The package contains tools for generating MMD files from netCDF-CF files with ACDD attributes, for documenting netCDF-CF files from MMD information, and for updating the https://metno.github.io/data-management-handbook/[Data Management Handbook] with information about the translation from ACDD to MMD. Command line tools are available in the `scripts/` folder. For example,

```
./script/nc2mmd.py -i tests/data/reference_nc.nc -o .
```

generates an output MMD file called `reference_nc.xml`.

# Installation

To avoid problems with conflicting versions, we recommend using the [Conda](
https://docs.conda.io/projects/conda/en/latest/user-guide/getting-started.html) package manager.
The below steps assume that Conda is installed.

Create a new environment:

```text
conda create --name testenv python=3.9
```

Verify that the new environment is registered:

```text
conda info --envs
```

Activate (use) the new environment:

```text
conda activate testenv
```

Install the Py-MMD-Tools package:

```text
pip install .
```

Provided that all dependencies happen to already be installed, the following should work
(and generate an MMD file):

```text
PYTHONPATH=. nc2mmd -i tests/data/reference_nc.nc -o .
```

If the command fails due to missing packages (see `conda list`), these may now be installed like
this (for a given package P):

```text
conda install P
```

**Tip:** Sometimes `pip install P` works if `conda install P` doesn't.

## Installing metvocab

The *metvocab* package can be installed like this:

```text
pip install metvocab@git+https://github.com/metno/met-vocab-tools@v1.0.1
```

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
