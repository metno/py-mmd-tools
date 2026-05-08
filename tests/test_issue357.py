"""
Test for issue #357: Variables containing 'lat' or 'lon' as substrings are
incorrectly filtered out when generating WMS layer lists.

License:

This file is part of the py-mmd-tools repository
<https://github.com/metno/py-mmd-tools>.

py-mmd-tools is licensed under the Apache License 2.0
<https://github.com/metno/py-mmd-tools/blob/master/LICENSE>
"""

import os
import pytest

from netCDF4 import Dataset

from py_mmd_tools.nc_to_mmd import Nc_to_mmd

from tests.test_nc2mmd_script import patchedDataset


@pytest.mark.py_mmd_tools
def test_wms_layer_no_false_positives_from_lat_lon(monkeypatch):
    """Issue #357: variables whose name contains 'lat' or 'lon' as a
    substring must NOT be excluded from WMS layers.

    'relative_humidity' contains 'lat' (r-e-l-a-t-i-v-e) and must appear in
    the WMS layer list. Only variables whose standard_name IS exactly one of the
    coordinate names ('lat', 'lon', 'latitude', 'longitude', …) should be
    skipped.
    """
    netcdf_file = os.path.abspath('tests/data/reference_nc.nc')
    opendap_url = (
        'https://thredds.met.no/thredds/dodsC/arcticdata/'
        'S2S_drift_TCD/SIDRIFT_S2S_SH/2019/07/31/'
    ) + netcdf_file

    # Build an in-memory NetCDF dataset that includes:
    #  - a variable whose name contains "lat" as a substring — must be included
    #  - coordinate variables named "lat" and "lon" — must be excluded by name
    #  - a variable named "whatever" with standard_name "longitude" — must be
    #    excluded by standard_name even though the variable name is not in skip_layers
    #  - a plain variable "air_temperature" — must be included
    ncin = Dataset(netcdf_file, "w", diskless=True)
    ncin.createDimension("x", 4)
    lat_var = ncin.createVariable("lat", "f4", ("x",))
    lat_var.standard_name = "latitude"
    lon_var = ncin.createVariable("lon", "f4", ("x",))
    lon_var.standard_name = "longitude"
    rh_var = ncin.createVariable("relative_humidity_2m", "f4", ("x",))
    rh_var.standard_name = "relative_humidity"
    t_var = ncin.createVariable("air_temperature", "f4", ("x",))
    t_var.standard_name = "air_temperature"
    whatever_var = ncin.createVariable("whatever", "f4", ("x",))
    whatever_var.standard_name = "longitude"

    with monkeypatch.context() as mp:
        mp.setattr("py_mmd_tools.nc_to_mmd.Dataset",
                   lambda *args, **kwargs: patchedDataset(opendap_url, *args, **kwargs))
        md = Nc_to_mmd(netcdf_file, opendap_url, check_only=True)
        data = md.get_data_access_dict(ncin, add_wms_data_access=True,
                                       wms_link='http://test-wms')

    ncin.close()

    wms_data = next(d for d in data if d["type"] == "OGC WMS")
    wms_layers = wms_data["wms_layers"]

    # Must be included: variable name "relative_humidity_2m" contains "lat" as
    # a substring (r-e-l-a-t-i-v-e...) but is not a coordinate variable
    assert "relative_humidity_2m" in wms_layers, (
        f"'relative_humidity_2m' should be a valid WMS layer but was filtered out. "
        f"Got: {wms_layers}"
    )
    # Must be included: unrelated variable
    assert "air_temperature" in wms_layers, (
        f"'air_temperature' should be a valid WMS layer but was filtered out. "
        f"Got: {wms_layers}"
    )
    # Must be excluded: exact coordinate variable names
    assert "lat" not in wms_layers, (
        "'lat' is a coordinate variable and must be excluded from WMS layers"
    )
    assert "lon" not in wms_layers, (
        "'lon' is a coordinate variable and must be excluded from WMS layers"
    )
    # Must be excluded: variable whose standard_name is a coordinate name,
    # even though the variable name itself is not in the skip list
    assert "whatever" not in wms_layers, (
        "'whatever' has standard_name 'longitude' and must be excluded from WMS layers"
    )
