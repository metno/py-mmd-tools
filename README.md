# Py-MMD-Tools

[![pytest](https://github.com/metno/py-mmd-tools/actions/workflows/tests.yml/badge.svg)](https://github.com/metno/py-mmd-tools/actions/workflows/tests.yml)
[![codecov](https://codecov.io/gh/metno/py-mmd-tools/branch/master/graph/badge.svg)](https://codecov.io/gh/metno/py-mmd-tools)

Python tools for MMD. The package contains tools for generating MMD files from netCDF-CF files with ACDD attributes, for documenting netCDF-CF files from MMD information, and for updating the [Data Management Handbook](https://metno.github.io/data-management-handbook/) with information about the translation from ACDD to MMD. Command line tools are available in the `py_mmd_tools/scripts/` folder. For example,

```
./py_mmd_tools/script/nc2mmd.py -i tests/data/reference_nc.nc -o .
```

generates an output MMD file called `reference_nc.xml`.

In addition, the `mmd_operations` module currently contains a tool to move data
files and accordingly update MMD files registered in online catalogs. This
module can be extended with other necessary data management tools. Moving
can be done with the `move_data` script, e.g.:

```
move_data /path/to/files-from-git/mmd-xml-<env> /path/to/old/storage /path/to/new/storage "%Y/%m/%d/*.nc" --dmci-update
```

The two last arguments provide a search pattern in case the netCDF files are
stored in subfolders, and to directly updated the metadata catalog,
respectively. If --dmci-update is not provided, local MMD files will not be
pushed to the catalog.

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

or (for development)

```text
pip install . --editable
```

All dependencies should now be installed, and the following command should generate an MMD file:

```text
nc2mmd -i tests/data/reference_nc.nc -o .
```

(alternatively use `export PYTHONPATH=$PWD`)

## Known issue: 'Error:curl error: Problem with the SSL CA cert (path? access rights?)'

If this problem is encountered please add a file in your home directory named `.ncrc` and add this line: `HTTP.SSL.CAINFO=/etc/ssl/certs/ca-certificates.crt`

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
