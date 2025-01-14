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
    test_in = os.path.join(dataDir, "reference_nc.nc")
    out_dir = tempfile.mkdtemp()
    url = "https://thredds.met.no/thredds/dodsC/reference_nc.nc"
    parsed = parser.parse_args([
        "-i", test_in,
        "--url", url,
        "-o", out_dir
    ])
    with monkeypatch.context() as mp:
        mp.setattr("py_mmd_tools.nc_to_mmd.Dataset",
                   lambda *args, **kwargs: patchedDataset(url, *args, **kwargs))
        main(parsed)
        assert os.path.isfile(os.path.join(out_dir, "reference_nc.xml"))
    shutil.rmtree(out_dir)


@pytest.mark.script
def test_main_localfile_missing_opendap(dataDir):
    parser = create_parser()
    test_in = os.path.join(dataDir, "reference_nc.nc")
    out_dir = tempfile.mkdtemp()
    parsed = parser.parse_args([
        "-i", test_in,
        "-o", out_dir,
    ])
    with pytest.raises(ValueError) as ve:
        main(parsed)
    assert str(ve.value) == "OPeNDAP url must be provided"


@pytest.mark.script
def test_main_localfile_missing_output_dir(dataDir):
    parser = create_parser()
    test_in = os.path.join(dataDir, "reference_nc.nc")
    url = "https://thredds.met.no/thredds/dodsC/reference_nc.nc"
    parsed = parser.parse_args([
        "-i", test_in,
        "-u", url,
    ])
    with pytest.raises(ValueError) as ve:
        main(parsed)
    assert str(ve.value) == "MMD XML output directory must be provided"


@pytest.mark.script
def test_main_localfile_specify_collection(dataDir, monkeypatch):
    parser = create_parser()
    test_in = os.path.join(dataDir, "reference_nc.nc")
    out_dir = tempfile.mkdtemp()
    url = "https://thredds.met.no/thredds/dodsC/reference_nc.nc"
    parsed = parser.parse_args([
        "-i", test_in,
        "-u", url,
        "-o", out_dir,
        "--collection", "ADC"
    ])
    with monkeypatch.context() as mp:
        mp.setattr("py_mmd_tools.nc_to_mmd.Dataset",
                   lambda *args, **kwargs: patchedDataset(url, *args, **kwargs))
        main(parsed)
        assert os.path.isfile(os.path.join(out_dir, "reference_nc.xml"))
    shutil.rmtree(out_dir)


@pytest.mark.script
def test_main_localfile_more_than_1_dot_in_filename(dataDir, monkeypatch):
    parser = create_parser()
    test_in = os.path.join(dataDir, "reference.withextradot_nc.nc")
    out_dir = tempfile.mkdtemp()
    url = "https://thredds.met.no/thredds/dodsC/reference.withextradot_nc.nc"
    parsed = parser.parse_args([
        "-i", test_in,
        "-u", url,
        "-o", out_dir,
    ])
    with monkeypatch.context() as mp:
        mp.setattr("py_mmd_tools.nc_to_mmd.Dataset",
                   lambda *args, **kwargs: patchedDataset(url, *args, **kwargs))
        main(parsed)
        assert os.path.isfile(os.path.join(out_dir, "reference.withextradot_nc.xml"))
    shutil.rmtree(out_dir)


@pytest.mark.script
def test_main_thredds(dataDir, monkeypatch):
    """Test nc2mmd.py with a fake OPeNDAP file"""
    parser = create_parser()
    test_in = os.path.join(dataDir, "reference_nc.nc")
    out_dir = tempfile.mkdtemp()
    url = "https://thredds.met.no/thredds/dodsC/reference_nc.nc"
    parsed = parser.parse_args([
        "-i", test_in,
        "-u", url,
        "-o", out_dir,
        "-w"
    ])
    with monkeypatch.context() as mp:
        mp.setattr("py_mmd_tools.nc_to_mmd.os.remove", lambda *a: None)
        mp.setattr("py_mmd_tools.nc_to_mmd.Dataset",
                   lambda *args, **kwargs: patchedDataset(url, *args, **kwargs))
        main(parsed)
    assert os.path.isfile(os.path.join(out_dir, "reference_nc.xml"))
    shutil.rmtree(out_dir)


@pytest.mark.script
def test_with_folder(dataDir, monkeypatch):
    """Test nc2mmd.py with a folder as input

    Note: The function main() in patchedDataset (defined in nc2mmd.py)
          parses the input folder for .nc files via glob, i.e.:

          inputfiles = pathlib.Path(args.input).glob('*.nc')

          Which of the files 'reference_nc_copy.nc' or
          'reference_nc_copy.nc' gets parsed first, resulting in the
          corresponding .xml file being in out_dir, depends on the
          filesystem (see glob.glob in
          https://docs.python.org/3/library/glob.html). This is the
          reason why we use an 'or' condition to assert the presence
          of the .xml file in the output.
    """
    parser = create_parser()
    in_dir = tempfile.mkdtemp()
    shutil.copy(os.path.join(dataDir, "reference_nc.nc"), in_dir)
    shutil.copy(os.path.join(dataDir, "reference_nc.nc"),
                os.path.join(in_dir, "reference_nc_copy.nc"))
    assert os.path.isfile(os.path.join(in_dir, "reference_nc_copy.nc"))
    assert os.path.isfile(os.path.join(in_dir, "reference_nc.nc"))

    out_dir = tempfile.mkdtemp()
    url = "https://thredds.met.no/thredds/dodsC"
    parsed = parser.parse_args([
        "-i", in_dir,
        "-u", url,
        "-o", out_dir,
        "--log-ids", os.path.join(out_dir, "dataset_ids.txt"),
    ])

    # Repetion of IDs
    with monkeypatch.context() as mp:
        mp.setattr("py_mmd_tools.nc_to_mmd.Dataset",
                   lambda *args, **kwargs: patchedDataset(url, *args, **kwargs))
        with pytest.raises(ValueError) as ve:
            main(parsed)
    filcheckopt1 = os.path.isfile(os.path.join(out_dir, "reference_nc.xml"))
    filcheckopt2 = os.path.isfile(os.path.join(out_dir, "reference_nc_copy.xml"))
    assert filcheckopt1 or filcheckopt2
    assert "Unique ID repetition" in str(ve.value)
    os.unlink(os.path.join(in_dir, "reference_nc_copy.nc"))

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
        "-i", "nbm.snb",
        "-u", "lkjd",
        "-o", out_dir
    ])
    with pytest.raises(ValueError) as ve:
        main(parsed)
    assert "Invalid input" in str(ve.value)


@pytest.mark.script
def test_dry_run(dataDir):
    """Test running the script with the dry-run option."""
    parser = create_parser()
    test_in = os.path.join(dataDir, "reference_nc.nc")
    parsed = parser.parse_args([
        "-i", test_in,
        "--dry-run"
    ])
    main(parsed)


@pytest.mark.script
def test_override_file_location(dataDir):
    """Test overriding the file location"""
    alt_loc = "/some/where/else"
    out_dir = tempfile.mkdtemp()
    test_in = os.path.join(dataDir, "reference_nc.nc")
    parser = create_parser()
    parsed = parser.parse_args([
        "-i", test_in,
        "-u", "https://thredds.met.no/thredds",
        "-o", out_dir,
        "--file_location", alt_loc,
    ])
    main(parsed)
    assert os.path.isfile(os.path.join(out_dir, "reference_nc.xml"))
    with open(os.path.join(out_dir, "reference_nc.xml")) as fn:
        lines = fn.readlines()
    assert "<mmd:file_location>" + alt_loc + "</mmd:file_location>" in "".join(lines)
