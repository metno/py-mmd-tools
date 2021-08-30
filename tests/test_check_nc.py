"""
License:

This file is part of the py-mmd-tools repository
<https://github.com/metno/py-mmd-tools>.

py-mmd-tools is licensed under the Apache License 2.0
<https://github.com/metno/py-mmd-tools/blob/master/LICENSE>
"""

import os
import argparse

from script.check_nc import main

def test_create_parser(dataDir, parsedRefNC):
    ref0 = os.path.join(dataDir, 'reference_nc.nc')
    assert parsedRefNC.input == ref0

def test_main(parsedRefNC):
    res = main(parsedRefNC)
    assert res == None
