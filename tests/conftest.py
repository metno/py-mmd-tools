"""
License:

This file is part of the py-mmd-tools repository
<https://github.com/metno/py-mmd-tools>.

py-mmd-tools is licensed under the Apache License 2.0
<https://github.com/metno/py-mmd-tools/blob/master/LICENSE>
"""

import os
import sys

import pytest

from script.check_nc import create_parser

# Note: This line forces the test suite to import the dmci package in the current source tree
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))

@pytest.fixture(scope="session")
def rootDir():
    """The root folder of the repository."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))

@pytest.fixture(scope="session")
def dataDir():
    """A path to the reference files folder."""
    testDir = os.path.dirname(__file__)
    theDir = os.path.join(testDir, "data")
    return theDir

@pytest.fixture(scope="session")
def parsedRefNC(dataDir):
    ref0 = os.path.join(dataDir, 'reference_nc.nc')
    parser = create_parser()
    parsed = parser.parse_args(['-i', ref0])
    return parsed
