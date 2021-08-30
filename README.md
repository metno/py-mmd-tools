# Py-MMD-Tools

[![pytest](https://github.com/metno/py-mmd-tools/actions/workflows/tests.yml/badge.svg)](https://github.com/metno/py-mmd-tools/actions/workflows/tests.yml)
[![codecov](https://codecov.io/gh/metno/py-mmd-tools/branch/master/graph/badge.svg)](https://codecov.io/gh/metno/py-mmd-tools)

Python tools for MMD.

To run the tests locally:
```
export MMD_PATH=<PATH TO MMD REPO>
python -m pytest -vv --cov-report=term
```
## Development environment

The following command will set up a docker development environment running on a vagrant virtual machine, and run tests:

```
vagrant up
```

For repeated testing, ssh into the vm and run your code there:

```
vagrant ssh
cd /vagrant
sudo docker-compose -f docker-compose.tests.yml up --build --exit-code-from tests
```

For interactive work:

```
vagrant ssh
cd /vagrant
sudo docker start vagrant_tests_1
sudo docker exec -it vagrant_tests_1 bash
ipython
```


