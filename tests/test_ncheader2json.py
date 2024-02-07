"""
License:

This file is part of the py-mmd-tools repository
<https://github.com/metno/py-mmd-tools>.

py-mmd-tools is licensed under the Apache License 2.0
<https://github.com/metno/py-mmd-tools/blob/master/LICENSE>
"""

import os
import json
import pytest
import tempfile
import glob

import numpy as np

from py_mmd_tools.script.ncheader2json import create_parser
from py_mmd_tools.script.ncheader2json import main
from py_mmd_tools.script.ncheader2json import get_header_netCDF
from py_mmd_tools.script.ncheader2json import handle_numpy_types
from netCDF4 import Dataset


@pytest.mark.script
def test_main(dataDir):
    """Test that the created json file contains correct dataset id"""
    parser = create_parser()
    test_in = os.path.join(dataDir, "reference_nc.nc")
    fd, test_out = tempfile.mkstemp(suffix=".json")
    parsed = parser.parse_args(["-i", test_in, "-o", test_out])
    main(parsed)
    with open(test_out, "r") as fp:
        ncheader = json.load(fp)
    assert ncheader["global_variables"]["id"] == "b7cb7934-77ca-4439-812e-f560df3fe7eb"
    os.remove(test_out)
    parsed = parser.parse_args(["-i", test_in])
    ncheader = main(parsed)
    assert ncheader["global_variables"]["id"] == "b7cb7934-77ca-4439-812e-f560df3fe7eb"


@pytest.mark.script
def test_main_raise_error():
    parser = create_parser()
    parsed = parser.parse_args(["-i", "this_path_should_not_exsist"])
    with pytest.raises(ValueError):
        main(args=parsed)


@pytest.mark.script
def test_read_folder(dataDir):
    parser = create_parser()
    temp_dir = tempfile.gettempdir()
    parsed = parser.parse_args(["-i", dataDir, "-o", temp_dir])
    main(parsed)
    assert True


@pytest.mark.script
@pytest.mark.parametrize(
    "dataDir, test_input, expected",
    [
        ("_", np.float32(0.1), np.float64),
        ("_", np.int64(1), int),
        ("_", np.ndarray([1, 2, 3]), list),
    ],
)
def test_handle_numpy_types(dataDir, test_input, expected):
    assert isinstance(handle_numpy_types(test_input), expected)


@pytest.mark.script
def test_get_header_netCDF(dataDir):
    with open(os.path.join(dataDir, "reference_nc_header.json")) as file:
        expected = json.load(file)
    test_input = get_header_netCDF(Dataset(os.path.join(dataDir, "reference_nc.nc")))
    assert json.dumps(json.loads(test_input), sort_keys=True) == json.dumps(
        expected, sort_keys=True
    )
