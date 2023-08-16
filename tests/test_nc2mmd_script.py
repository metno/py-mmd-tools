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
import uuid

import pytest

from netCDF4 import Dataset

from py_mmd_tools.script.nc2mmd import create_parser
from py_mmd_tools.script.nc2mmd import main


class MockDataset:
    def __init__(self, *args, **kwargs):
        pass

    def close(self):
        pass


def patchedDataset(url, *args, **kwargs):
    if args[0] == url:
        return MockDataset(*args, **kwargs)
    else:
        return Dataset(*args, **kwargs)


@pytest.mark.script
def test_main_localfile(dataDir, monkeypatch):
    """Test nc2mmd.py with a local file"""
    parser = create_parser()
    test_in = os.path.join(dataDir, 'reference_nc.nc')
    out_dir = tempfile.mkdtemp()
    url = 'https://thredds.met.no/thredds/dodsC/reference_nc.nc'
    parsed = parser.parse_args([
        '-i', test_in,
        '--url', url,
        '-o', out_dir
    ])
    with monkeypatch.context() as mp:
        mp.setattr("py_mmd_tools.nc_to_mmd.Dataset",
                   lambda *args, **kwargs: patchedDataset(url, *args, **kwargs))
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
    url = 'https://thredds.met.no/thredds/dodsC/reference_nc.nc'
    parsed = parser.parse_args([
        '-i', test_in,
        '-u', url,
    ])
    with pytest.raises(ValueError) as ve:
        main(parsed)
    assert str(ve.value) == 'MMD XML output directory must be provided'


@pytest.mark.script
def test_main_localfile_specify_collection(dataDir, monkeypatch):
    parser = create_parser()
    test_in = os.path.join(dataDir, 'reference_nc.nc')
    out_dir = tempfile.mkdtemp()
    url = 'https://thredds.met.no/thredds/dodsC/reference_nc.nc'
    parsed = parser.parse_args([
        '-i', test_in,
        '-u', url,
        '-o', out_dir,
        '--collection', 'ADC'
    ])
    with monkeypatch.context() as mp:
        mp.setattr("py_mmd_tools.nc_to_mmd.Dataset",
                   lambda *args, **kwargs: patchedDataset(url, *args, **kwargs))
        main(parsed)
        assert os.path.isfile(os.path.join(out_dir, 'reference_nc.xml'))
    shutil.rmtree(out_dir)


@pytest.mark.script
def test_main_thredds(dataDir, monkeypatch):
    """Test nc2mmd.py with a fake OPeNDAP file"""
    parser = create_parser()
    test_in = os.path.join(dataDir, 'reference_nc.nc')
    out_dir = tempfile.mkdtemp()
    url = 'https://thredds.met.no/thredds/dodsC/reference_nc.nc'
    parsed = parser.parse_args([
        '-i', test_in,
        '-u', url,
        '-o', out_dir,
        '-w'
    ])
    with monkeypatch.context() as mp:
        mp.setattr('py_mmd_tools.nc_to_mmd.os.remove', lambda *a: None)
        mp.setattr("py_mmd_tools.nc_to_mmd.Dataset",
                   lambda *args, **kwargs: patchedDataset(url, *args, **kwargs))
        main(parsed)
    assert os.path.isfile(os.path.join(out_dir, 'reference_nc.xml'))
    shutil.rmtree(out_dir)


@pytest.mark.script
def test_with_folder(dataDir, monkeypatch):
    """Test nc2mmd.py with a folder as input"""
    parser = create_parser()
    in_dir = tempfile.mkdtemp()
    shutil.copy(os.path.join(dataDir, 'reference_nc.nc'), in_dir)
    shutil.copy(os.path.join(dataDir, 'reference_nc.nc'), os.path.join(in_dir,
        'reference_nc_copy.nc'))
    assert os.path.isfile(os.path.join(in_dir, 'reference_nc_copy.nc'))

    out_dir = tempfile.mkdtemp()
    url = 'https://thredds.met.no/thredds/dodsC'
    parsed = parser.parse_args([
        '-i', in_dir,
        '-u', url,
        '-o', out_dir,
        '--log-ids', os.path.join(out_dir, "dataset_ids.txt"),
    ])

    # Repetion of IDs
    with monkeypatch.context() as mp:
        mp.setattr("py_mmd_tools.nc_to_mmd.Dataset",
                   lambda *args, **kwargs: patchedDataset(url, *args, **kwargs))
        with pytest.raises(ValueError) as ve:
            main(parsed)
    assert os.path.isfile(os.path.join(out_dir, 'reference_nc.xml'))
    assert "Unique ID repetition" in str(ve.value)
    os.unlink(os.path.join(in_dir, 'reference_nc_copy.nc'))

    # Check that an file with dataset IDs is written
    with monkeypatch.context() as mp:
        mp.setattr("py_mmd_tools.nc_to_mmd.Dataset",
                   lambda *args, **kwargs: patchedDataset(url, *args, **kwargs))
        main(parsed)
    assert os.path.isfile(os.path.join(out_dir, "dataset_ids.txt"))

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
