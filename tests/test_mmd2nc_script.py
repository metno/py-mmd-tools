"""
License:

This file is part of the py-mmd-tools repository
<https://github.com/metno/py-mmd-tools>.

py-mmd-tools is licensed under the Apache License 2.0
<https://github.com/metno/py-mmd-tools/blob/master/LICENSE>
"""
import os
import shutil
import tempfile

import pytest

from script.mmd2nc import create_parser
from script.mmd2nc import main


@pytest.mark.script
def test_main_localfile(dataDir):
    """Test mmd2nc.py with a local file"""
    parser = create_parser()
    test_mmd_in = os.path.join(dataDir, 'reference_nc.xml')
    test_nc_in = os.path.join(dataDir, 'nc_to_update.nc')
    tested = tempfile.mkstemp()[1]
    shutil.copy(test_nc_in, tested)
    parsed = parser.parse_args([
        '-m', test_mmd_in,
        '-n', tested
    ])
    main(parsed)
    assert os.path.isfile(tested)


@pytest.mark.script
def test_invalid_mmd(dataDir):
    """Test that the script raises ValueError if input MMD xml does not exist"""
    parser = create_parser()
    test_mmd_in = os.path.join(dataDir, 'toto.xml')
    test_nc_in = os.path.join(dataDir, 'toto.nc')
    parsed = parser.parse_args([
        '-m', test_mmd_in,
        '-n', test_nc_in
    ])
    with pytest.raises(ValueError) as ve:
        main(parsed)
        assert ve.exception.code == 2


@pytest.mark.script
def test_invalid_nc(dataDir):
    """Test that the script raises ValueError if input netcdf file does not exist"""
    parser = create_parser()
    test_mmd_in = os.path.join(dataDir, 'reference_mmd.xml')
    test_nc_in = os.path.join(dataDir, 'toto.nc')
    parsed = parser.parse_args([
        '-m', test_mmd_in,
        '-n', test_nc_in
    ])
    with pytest.raises(ValueError) as ve:
        main(parsed)
        assert ve.exception.code == 2
