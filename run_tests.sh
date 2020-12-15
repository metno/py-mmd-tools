#!/bin/bash

nosetests --with-coverage --cover-xml --cover-xml-file=/src/coverage.xml --cover-package=py_mmd_tools || exit 1
#nosetests --with-coverage --cover-xml --cover-xml-file=/src/coverage.xml --cover-package=py_mmd_tools tests.test_odajson_to_mmd:TestODA2MMD.test_retrieve_frost_stations__valid


echo

if [[ -n "$CODECOV_TOKEN" ]]
then
  bash <(curl -s https://codecov.io/bash)
else
  echo %%
  echo %% Do you want code coverage generated on https://codecov.io with GitHub Actions.
  echo %%
  echo "%%   1. Add repository to codecov.io."
  echo "%%   2. Add a repository secret in [ Setting > Secrets ]."
  echo "%%      Name it CODECOV_TOKEN, and use the token from codecov.io as value."
  echo %%
fi

