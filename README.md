![tests](https://github.com/metno/py-mmd-tools/workflows/tests/badge.svg)
[![codecov](https://codecov.io/gh/metno/py-mmd-tools/branch/master/graph/badge.svg)](https://codecov.io/gh/metno/py-mmd-tools)

# py-mmd-tools

Python tools for MMD.

To run the tests locally:
```
nosetests --with-coverage --cover-xml --cover-package=py_mmd_tools
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


## script/oda_to_mmd.py

The access to `frost-staging.met.no` is restricted. So to be able to request ODA tags, one must be on met.no network.

To be able to request from FROST, one must have the environment variable FROST_ID set
`export FROST_ID='myfrostid'`
