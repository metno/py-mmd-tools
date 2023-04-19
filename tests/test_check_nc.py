"""
License:

This file is part of the py-mmd-tools repository
<https://github.com/metno/py-mmd-tools>.

py-mmd-tools is licensed under the Apache License 2.0
<https://github.com/metno/py-mmd-tools/blob/master/LICENSE>
"""

import os
import pytest
import shutil
import tempfile

from py_mmd_tools.script.check_nc import main
from py_mmd_tools.script.check_nc import create_parser


@pytest.mark.script
def test_main(parsedRefNC):
    """Test that main function runs with reference file from fixture"""
    res = main(parsedRefNC)
    assert res is None


@pytest.mark.script
def test_create_parser(dataDir):
    """Test create_parser method"""
    ref0 = os.path.join(dataDir, 'reference_nc.nc')
    parser = create_parser()
    parsed = parser.parse_args(['-i', ref0])
    assert parsed.input == ref0


@pytest.mark.script
def test_with_folder(dataDir):
    """Test check_nc.py with a folder as input"""
    parser = create_parser()
    in_dir = tempfile.mkdtemp()
    shutil.copy(os.path.join(dataDir, 'reference_nc.nc'), in_dir)
    parsed = parser.parse_args([
        '-i', in_dir,
    ])
    res = main(parsed)
    assert res is None
    shutil.rmtree(in_dir)


@pytest.mark.script
def test_invalid():
    """Test that the script raises ValueError if input is wrong"""
    parser = create_parser()
    parsed = parser.parse_args([
        '-i', 'nbm.snb',
    ])
    with pytest.raises(ValueError) as ve:
        main(parsed)
        assert ve.exception.code == 2


@pytest.mark.script
def test_main_thredds(dataDir, monkeypatch):
    """Test check_nc.py with a fake OPeNDAP file"""
    parser = create_parser()
    test_in = os.path.join(dataDir, 'dodsC', 'reference_nc.nc')
    parsed = parser.parse_args([
        '-i', test_in,
    ])
    with monkeypatch.context() as mp:
        mp.setattr('py_mmd_tools.nc_to_mmd.os.remove', lambda *a: None)
        res = main(parsed)
    assert res is None


@pytest.mark.script
def test_failing_ncfile(dataDir, capsys):
    """Check that nothing fails, even with invalid input file"""
    parser = create_parser()
    test_in = os.path.join(dataDir, 'reference_nc_fail.nc')
    parsed = parser.parse_args([
        '-i', test_in,
    ])
    main(parsed)
    captured = capsys.readouterr()
    assert captured.out.startswith('Not OK')
