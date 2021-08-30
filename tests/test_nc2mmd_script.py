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

from script.nc2mmd import create_parser
from script.nc2mmd import main

@pytest.mark.script
def test_main_localfile(dataDir):
    """Test nc2mmd.py with a local file"""
    parser = create_parser()
    test_in = os.path.join(dataDir, 'reference_nc.nc')
    out_dir = tempfile.mkdtemp()
    parsed = parser.parse_args([
        '-i', test_in,
        '-o', out_dir
    ])
    main(parsed)
    assert os.path.isfile(os.path.join(out_dir, 'reference_nc.xml'))
    shutil.rmtree(out_dir)

@pytest.mark.script
def test_main_thredds(dataDir, monkeypatch):
    """Test nc2mmd.py with a fake OPeNDAP file"""
    parser = create_parser()
    test_in = os.path.join(dataDir, 'dodsC', 'reference_nc.nc')
    out_dir = tempfile.mkdtemp()
    parsed = parser.parse_args([
        '-i', test_in,
        '-o', out_dir,
        '-w'
    ])
    with monkeypatch.context() as mp:
        mp.setattr('py_mmd_tools.nc_to_mmd.wget.download', lambda *a: test_in)
        mp.setattr('py_mmd_tools.nc_to_mmd.os.remove', lambda *a: None)
        main(parsed)
    assert os.path.isfile(os.path.join(out_dir, 'reference_nc.xml'))
    shutil.rmtree(out_dir)

@pytest.mark.script
def test_with_folder(dataDir):
    """Test nc2mmd.py with a folder as input"""
    parser = create_parser()
    in_dir = tempfile.mkdtemp()
    shutil.copy(os.path.join(dataDir, 'reference_nc.nc'), in_dir)
    out_dir = tempfile.mkdtemp()
    parsed = parser.parse_args([
        '-i', in_dir,
        '-o', out_dir
    ])
    main(parsed)
    assert os.path.isfile(os.path.join(out_dir, 'reference_nc.xml'))
    shutil.rmtree(out_dir)
    shutil.rmtree(in_dir)

@pytest.mark.script
def test_invalid():
    """Test that the script raises ValueError if input is wrong"""
    parser = create_parser()
    out_dir = tempfile.mkdtemp()
    parsed = parser.parse_args([
        '-i', 'nbm.snb',
        '-o', out_dir
    ])
    with pytest.raises(ValueError) as ve:
        main(parsed)
        assert ve.exception.code == 2
