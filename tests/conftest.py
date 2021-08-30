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

# Note: This line forces the test suite to import the dmci package in the current source tree
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
sys.path.insert(1, os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.path.pardir, "script"))
)

@pytest.fixture
def dataDir():
    """A folder with example test data"""
    testDir = os.path.dirname(__file__)
    theDir = os.path.join(testDir, "data")
    return theDir
