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

from py_mmd_tools.script.nc2mmd import create_parser
from py_mmd_tools.script.nc2mmd import main


@pytest.mark.script
def test_main_localfile(dataDir):
    """Test nc2mmd.py with a local file"""
    parser = create_parser()
    test_in = os.path.join(dataDir, 'reference_nc.nc')
    out_dir = tempfile.mkdtemp()
    parsed = parser.parse_args([
        '-i', test_in,
        '--url', 'https://thredds.met.no/thredds/dodsC/reference_nc.nc',
        '-o', out_dir
    ])
    main(parsed)
    assert os.path.isfile(os.path.join(out_dir, 'reference_nc.xml'))
    shutil.rmtree(out_dir)


@pytest.mark.script
def test_main_localfile_missing_opendap(dataDir):
    parser = create_parser()
    test_in = os.path.join(dataDir, 'reference_nc.nc')
    out_dir = tempfile.mkdtemp()
    parsed = parser.parse_args([
        '-i', test_in,
        '-o', out_dir,
    ])
    with pytest.raises(ValueError) as ve:
        main(parsed)
    assert str(ve.value) == 'OPeNDAP url must be provided'


@pytest.mark.script
def test_main_localfile_missing_output_dir(dataDir):
    parser = create_parser()
    test_in = os.path.join(dataDir, 'reference_nc.nc')
    parsed = parser.parse_args([
        '-i', test_in,
        '-u', 'https://thredds.met.no/thredds/dodsC/reference_nc.nc',
    ])
    with pytest.raises(ValueError) as ve:
        main(parsed)
    assert str(ve.value) == 'MMD XML output directory must be provided'


@pytest.mark.script
def test_main_localfile_specify_collection(dataDir):
    parser = create_parser()
    test_in = os.path.join(dataDir, 'reference_nc.nc')
    out_dir = tempfile.mkdtemp()
    parsed = parser.parse_args([
        '-i', test_in,
        '-u', 'https://thredds.met.no/thredds/dodsC/reference_nc.nc',
        '-o', out_dir,
        '--collection', 'ADC'
    ])
    main(parsed)
    assert os.path.isfile(os.path.join(out_dir, 'reference_nc.xml'))
    shutil.rmtree(out_dir)


@pytest.mark.script
def test_main_thredds(dataDir, monkeypatch):
    """Test nc2mmd.py with a fake OPeNDAP file"""
    parser = create_parser()
    test_in = os.path.join(dataDir, 'reference_nc.nc')
    out_dir = tempfile.mkdtemp()
    parsed = parser.parse_args([
        '-i', test_in,
        '-u', 'https://thredds.met.no/thredds/dodsC/reference_nc.nc',
        '-o', out_dir,
        '-w'
    ])
    with monkeypatch.context() as mp:
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
        '-u', 'https://thredds.met.no/thredds/dodsC',
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
        '-u', 'lkjd',
        '-o', out_dir
    ])
    with pytest.raises(ValueError) as ve:
        main(parsed)
    assert 'Invalid input' in str(ve.value)


@pytest.mark.script
def test_dry_run(dataDir):
    """Test running the script with the dry-run option."""
    parser = create_parser()
    test_in = os.path.join(dataDir, 'reference_nc.nc')
    parsed = parser.parse_args([
        '-i', test_in,
        '--dry-run'
    ])
    main(parsed)
