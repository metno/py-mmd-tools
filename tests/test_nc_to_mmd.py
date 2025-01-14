"""
License:

This file is part of the py-mmd-tools repository
<https://github.com/metno/py-mmd-tools>.

py-mmd-tools is licensed under the Apache License 2.0
<https://github.com/metno/py-mmd-tools/blob/master/LICENSE>
"""

import os
import pathlib
import tempfile
import yaml
import warnings
import unittest
import pytest
import json

import numpy as np

from dateutil.parser import isoparse
from filehash import FileHash
from lxml import etree
from netCDF4 import Dataset
from pkg_resources import resource_string
from unittest.mock import patch

from py_mmd_tools.nc_to_mmd import Nc_to_mmd, normalize_iso8601, normalize_iso8601_0
from py_mmd_tools.nc_to_mmd import valid_url
from py_mmd_tools.nc_to_mmd import get_short_and_long_names
from py_mmd_tools.nc_to_mmd import nc_wrapper
from py_mmd_tools.yaml_to_adoc import nc_attrs_from_yaml
from py_mmd_tools.yaml_to_adoc import required
from py_mmd_tools.yaml_to_adoc import repetition_allowed
from py_mmd_tools.yaml_to_adoc import set_attribute
from py_mmd_tools.yaml_to_adoc import set_attributes

from tests.test_nc2mmd_script import patchedDataset

warnings.simplefilter("ignore", ResourceWarning)


@pytest.mark.py_mmd_tools
def test_parent_keyword_arg(dataDir):
    """ Test that a parent uuid can be provided to the to_mmd
    function, and that it is verified that the uuid part of the ID is
    a UUID.
    """
    # UUID is UUID
    md = Nc_to_mmd(os.path.join(dataDir, 'reference_nc.nc'), check_only=True)
    req, msg = md.to_mmd(parent="no.met:b7cb7934-77ca-4439-812e-f560df3fe7eb")
    assert req is True

    # ID is not correctly composed
    md = Nc_to_mmd(os.path.join(dataDir, 'reference_nc.nc'), check_only=True)
    with pytest.raises(ValueError) as ve:
        req, msg = md.to_mmd(parent="not-a-uuid")
    assert str(ve.value) == "parent must be composed as <naming_authority>:<uuid>"

    # naming_authority is not valid
    md = Nc_to_mmd(os.path.join(dataDir, 'reference_nc.nc'), check_only=True)
    with pytest.raises(ValueError) as ve:
        req, msg = md.to_mmd(parent="no.kvet:not-a-uuid")
    assert str(ve.value) == "naming_authority ACDD attribute no.kvet is not valid"

    # UUID is not UUID
    md = Nc_to_mmd(os.path.join(dataDir, 'reference_nc.nc'), check_only=True)
    with pytest.raises(ValueError) as ve:
        req, msg = md.to_mmd(parent="no.met:not-a-uuid")
    assert str(ve.value) == "UUID part of the parent ID is not valid"


@pytest.mark.py_mmd_tools
def test_file_location_in_overrides(dataDir):
    """Test that over-riding the file location works as expected.
    """
    md = Nc_to_mmd(os.path.join(dataDir, "reference_nc.nc"), check_only=True)
    req, msg = md.to_mmd()
    assert md.metadata["storage_information"]["file_location"] == dataDir
    md = Nc_to_mmd(os.path.join(dataDir, "reference_nc.nc"), check_only=True)
    req, msg = md.to_mmd(overrides={"file_location": "/some/where/else"})
    assert md.metadata["storage_information"]["file_location"] == "/some/where/else"


@pytest.mark.py_mmd_tools
def test_platform_in_overrides(dataDir):
    """Test that over-riding the platform attribute works as expected.
    """
    md = Nc_to_mmd(os.path.join(dataDir, 'reference_nc.nc'), check_only=True)
    req, msg = md.to_mmd(
        overrides={
            "platform": {
                "short_name": "Metop-A",
                "long_name": "Meteorological operational satellite - A",
                "resource": "http://www.wmo-sat.info/oscar/satellites/view/metop-a",
                "orbit_relative": 3,
                "orbit_absolute": 100,
                "orbit_direction": "ascending",
                "instrument": {
                    "short_name": "AVHRR",
                    "long_name": "Advanced Very High Resolution Radiometer",
                    "resource": "https://www.wmo-sat.info/oscar/instruments/view/avhrr"}}})
    assert md.metadata["platform"][0]["short_name"] == "Metop-A"


@pytest.mark.py_mmd_tools
def test_get_landing_page_url(dataDir):
    md = Nc_to_mmd(os.path.join(dataDir, "reference_nc.nc"), check_only=True)
    assert md.get_dataset_landing_page_url() == "https://data.met.no/dataset/" \
                                                "b7cb7934-77ca-4439-812e-f560df3fe7eb"
    md = Nc_to_mmd(os.path.join(dataDir, "reference_nc_missing_keywords_vocab.nc"),
                   check_only=True)
    assert md.get_dataset_landing_page_url() == "https://data.fake.no/dummy"


@pytest.mark.py_mmd_tools
def test_license_missing(dataDir):
    """ Test that an error is raised if the license attribute is missing.
    """
    mmd_yaml = yaml.load(
        resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
    )
    # nc_to_update.nc does not have license..
    md = Nc_to_mmd(os.path.join(dataDir, "nc_to_update.nc"), check_only=True)
    md.get_license(mmd_yaml['use_constraint'], md.ncin)
    assert md.missing_attributes["errors"][0] == 'ACDD attribute "license" is required'


@pytest.mark.py_mmd_tools
def test_separate_repeated(dataDir):
    """ Test function Nc_to_mmd.separate_repeated
    """
    md = Nc_to_mmd(os.path.join(dataDir, 'reference_nc.nc'), check_only=True)
    ncin = Dataset(md.netcdf_file, "w", diskless=True)
    ncin.platform = ['&quot;Basis&quot;: &quot;Space-based Platforms&quot;',
                     ' &quot;Category&quot;: &quot;Earth Observation Satellites&quot;',
                     ' &quot;Sub_Category&quot;: &quot;Sentinel-1&quot;',
                     ' &quot;Short_Name&quot;: &quot;Sentinel-1A&quot;',
                     ' &quot;Long_Name&quot;: &quot;Sentinel-1A&quot;']
    with pytest.raises(AttributeError) as ee:
        md.separate_repeated(True, getattr(ncin, "platform"))
    assert str(ee.value) == "'list' object has no attribute 'split'"


@pytest.mark.py_mmd_tools
def testNc_to_mmd_get_geographic_extent_polygon(dataDir):
    """ Test that get_geographic_extent_polygon returns default crs if
    geospatial_bounds_crs is missing.
    """
    md = Nc_to_mmd(os.path.join(dataDir, 'reference_nc.nc'), check_only=True)
    ncin = Dataset(md.netcdf_file, "w", diskless=True)
    ncin.geospatial_bounds = ("POLYGON ((59.01 1.23, 59.06 1.66, 59.10 2.09, 59.15 2.53, "
                              "59.19 2.96, 59.24 3.40, 59.28 3.84, 59.32 4.28, 59.35 4.72, "
                              "59.39 5.16, 59.43 5.61, 59.43 5.61, 59.57 5.57, 59.72 5.52, "
                              "59.87 5.48, 60.01 5.43, 60.16 5.39, 60.31 5.34, 60.46 5.29, "
                              "60.60 5.25, 60.75 5.20, 60.92 5.15, 60.92 5.15, 60.88 4.67, "
                              "60.84 4.21, 60.80 3.75, 60.76 3.29, 60.72 2.84, 60.68 2.38, "
                              "60.63 1.92, 60.59 1.47, 60.54 1.02, 60.49 0.56, 60.49 0.56, "
                              "60.33 0.64, 60.18 0.71, 60.03 0.77, 59.89 0.84, 59.74 0.90, "
                              "59.59 0.97, 59.45 1.03, 59.30 1.10, 59.15 1.16, 59.01 1.23))")
    mmd_yaml = yaml.load(
        resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
    )
    data = md.get_geographic_extent_polygon(mmd_yaml["geographic_extent"].pop("polygon"), ncin)
    assert data["srsName"] == "EPSG:4326"


@pytest.mark.py_mmd_tools
def test_get_related_dataset(dataDir):
    """ Test get_related_dataset function.
    """
    mmd_yaml = yaml.load(
        resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
    )
    # One related dataset
    md = Nc_to_mmd(os.path.join(dataDir, 'reference_nc.nc'), check_only=True)
    ncin = Dataset(md.netcdf_file, "w", diskless=True)
    ncin.related_dataset = 'no.met:b7cb7934-77ca-4439-812e-f560df3fe7eb (parent)'
    data = md.get_related_dataset(mmd_yaml['related_dataset'], ncin)
    assert data[0]['id'] == 'no.met:b7cb7934-77ca-4439-812e-f560df3fe7eb'
    ncin.close()

    # Two related datasets
    md = Nc_to_mmd(os.path.join(dataDir, 'reference_nc.nc'), check_only=True)
    ncin = Dataset(md.netcdf_file, "w", diskless=True)
    ncin.related_dataset = (
        'no.met:b7cb7934-77ca-4439-812e-f560df3fe7eb (parent), '
        'no.met:b7cb7934-78ca-4439-812e-f560df3fe7eb (auxiliary)')
    data = md.get_related_dataset(mmd_yaml['related_dataset'], ncin)
    assert data[0]['id'] == 'no.met:b7cb7934-77ca-4439-812e-f560df3fe7eb'
    assert data[1]['id'] == 'no.met:b7cb7934-78ca-4439-812e-f560df3fe7eb'
    ncin.close()

    # Malformed relation
    md = Nc_to_mmd(os.path.join(dataDir, 'reference_nc.nc'), check_only=True)
    ncin = Dataset(md.netcdf_file, "w", diskless=True)
    ncin.related_dataset = 'no.met:b7cb7934-77ca-4439-812e-f560df3fe7eb'
    data = md.get_related_dataset(mmd_yaml['related_dataset'], ncin)
    assert 'The global attribute "related_dataset" is malformed' in \
        md.missing_attributes['errors'][0]
    ncin.close()

    # Invalid relation type
    md = Nc_to_mmd(os.path.join(dataDir, 'reference_nc.nc'), check_only=True)
    ncin = Dataset(md.netcdf_file, "w", diskless=True)
    ncin.related_dataset = 'no.met:b7cb7934-77ca-4439-812e-f560df3fe7eb (child)'
    data = md.get_related_dataset(mmd_yaml['related_dataset'], ncin)
    assert 'The dataset relation type must be either' in \
        md.missing_attributes['errors'][0]
    ncin.close()

    # Invalid identifier pattern
    md = Nc_to_mmd(os.path.join(dataDir, 'reference_nc.nc'), check_only=True)
    ncin = Dataset(md.netcdf_file, "w", diskless=True)
    ncin.related_dataset = 'b7cb7934-77ca-4439-812e-f560df3fe7eb (parent)'
    data = md.get_related_dataset(mmd_yaml['related_dataset'], ncin)
    assert 'missing naming_authority in the identifier' in \
        md.missing_attributes['errors'][0]
    ncin.close()


@pytest.mark.py_mmd_tools
def test_invalid_opendap_url(dataDir):
    """Test that a warning is issued if the opendap url is not
    accessible.
    """
    test_in = os.path.join(dataDir, 'reference_nc.nc')
    url = 'https://thredds.met.no/thredds/dodsC/reference_nc.nc'
    md = Nc_to_mmd(test_in, url, check_only=True)
    req, msg = md.to_mmd()
    assert "Cannot access OPeNDAP stream" in md.missing_attributes['warnings'][2]


@pytest.mark.py_mmd_tools
def testNc_to_mmd_Get_acdd_metadata(dataDir):
    """ Test that the if-check

    'default' in acdd_ext[acdd_ext_key].keys()

    is covered for the boolean True case.
    """
    mmd_yaml = yaml.load(
        resource_string("py_mmd_tools", "mmd_elements.yaml"), Loader=yaml.FullLoader
    )
    key = "dataset_production_status"
    test_in = os.path.join(dataDir, "reference_nc.nc")
    md = Nc_to_mmd(test_in, check_only=True)
    ncin = Dataset(test_in, "w", diskless=True)
    assert md.get_acdd_metadata(mmd_yaml[key], ncin, key) == "Complete"


@pytest.mark.py_mmd_tools
def test_checksum(monkeypatch):
    """Verify that the checksum created in nc_to_mmd.py is correct"""
    tested = tempfile.mkstemp()[1]
    fn = os.path.abspath('tests/data/reference_nc.nc')
    url = os.path.join('https://thredds.met.no/thredds/dodsC/', os.path.basename(fn))
    with monkeypatch.context() as mp:
        mp.setattr("py_mmd_tools.nc_to_mmd.Dataset",
                   lambda *args, **kwargs: patchedDataset(url, *args, **kwargs))
        md = Nc_to_mmd(fn, url, checksum_calculation=True, check_only=True)
        md.to_mmd()
    checksum = md.metadata['storage_information']['checksum']
    with open(tested, 'w') as tt:
        tt.write('%s *%s'%(checksum, fn))
    md5hasher = FileHash('md5')
    assert md5hasher.verify_checksums(tested)[0].hashes_match is True


@pytest.mark.py_mmd_tools
def test_create_mmd_1(monkeypatch):
    """Test MMD creation from a valid netcdf file, validation
    with the mmd_strict.xsd, and that some fields are as expected.
    Please add new fields to test as needed..
    """
    tested = tempfile.mkstemp()[1]
    fn = os.path.abspath('tests/data/reference_nc_with_altID_multiple.nc')
    url = 'https://thredds.met.no/thredds/dodsC/reference_nc_with_altID_multiple.nc'
    with monkeypatch.context() as mp:
        mp.setattr("py_mmd_tools.nc_to_mmd.Dataset",
                   lambda *args, **kwargs: patchedDataset(url, *args, **kwargs))
        md = Nc_to_mmd(fn, url, output_file=tested, checksum_calculation=True)
        md.to_mmd()

    reference_xsd = os.path.join(os.environ['MMD_PATH'], 'xsd/mmd_strict.xsd')
    xsd_obj = etree.XMLSchema(etree.parse(reference_xsd))
    xml_doc = etree.ElementTree(file=tested)
    valid = xsd_obj.validate(xml_doc)
    assert valid is True
    """ Check content of the xml_doc """
    # alternate_identifier
    assert xml_doc.getroot().find(
        "{http://www.met.no/schema/mmd}alternate_identifier[@type='dummy_type']"
    ).text == "dummy_id_no1"
    assert xml_doc.getroot().find(
        "{http://www.met.no/schema/mmd}alternate_identifier[@type='other_type']"
    ).text == "dummy_id_no2"
    # platform
    platform = xml_doc.getroot().find("{http://www.met.no/schema/mmd}platform")
    assert platform.getchildren()[0].text == "SNPP"
    assert platform.getchildren()[1].text == "Suomi National Polar-orbiting Partnership"


def test_create_and_validate_mmd_platform(monkeypatch):
    """ Test that an MMD file for a netcdf with missing platform
    short_name and long_name validates as long as the vocabulary
    is given."""
    tested = tempfile.mkstemp()[1]
    fn = os.path.abspath('tests/data/reference_nc_platform_names_missing.nc')
    url = 'https://thredds.met.no/thredds/dodsC/reference_nc_platform_names_missing.nc'
    with monkeypatch.context() as mp:
        mp.setattr("py_mmd_tools.nc_to_mmd.Dataset",
                   lambda *args, **kwargs: patchedDataset(url, *args, **kwargs))
        md = Nc_to_mmd(fn, url, output_file=tested, checksum_calculation=True)
        md.to_mmd()
    reference_xsd = os.path.join(os.environ['MMD_PATH'], 'xsd/mmd_strict.xsd')
    xsd_obj = etree.XMLSchema(etree.parse(reference_xsd))
    xml_doc = etree.ElementTree(file=tested)
    valid = xsd_obj.validate(xml_doc)
    assert valid is True


@pytest.mark.py_mmd_tools
def test_get_data_access_dict_with_wms(monkeypatch):
    """ToDo: Add docstring"""
    netcdf_file = os.path.abspath('tests/data/reference_nc.nc')
    opendap_url = (
        'https://thredds.met.no/thredds/dodsC/arcticdata/'
        'S2S_drift_TCD/SIDRIFT_S2S_SH/2019/07/31/'
    ) + netcdf_file
    kwargs = {
        "dataset_citation": {
            "author": "Some name to ensure that kwargs not required "
                      "by get_data_access_dict are allowed"
        },
        "add_wms_data_access": True,
    }
    with monkeypatch.context() as mp:
        mp.setattr("py_mmd_tools.nc_to_mmd.Dataset",
                   lambda *args, **kwargs: patchedDataset(opendap_url, *args, **kwargs))
        md = Nc_to_mmd(netcdf_file, opendap_url, check_only=True)
        ncin = Dataset(md.netcdf_file)
        data = md.get_data_access_dict(ncin, **kwargs)
    assert data[0]['type'] == 'OPeNDAP'
    assert data[1]['type'] == 'OGC WMS'
    assert data[2]['type'] == 'HTTP'


@pytest.mark.py_mmd_tools
def test_get_data_access_dict_with_custom_wms(monkeypatch):
    """WMS link is set."""
    netcdf_file = os.path.abspath('tests/data/reference_nc.nc')
    opendap_url = (
        'https://thredds.met.no/thredds/dodsC/arcticdata/'
        'S2S_drift_TCD/SIDRIFT_S2S_SH/2019/07/31/'
    ) + netcdf_file
    with monkeypatch.context() as mp:
        mp.setattr("py_mmd_tools.nc_to_mmd.Dataset",
                   lambda *args, **kwargs: patchedDataset(opendap_url, *args, **kwargs))
        md = Nc_to_mmd(netcdf_file, opendap_url, check_only=True)
        ncin = Dataset(md.netcdf_file)
        data = md.get_data_access_dict(ncin, add_wms_data_access=True,
                                       wms_link='http://test-link')
    assert data[1]['type'] == 'OGC WMS'
    assert 'http://test-link' in str(data[1]['resource'])
    assert data[1]['wms_layers'] == ['M01',
                                     'M01_copy']


@pytest.mark.py_mmd_tools
def test_get_data_access_dict_with_custom_wms_and_layer_names(monkeypatch):
    """WMS link and layer names are set."""
    netcdf_file = os.path.abspath('tests/data/reference_nc.nc')
    opendap_url = (
        'https://thredds.met.no/thredds/dodsC/arcticdata/'
        'S2S_drift_TCD/SIDRIFT_S2S_SH/2019/07/31/'
    ) + netcdf_file
    with monkeypatch.context() as mp:
        mp.setattr("py_mmd_tools.nc_to_mmd.Dataset",
                   lambda *args, **kwargs: patchedDataset(opendap_url, *args, **kwargs))
        md = Nc_to_mmd(netcdf_file, opendap_url, check_only=True)
        ncin = Dataset(md.netcdf_file)
        data = md.get_data_access_dict(ncin, add_wms_data_access=True,
                                       wms_link='http://test-link',
                                       wms_layer_names=['layer_name_1', 'layer_name_2'])
    assert data[1]['type'] == 'OGC WMS'
    assert 'http://test-link' in str(data[1]['resource'])
    assert data[1]['wms_layers'] == ['layer_name_1', 'layer_name_2']


@pytest.mark.py_mmd_tools
def test_get_data_access_dict(monkeypatch):
    """ToDo: Add docstring"""
    netcdf_file = os.path.abspath('tests/data/reference_nc.nc')
    opendap_url = (
        'https://thredds.met.no/thredds/dodsC/arcticdata/'
        'S2S_drift_TCD/SIDRIFT_S2S_SH/2019/07/31/'
    ) + netcdf_file
    with monkeypatch.context() as mp:
        mp.setattr("py_mmd_tools.nc_to_mmd.Dataset",
                   lambda *args, **kwargs: patchedDataset(opendap_url, *args, **kwargs))
        md = Nc_to_mmd(netcdf_file, opendap_url, check_only=True)
        ncin = Dataset(md.netcdf_file)
        data = md.get_data_access_dict(ncin)
    assert data[0]['type'] == 'OPeNDAP'
    assert data[1]['type'] == 'HTTP'


@pytest.mark.py_mmd_tools
def test_not_absolute_path():
    fn = 'tests/data/reference_nc.nc'
    md = Nc_to_mmd(fn, check_only=True)
    assert os.path.isabs(md.netcdf_file) is True


@pytest.mark.py_mmd_tools
def test_get_operational_status(dataDir, monkeypatch):
    mmd_yaml = yaml.load(
        resource_string("py_mmd_tools", "mmd_elements.yaml"), Loader=yaml.FullLoader
    )
    mmd_element = mmd_yaml["operational_status"]
    test_in = os.path.join(dataDir, "reference_nc.nc")
    md = Nc_to_mmd(test_in, check_only=True)
    ncin = Dataset(test_in, "w", diskless=True)

    # processing_level is not present
    value = md.get_operational_status(mmd_element, ncin)
    assert value == "Not available"

    # processing_level is not valid
    ncin.processing_level = "kjhhas"
    mmd_element["maxOccurs"] = "1"
    value = md.get_operational_status(mmd_element, ncin)
    assert ("The ACDD attribute 'processing_level' in MMD attribute 'operational_status'"
            in md.missing_attributes['errors'][0])

    # repetition of processing_level is allowed
    mmd_element["maxOccurs"] = "unbounded"
    with pytest.raises(ValueError) as ve:
        value = md.get_operational_status(mmd_element, ncin)
    assert str(ve.value) == "This is not expected..."


@pytest.mark.py_mmd_tools
def test_dataset_production_status(dataDir):
    mmd_yaml = yaml.load(
        resource_string("py_mmd_tools", "mmd_elements.yaml"), Loader=yaml.FullLoader
    )
    mmd_element = mmd_yaml["dataset_production_status"]
    test_in = os.path.join(dataDir, "reference_nc.nc")
    md = Nc_to_mmd(test_in, check_only=True)
    ncin = Dataset(test_in, "w", diskless=True)

    # dataset_production_status is not present
    value = md.get_dataset_production_status(mmd_element, ncin)
    assert value == "Complete"

    # dataset_production_status is not valid
    ncin.dataset_production_status = "kjhhas"
    mmd_element["maxOccurs"] = "1"
    value = md.get_dataset_production_status(mmd_element, ncin)
    assert "The ACDD attribute 'dataset_production_status'"
    "must " in md.missing_attributes['errors'][0]

    # repetition of processing_level is allowed
    mmd_element["maxOccurs"] = "unbounded"
    with pytest.raises(ValueError) as ve:
        value = md.get_dataset_production_status(mmd_element, ncin)
    assert str(ve.value) == "This is not expected..."


@pytest.mark.py_mmd_tools
def test_get_quality_control(dataDir):
    mmd_yaml = yaml.load(
        resource_string("py_mmd_tools", "mmd_elements.yaml"), Loader=yaml.FullLoader
    )
    mmd_element = mmd_yaml["quality_control"]
    test_in = os.path.join(dataDir, "reference_nc.nc")
    md = Nc_to_mmd(test_in, check_only=True)
    ncin = Dataset(test_in, "w", diskless=True)

    # processing_level is not valid
    ncin.quality_control = "kjhhas"
    mmd_element["maxOccurs"] = "1"
    md.get_quality_control(mmd_element, ncin)
    assert "The ACDD attribute 'quality_control' must " in md.missing_attributes['errors'][0]

    # repetition of processing_level is allowed
    mmd_element["maxOccurs"] = "unbounded"
    with pytest.raises(ValueError) as ve:
        md.get_quality_control(mmd_element, ncin)
    assert str(ve.value) == "This is not expected..."


@pytest.mark.py_mmd_tools
def test_nc_wrapper_global_attrs(dataDir):

    test_ncin = os.path.join(dataDir, "reference_nc.nc")
    test_ncin = Dataset(test_ncin)

    test_json_header = os.path.join(dataDir, "reference_nc_header.json")

    with open(test_json_header, "r") as file:
        test_json_header = nc_wrapper(json.load(file))

    for attr in test_ncin.ncattrs():
        assert test_ncin.getncattr(attr) == test_json_header.getncattr(attr), \
            (f"Divergence in global attribute between header and nc header at {attr},"
             f" nc: {test_ncin.getncattr(attr)}, json: {test_json_header.getncattr(attr)}")
    for attr in test_ncin.ncattrs():
        assert test_ncin.getncattr(attr) == test_json_header[attr], \
            (f"Divergence in global attribute between header and nc header at {attr},"
             f" nc: {test_ncin.getncattr(attr)}, json: {test_json_header[attr]}")


@pytest.mark.py_mmd_tools
def test_nc_wrapper_variable_attrs(dataDir):

    test_ncin = os.path.join(dataDir, "reference_nc.nc")
    test_ncin = Dataset(test_ncin)

    test_json_header = os.path.join(dataDir, "reference_nc_header.json")

    with open(test_json_header, "r") as file:
        test_json_header = nc_wrapper(json.load(file))

    def handle_type_comparison(a, b):
        if isinstance(a, (np.floating, float)) or isinstance(b, (np.floating, float)):
            if np.isnan(a) and np.isnan(b):
                return True
            else:
                return np.abs(a-b) < 1e-8

        if isinstance(a, (np.ndarray, list)) and isinstance(b, (np.ndarray, list)):
            return (a == b).all()

        return a == b

    for var, var_attrs in test_ncin.variables.items():
        for attr in var_attrs.ncattrs():
            assert handle_type_comparison(var_attrs.getncattr(attr),
                                          test_json_header.variables[var].getncattr(attr)), \
                (f"Divergence in variable attribute between json and nc header at {var}:{attr},"
                 f" nc: {var_attrs.getncattr(attr)} of type {type(var_attrs.getncattr(attr))},"
                 f"json: {test_json_header.variables[var].getncattr(attr)}"
                 f" of type {type(test_json_header.variables[var].getncattr(attr))}")

    for var, var_attrs in test_ncin.variables.items():
        for attr in var_attrs.ncattrs():
            assert handle_type_comparison(var_attrs.getncattr(attr),
                                          test_json_header.variables[var][attr]), \
                (f"Divergence in variable attribute between json and nc header at {var}:{attr},"
                 f" nc: {var_attrs.getncattr(attr)} of type {type(var_attrs.getncattr(attr))},"
                 f"json: {test_json_header.variables[var][attr]}"
                 f" of type {type(test_json_header.variables[var][attr])}")


@pytest.mark.py_mmd_tools
def test_json(dataDir, monkeypatch):
    """TODO: add docstring
    """
    test_json_header = os.path.join(dataDir, "reference_nc_header.json")

    with open(test_json_header, "r") as file:
        test_json_header = json.load(file)

    tmp = Nc_to_mmd(test_json_header, json_input=True, check_only=True, checksum_calculation=True)
    tmp.to_mmd()

    with monkeypatch.context() as mp:
        mp.setattr(nc_wrapper, "__init__", lambda *a, **k: None)
        mp.setattr(nc_wrapper, "ncattrs", lambda *a, **k: ["what", "ever"])
        mp.setattr(nc_wrapper, "getncattr", lambda *a, **k: ["what", "ever"])
        test_json_header.pop("file_size")
        with pytest.raises(KeyError) as ee:
            tmp = Nc_to_mmd(test_json_header, json_input=True,
                            opendap_url="https://thredds.met.no/etc", output_file="somefn.xml")
        assert "'file_size'" == str(ee.value)

    test_json_header.pop("archive_location")
    with pytest.raises(KeyError) as ee:
        tmp = Nc_to_mmd(test_json_header, json_input=True,
                        opendap_url="https://thredds.met.no/etc", output_file="somefn.xml")
    assert "'archive_location'" in str(ee.value)


# The target_nc_filename should not be needed if the file is correctly
# placed before creating the MMD file. With
# https://github.com/metno/discovery-metadata-catalog-ingestor/issues/225
# we can let the MMD files validate but not be inserted unless the
# nc-file and the odap url exist.
# @pytest.mark.py_mmd_tools
# def testNc_to_mmd_Init(dataDir):
#     """Test __init__
#
#     1: that the target_nc_filename is added, if provided.
#
#     Additional tests for the init method can be added here.
#     """
#     # Test case with target_nc_filename different from input filename
#     md = Nc_to_mmd(os.path.join(dataDir, 'reference_nc.nc'),
#                    target_nc_filename="/dummy/path/to/filename.nc",
#                    opendap_url="https://thredds.met.no/etc",
#                    output_file="somefn.xml")
#     assert md.target_nc_filename == "/dummy/path/to/filename.nc"


@pytest.mark.py_mmd_tools
def test_nc_wrapper_ncatters(dataDir):
    test_ncin = os.path.join(dataDir, "reference_nc.nc")
    test_ncin = Dataset(test_ncin)

    test_json_header = os.path.join(dataDir, "reference_nc_header.json")

    with open(test_json_header, "r") as file:
        test_json_header = nc_wrapper(json.load(file))

    assert test_json_header.ncattrs() == test_ncin.ncattrs(), \
        "Keys in global ncattrs does not match between json and nc."

    for var in test_ncin.variables:
        assert test_ncin.variables[var].ncattrs() == test_json_header.variables[var].ncattrs(), \
            f"Mismatch in variable attributes, for variable {var}"


@pytest.mark.py_mmd_tools
def test_attribute_error_title_json(dataDir):
    test_json_header = os.path.join(dataDir, "reference_nc_header_missing_title.json")

    with open(test_json_header, "r") as file:
        test_json_header = json.load(file)

    tmp = Nc_to_mmd(test_json_header, json_input=True, check_only=True)
    with pytest.raises(AttributeError):
        tmp.to_mmd()


@pytest.mark.py_mmd_tools
def test_get_CFSTDN_keywords(dataDir):
    """ Test that get_CFSTDN_keywords returns a list with one CF
    standard name from the test file.
    """
    md = Nc_to_mmd(os.path.join(dataDir, 'reference_nc.nc'), check_only=True)
    vars = md.get_CFSTDN_keywords(md.ncin)
    assert len(vars) == 1
    assert vars[0] == "toa_bidirectional_reflectance"


class TestNCAttrsFromYaml(unittest.TestCase):

    def setUp(self):
        """ Sets up class with an attribute `mmd_yaml` containing
        the MMD to ACDD translations.
        """
        self.maxDiff = None
        self.mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        self.attributes = {}
        self.attributes['acdd'] = {}
        self.attributes['acdd']['required'] = []
        self.attributes['acdd']['not_required'] = []
        self.attributes['acdd_ext'] = {}
        self.attributes['acdd_ext']['required'] = []
        self.attributes['acdd_ext']['not_required'] = []

    def test_set_attribute__wrong_input(self):
        """ Test that errors are raised in case of wrong input to the
        set_attribute method.
        """
        mmd_field = 'keywords'
        key = 'maxOccurs'
        val = self.mmd_yaml[mmd_field][key]
        convention = 'acdd'
        with self.assertRaises(ValueError):
            set_attribute(mmd_field, val, convention, self.attributes, req='not_required')

    def test_set_attribute__no_convention(self):
        """ Test the set_attribute method when no convention is
        defined in mmd_yaml.
        """
        mmd_field = 'alternate_identifier'
        val = self.mmd_yaml[mmd_field]
        convention = 'acdd'
        set_attribute(mmd_field, val, convention, self.attributes, req='not_required')
        self.assertFalse(bool(self.attributes['acdd']['not_required']))

    def test_set_attribute__one_conv_field(self):
        """ Test the set_attribute method when one convention field
        is provided in mmd_yaml. Tests both acdd and acdd_ext.
        """
        # Test acdd_ext
        mmd_field = 'dataset_production_status'
        val = self.mmd_yaml[mmd_field]
        convention = 'acdd_ext'
        set_attribute(mmd_field, val, convention, self.attributes, req='not_required')
        self.assertEqual(self.attributes['acdd_ext']['not_required'][0], {
            'attribute': 'dataset_production_status',
            'comment': 'No repetition allowed.',
            'default': 'Complete',
            'description':
                'Production status for the dataset, using a controlled '
                'vocabulary. The valid keywords are listed in '
                'https://htmlpreview.github.io/?https://github.com/metno/mmd/blob/'
                'master/doc/mmd-specification.html#dataset-production-status-types[section '
                '4.2 of the MMD specification]. If set as "In Work", remember '
                'that end_date in '
                'https://htmlpreview.github.io/?https://github.com/metno/mmd/blob/'
                'master/doc/mmd-specification.html#temporal_extent[section '
                '2.8 of the MMD specification] can (should) be empty.',
            'mmd_field': 'dataset_production_status',
            'recommended': True,
            'repetition_allowed': False,
            'separator': '',
        })
        # Test acdd
        mmd_field = 'operational_status'
        val = self.mmd_yaml[mmd_field]
        convention = 'acdd'
        set_attribute(mmd_field, val, convention, self.attributes, req='not_required')
        self.assertEqual(self.attributes['acdd']['not_required'][0], {
            'attribute': 'processing_level',
            'comment': 'Optional',
            'default': '',
            'description':
                'A textual description of the processing '
                'level of the data. Valid keywords are listed in '
                'https://htmlpreview.github.io/?https://github.com/metno/mmd/blob/'
                'master/doc/mmd-specification.html#operational-status[Section '
                '4.5 of the MMD specification].',
            'mmd_field': 'operational_status',
            'recommended': True,
            'repetition_allowed': False,
            'separator': '',
        })

    def test_set_attribute__two_conv_fields(self):
        """ Test the set_attribute method when two convention fields
        are provided in mmd_yaml.
        """
        mmd_field = 'metadata_identifier'
        val = self.mmd_yaml[mmd_field]
        convention = 'acdd'
        set_attribute(mmd_field, val, convention, self.attributes, req='required')
        self.assertEqual(self.attributes['acdd']['required'][0], {
            'attribute': 'id',
            'comment': 'Required, and should be UUID. No repetition allowed.',
            'default': '',
            'description':
                'An identifier for the dataset, provided by and unique within '
                'its naming authority. The combination of the "naming '
                'authority" and the "id" should be globally unique, but the id '
                'can be globally unique by itself also. A uuid is recommended.',
            'mmd_field': 'metadata_identifier',
            'recommended': True,
            'repetition_allowed': False,
            'separator': '',
        })
        self.assertEqual(self.attributes['acdd']['required'][1], {
            'attribute': 'naming_authority',
            'comment': 'Required. We recommend using reverse-DNS naming. '
                       'No repetition allowed.',
            'default': '',
            'description':
                'The organisation that provides the initial id (see above) for '
                'the dataset. The naming authority should be uniquely '
                'specified by this attribute. We recommend using reverse-DNS '
                'naming for the naming authority.',
            'mmd_field': 'metadata_identifier',
            'recommended': True,
            'repetition_allowed': False,
            'separator': '',
        })

    def test_set_attribute__required_not_req(self):
        """ Test the set_attribute method when the
        attributes[convention]['required'] field should be
        populated but the convention is not required.
        """
        mmd_field = 'operational_status'
        val = self.mmd_yaml[mmd_field]
        convention = 'acdd'
        set_attribute(mmd_field, val, convention, self.attributes, req='required')
        self.assertEqual(self.attributes['acdd']['required'], [])
        self.assertEqual(self.attributes['acdd']['not_required'], [])

    def test_set_attribute__not_required_req(self):
        """ Test the set_attribute method when the
        attributes[convention]['not_required'] field should be
        populated but the convention is required.
        """
        mmd_field = 'iso_topic_category'
        val = self.mmd_yaml[mmd_field]
        convention = 'acdd_ext'
        set_attribute(mmd_field, val, convention, self.attributes, req='not_required')
        self.assertEqual(self.attributes['acdd']['required'], [])
        self.assertEqual(self.attributes['acdd']['not_required'], [])

    def test_set_attributes__single(self):
        mmd_field = 'metadata_identifier'
        val = self.mmd_yaml[mmd_field]
        set_attributes(mmd_field, val, self.attributes)
        self.assertEqual(self.attributes['acdd']['required'][0], {
            'attribute': 'id',
            'comment': 'Required, and should be UUID. No repetition allowed.',
            'default': '',
            'description':
                'An identifier for the dataset, provided by and unique within '
                'its naming authority. The combination of the "naming '
                'authority" and the "id" should be globally unique, but the id '
                'can be globally unique by itself also. A uuid is recommended.',
            'mmd_field': 'metadata_identifier',
            'recommended': True,
            'repetition_allowed': False,
            'separator': '',
        })

    def test_set_attributes__nested(self):
        mmd_field = 'keywords'
        val = self.mmd_yaml[mmd_field]
        set_attributes(mmd_field, val, self.attributes)
        self.assertEqual(self.attributes['acdd']['required'][0], {
            'attribute': 'keywords',
            'comment': 'Comma separated list.',
            'default': '',
            'description':
                'A comma-separated list of keywords and/or '
                'phrases. Keywords may be common words or phrases, '
                'terms from a controlled vocabulary (GCMD is '
                'required), or URIs for terms from a controlled '
                'vocabulary (see also "keywords_vocabulary" '
                'attribute). If keywords are extracted from, e.g., '
                'GCMD Science Keywords, add '
                'keywords_vocabulary="GCMDSK" and prefix in any case '
                'each keyword with the appropriate prefix.',
            'mmd_field': 'keywords>keyword',
            'recommended': True,
            'repetition_allowed': True,
            'separator': ',',
        })

    def test_required__is_required(self):
        """ Test method required on a required MMD field.
        """
        self.assertTrue(required(self.mmd_yaml['temporal_extent']['start_date']))

    def test_required__not_required(self):
        """ Test method required on a not required MMD field.
        """
        self.assertFalse(required(self.mmd_yaml['temporal_extent']['end_date']))

    def test_required__minOccurs_missing(self):
        """ Test method required on an MMD field where the minOccurs
        key is missing.
        """
        sd = self.mmd_yaml['temporal_extent']['start_date']
        sd.pop('minOccurs')
        self.assertFalse(required(sd))

    def test_repetition_allowed(self):
        """ Test method repetition_allowed with an MMD field which
        can allows repetition.
        """
        self.assertTrue(repetition_allowed(self.mmd_yaml['temporal_extent']['start_date']))

    def test_repetition_allowed__not_allowed(self):
        """ Test method repetition_allowed with an MMD field which
        can does not allow repetition.
        """
        self.assertFalse(repetition_allowed(self.mmd_yaml['geographic_extent']))

    def test_repetition_allowed__maxOccurs_missing(self):
        """ Test method repetition_allowed with an MMD field where
        the maxOccurs key is missing.
        """
        sd = self.mmd_yaml['temporal_extent']['start_date']
        sd.pop('maxOccurs')
        self.assertTrue(repetition_allowed(sd))

    def test_nc_attrs_from_yaml(self):
        """ToDo: Add docstring"""
        adoc = nc_attrs_from_yaml()
        self.assertEqual(type(adoc), str)

    def test_creator_role_acdd_extension(self):
        mmd_field = 'personnel'
        val = self.mmd_yaml[mmd_field]
        set_attributes(mmd_field, val, self.attributes)
        self.assertEqual(self.attributes['acdd_ext']['not_required'][0]['attribute'],
                         'creator_role')


class TestNC2MMD(unittest.TestCase):

    def setUp(self):
        """ToDo: Add docstring"""
        #
        # run this test from the root directory by running:
        #
        # python3 -m unittest
        #
        # unset the output limit when printing the xml diff
        #
        current_dir = pathlib.Path.cwd()
        self.reference_nc = str(current_dir / 'tests' / 'data' / 'reference_nc.nc')
        self.fail_nc = str(current_dir / 'tests' / 'data' / 'reference_nc_fail.nc')
        self.reference_xml = str(current_dir / 'tests' / 'data' / 'reference_nc.xml')
        self.reference_xsd = os.path.join(os.environ['MMD_PATH'], 'xsd/mmd_strict.xsd')

    # @patch('py_mmd_utils.nc_to_mmd.Nc_to_mmd.__init__')
    # @patch('mmd_utils.nc_to_mmd.Nc_to_mmd.to_mmd')
    # def test__main_with_defaults(self, mock_to_mmd, mock_init):
    #     mock_init.return_value = None
    #     self.assertTrue(mock_init.called)
    #     self.assertTrue(mock_to_mmd.called)

    def test_valid_url(self):
        self.assertTrue(valid_url('http://www.google.com'))
        self.assertTrue(valid_url('http://spdx.org/licenses/CC-BY-4.0'))
        self.assertFalse(valid_url('www.google.com'))
        self.assertFalse(valid_url(None))

    def test_license__deprecated_attrs(self):
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(self.reference_nc, check_only=True)
        ncin = Dataset(md.netcdf_file, "w", diskless=True)
        ncin.license = "CC-BY-4.0"
        ncin.license_resource = "http://spdx.org/licenses/CC-BY-4.0"
        value = md.get_license(mmd_yaml['use_constraint'], ncin)
        self.assertEqual(value['resource'], 'http://spdx.org/licenses/CC-BY-4.0')
        self.assertEqual(value['identifier'], 'CC-BY-4.0')
        self.assertEqual(
            md.missing_attributes["warnings"][0],
            '"license_resource" is a deprecated attribute')

    def test_license__invalid_url(self):
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(self.reference_nc, check_only=True)
        ncin = Dataset(md.netcdf_file, "w", diskless=True)
        ncin.license = "spdx.org/licenses/CC-BY-4.0"
        value = md.get_license(mmd_yaml['use_constraint'], ncin)
        self.assertIsNone(value)
        self.assertEqual(
            md.missing_attributes["errors"][0],
            '"spdx.org/licenses/CC-BY-4.0" is not a valid url'
        )

    def test_license__basic(self):
        """Test that a valid full license with both url and
        identifier is accepted and parsed correctly.
        """
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(self.reference_nc, check_only=True)
        ncin = Dataset(md.netcdf_file, "w", diskless=True)
        ncin.license = "http://spdx.org/licenses/CC-BY-4.0 (CC-BY-4.0)"
        value = md.get_license(mmd_yaml['use_constraint'], ncin)
        self.assertEqual(value['resource'], 'http://spdx.org/licenses/CC-BY-4.0')
        self.assertEqual(value['identifier'], 'CC-BY-4.0')

    def test_license__simple(self):
        """Test that a license with valid url only is accepted and parsed correctly.
        """
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(self.reference_nc, check_only=True)
        ncin = Dataset(md.netcdf_file, "w", diskless=True)
        ncin.license = "http://spdx.org/licenses/CC-BY-4.0"
        value = md.get_license(mmd_yaml['use_constraint'], ncin)
        # met-vocab-tools should be able to find the license by
        # searching a url (see issue https://github.com/metno/met-vocab-tools/issues/25):
        # self.assertEqual(value['identifier'], 'CC-BY-4.0')
        self.assertEqual(value['resource'], 'http://spdx.org/licenses/CC-BY-4.0')
        self.assertEqual(len(list(value.keys())), 2)

    def test_license__only_url_but_not_standard(self):
        """Test that a license with a valid url to an unstandard
        license causes an error.
        """
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(self.reference_nc, check_only=True)
        ncin = Dataset(md.netcdf_file, "w", diskless=True)
        ncin.license = "http://spdx.org/licenses/CC-BY-4.1"
        value = md.get_license(mmd_yaml['use_constraint'], ncin)
        # met-vocab-tools should be able to find the license by
        # searching a url (see issue https://github.com/metno/met-vocab-tools/issues/25):
        # self.assertEqual(value['identifier'], 'CC-BY-4.0')
        self.assertEqual(value['resource'], 'http://spdx.org/licenses/CC-BY-4.1')
        self.assertEqual(len(list(value.keys())), 1)
        self.assertEqual(md.missing_attributes['errors'][0],
                         'license should be provided as <url> (<Identifier>)')

    def test_license__according_to_adc1(self):
        """Test that a license passed as url(identifier) is accepted and parsed correctly.
        """
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(self.reference_nc, check_only=True)
        ncin = Dataset(md.netcdf_file, "w", diskless=True)
        ncin.license = "http://spdx.org/licenses/CC-BY-4.0(CC-BY-4.0)"
        value = md.get_license(mmd_yaml['use_constraint'], ncin)
        self.assertEqual(value['resource'], 'http://spdx.org/licenses/CC-BY-4.0')
        self.assertEqual(value['identifier'], 'CC-BY-4.0')

    def test_license__according_to_adc2(self):
        """Test that a license passed as url (identifier) is accepted and parsed correctly.
        """
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(self.reference_nc, check_only=True)
        ncin = Dataset(md.netcdf_file, "w", diskless=True)
        ncin.license = "http://spdx.org/licenses/CC-BY-4.0 (CC-BY-4.0)"
        value = md.get_license(mmd_yaml['use_constraint'], ncin)
        self.assertEqual(value['resource'], 'http://spdx.org/licenses/CC-BY-4.0')
        self.assertEqual(value['identifier'], 'CC-BY-4.0')

    def test_license__not_standard(self):
        """ Test that a license string that is not standard is added
        as license_text.
        """
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(self.reference_nc, check_only=True)
        ncin = Dataset(md.netcdf_file, "w", diskless=True)
        ncin.license = "https://earth.esa.int/eogateway/documents/20142/1564626/" \
                       "ESA-Data-Policy-ESA-PB-EO-2010-54.pdf (ESA earth observation data policy)"
        value = md.get_license(mmd_yaml['use_constraint'], ncin)
        self.assertEqual(
            value['license_text'],
            "https://earth.esa.int/eogateway/documents/20142/1564626/"
            "ESA-Data-Policy-ESA-PB-EO-2010-54.pdf (ESA earth observation data policy)")

    def test_init_raises_error(self):
        """Nc_to_mmd.__init__ should raise error if check_only=False,
        but output_file is None. Test that this is the case.
        """
        with self.assertRaises(ValueError):
            Nc_to_mmd(os.path.abspath('tests/data/reference_nc.nc'), output_file=None,
                      check_only=False)

    @patch('metvocab.mmdgroup.MMDGroup.init_vocab')
    def test_init_raises_error_on_mmd_group(self, mock_init_vocab):
        """Nc_to_mmd.__init__ should raise error if mmdgroups are not
        initialised.
        """
        with self.assertRaises(ValueError):
            Nc_to_mmd(os.path.abspath('tests/data/reference_nc.nc'), output_file=None,
                      check_only=True)

    def test_default_when_no_acdd_or_acdd_ext(self):
        """ Test that a default value can be used even if no acdd
        or acdd_ext fields are present.
        """
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc.nc'), check_only=True)
        ncin = Dataset(md.netcdf_file)
        value = md.get_acdd_metadata(
            mmd_yaml['metadata_status'],
            ncin, 'metadata_status'
        )
        self.assertEqual(value, 'Active')

    def test__get_acdd_metadata__dont_accept_alternatives(self):
        """ Test that the function get_acdd_metadata raises an
        error if there are several alternative acdd or acdd_ext
        fields.
        """
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc.nc'), check_only=True)
        ncin = Dataset(md.netcdf_file)
        with self.assertRaises(ValueError) as e:
            md.get_acdd_metadata(
                mmd_yaml['metadata_identifier'],
                ncin, 'metadata_identifier'
            )
        self.assertEqual(str(e.exception),
                         'Multiple ACDD or ACCD extension fields provided.'
                         ' Please use another translation function.')

    def test_get_acdd_metadata_uses_default_date_created_type(self):
        """Test that the get_acdd_metadata function uses default
        date_created_type."""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc.nc'), check_only=True)
        ncin = Dataset(md.netcdf_file)
        value = md.get_metadata_updates(mmd_yaml['last_metadata_update'], ncin)
        self.assertEqual(value['update'][0]['type'], 'Created')

    def test_polygon_is_not_wkt(self):
        """The geospatial_bounds nc attribute may not be a proper wkt string.
        Test that this case is properly handled.
        """
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(self.fail_nc, check_only=True)
        ncin = Dataset(md.netcdf_file, "w", diskless=True)
        ncin.geospatial_bounds = ""
        md.get_geographic_extent_polygon(
            mmd_yaml['geographic_extent']['polygon'], ncin
        )
        self.assertEqual(
            md.missing_attributes["errors"][0],
            "geospatial_bounds must be formatted as a WKT string"
        )

    def test_geographic_extent_polygon(self):
        """ToDo: Add docstring"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc.nc'), check_only=True)
        ncin = Dataset(md.netcdf_file)
        value = md.get_geographic_extent_polygon(
            mmd_yaml['geographic_extent']['polygon'], ncin
        )
        self.assertEqual(value['srsName'], 'EPSG:4326')
        self.assertEqual(value['pos'][0], '69.0000 3.7900')

    def test_missing_nc_attrs(self):
        """ToDo: Add docstring"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc_missing_attrs.nc'),
                       check_only=True)
        ncin = Dataset(md.netcdf_file)
        value = md.get_acdd_metadata(mmd_yaml['geographic_extent'], ncin, 'geographic_extent')
        self.assertEqual(value['rectangle']['north'], None)
        value = md.get_data_centers(mmd_yaml['data_center'], ncin)
        self.assertEqual(
            md.missing_attributes['errors'][0], 'geospatial_lat_max is a required attribute'
        )
        self.assertEqual(
            md.missing_attributes['errors'][4], 'institution is a required attribute'
        )

    def test_geographic_extent_rectangle_is_floatable(self):
        """ Test that the provided geospatial coordinates can be
        converted to float.
        """
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc.nc'), check_only=True)
        ncin = Dataset(md.netcdf_file, "w", diskless=True)
        ncin.geospatial_lat_max = "60.158733f; // float"
        ncin.geospatial_lat_min = "59.78492f; // float"
        ncin.geospatial_lon_max = "10.944986f; // float"
        ncin.geospatial_lon_min = "10.508897f; // float"
        md.get_geographic_extent_rectangle(
            mmd_yaml['geographic_extent']['rectangle'], ncin)
        self.assertEqual(
            md.missing_attributes['errors'][0],
            'geospatial_lat_max must be convertible to float type.')

    def test_missing_geographic_extent_but_provided_as_kwarg(self):
        """Test that the geographic extent rectangle can be added
        as a kwarg.
        """
        yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc_missing_rectangle.nc'),
                       check_only=True)
        md.to_mmd(overrides={
            "geographic_extent_rectangle": {"geospatial_lat_max": 90,
                                            "geospatial_lat_min": -90,
                                            "geospatial_lon_min": -180,
                                            "geospatial_lon_max": 180}})
        self.assertEqual(md.metadata['geographic_extent']['rectangle']['north'], 90)

    def test_collection_is_not_list(self):
        """Test that an error is raised if the collection input
        parameter is wrong type.
        """
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc_missing_attrs.nc'),
                       check_only=True)
        with self.assertRaises(ValueError) as e:
            md.to_mmd(collection=2)
        self.assertEqual(str(e.exception), 'collection must be of type str')

    def test_collection_not_set(self):
        """ToDo: Add docstring"""
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc_missing_collection.nc'),
                       check_only=True)
        req_ok, msg = md.to_mmd()
        self.assertTrue(req_ok)
        self.assertEqual(md.metadata['collection'], ['METNCS'])

    def test_collection_set(self):
        """ToDo: Add docstring"""
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc.nc'), check_only=True)
        status, msg = md.to_mmd(collection='ADC')
        # nc files should normally not have a collection element, as this is
        # set during harvesting
        self.assertTrue(status)
        self.assertEqual(md.metadata['collection'], ['ADC'])

    def test_abstract(self):
        """ToDo: Add docstring"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc.nc'), check_only=True)
        ncin = Dataset(md.netcdf_file)
        value = md.get_abstracts(mmd_yaml['abstract'], ncin)
        self.assertEqual(type(value), list)
        self.assertTrue('lang' in value[0].keys())
        self.assertTrue('abstract' in value[0].keys())

    def test_title(self):
        """ToDo: Add docstring"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc.nc'), check_only=True)
        ncin = Dataset(md.netcdf_file)
        value = md.get_titles(mmd_yaml['title'], ncin)
        self.assertEqual(type(value), list)
        self.assertTrue('lang' in value[0].keys())
        self.assertTrue('title' in value[0].keys())
        self.assertEqual(
            value[0]['title'],
            'Direct Broadcast data processed in satellite swath to L1C.'
        )
        self.assertEqual(value[1]['title'], 'Norsk tittel')

    def test_title_one_language_only(self):
        """ToDo: Add docstring"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc_id_missing.nc'), check_only=True)
        ncin = Dataset(md.netcdf_file)
        value = md.get_titles(mmd_yaml['title'], ncin)
        self.assertEqual(type(value), list)
        self.assertTrue('lang' in value[0].keys())
        self.assertTrue('title' in value[0].keys())
        self.assertEqual(
            md.missing_attributes['errors'][0],
            "title_no is a required attribute")

    def test_data_center(self):
        """Test get_data_centers function"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc.nc'), check_only=True)
        ncin = Dataset(md.netcdf_file)
        value = md.get_data_centers(mmd_yaml['data_center'], ncin)
        self.assertEqual(type(value), list)
        self.assertEqual(value, [{
            'data_center_name': {
                'long_name': 'Norwegian Meteorological Institute',
                'short_name': 'MET Norway'
            },
            'data_center_url': 'met.no',
        }])

    def test_data_access(self):
        """ToDo: Add docstring"""
        yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader)
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc.nc'), check_only=True)
        Dataset(md.netcdf_file)
        value = None
        self.assertEqual(value, None)

    def test_dataset_production_status(self):
        """ToDo: Add docstring"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc.nc'), check_only=True)
        ncin = Dataset(md.netcdf_file)
        value = md.get_acdd_metadata(
            mmd_yaml['dataset_production_status'], ncin, 'dataset_production_status'
        )
        self.assertEqual(value, 'In Work')

    def test_alternate_identifier_missing(self):
        """Test that get_alternate_identifier returns an empty list
        when alternate_identifier is no present in the global
        attributes of the nc-file.
        """
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc.nc'), check_only=True)
        ncin = Dataset(md.netcdf_file)
        value = md.get_alternate_identifier(mmd_yaml['alternate_identifier'], ncin)
        self.assertEqual(len(value), 0)

    def test_alternate_identifier_wrong_format(self):
        """Test that an error is raised when the alternate_identifier
        is missing the type between parentheses.
        """
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc_with_altID.nc'), check_only=True)
        ncin = Dataset(md.netcdf_file, "w", diskless=True)
        ncin.alternate_identifier = 'wrong format, missing type'
        value = md.get_alternate_identifier(
            mmd_yaml['alternate_identifier'], ncin
        )
        print(value)
        self.assertEqual(
            md.missing_attributes['errors'][0],
            'alternate_identifier must be formed as <url> (<type>).'
        )

    def test_alternate_identifier(self):
        """Test that MMD alternate_identifier is equal to the one
        provided in the nc-file.
        """
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc_with_altID.nc'), check_only=True)
        ncin = Dataset(md.netcdf_file)
        value = md.get_alternate_identifier(
            mmd_yaml['alternate_identifier'], ncin
        )
        self.assertEqual(value[0]['alternate_identifier'], 'dummy_id_no1')
        self.assertEqual(value[0]['alternate_identifier_type'], 'dummy_type')

    def test_alternate_identifier_multiple(self):
        """Test that MMD alternate_identifier is equal to the ones
        provided in the nc-file.
        """
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc_with_altID_multiple.nc'),
                       check_only=True)
        ncin = Dataset(md.netcdf_file)
        value = md.get_alternate_identifier(
            mmd_yaml['alternate_identifier'], ncin
        )
        self.assertEqual(value[0]['alternate_identifier'], 'dummy_id_no1')
        self.assertEqual(value[0]['alternate_identifier_type'], 'dummy_type')
        self.assertEqual(value[1]['alternate_identifier_type'], 'other_type')

    def test_metadata_status_is_active(self):
        """ToDo: Add docstring"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc.nc'), check_only=True)
        ncin = Dataset(md.netcdf_file)
        value = md.get_acdd_metadata(mmd_yaml['metadata_status'], ncin, 'metadata_status')
        self.assertEqual(value, 'Active')

    def test_last_metadata_update(self):
        """ToDo: Add docstring"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc.nc'), check_only=True)
        ncin = Dataset(md.netcdf_file)
        value = md.get_metadata_updates(mmd_yaml['last_metadata_update'], ncin)
        self.assertEqual(value['update'][0]['datetime'], '2020-11-27T14:05:56Z')

    def test_use_defaults_for_personnel(self):
        """ToDo: Add docstring"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(
            os.path.abspath(os.path.abspath('tests/data/reference_nc_missing_attrs.nc')),
            check_only=True)
        ncin = Dataset(md.netcdf_file)
        value = md.get_personnel(mmd_yaml['personnel'], ncin)
        self.assertEqual(value[0]['role'], 'Investigator')
        self.assertEqual(value[0]['name'], 'Not available')
        self.assertEqual(value[0]['email'], 'Not available')
        self.assertEqual(value[0]['organisation'], 'Not available')

    def test_missing_temporal_extent(self):
        """ToDo: Add docstring"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc_missing_attrs.nc'),
                       check_only=True)
        ncin = Dataset(md.netcdf_file)
        value = md.get_temporal_extents(mmd_yaml['temporal_extent'], ncin)
        self.assertEqual(value, [])
        self.assertEqual(
            md.missing_attributes['errors'][0],
            'time_coverage_start is a required ACDD attribute'
        )

    def test_missing_temporal_extent_but_start_provided_in_dict(self):
        """ToDo: Add docstring"""
        yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc_missing_attrs.nc'),
                       check_only=True)
        with self.assertRaises(AttributeError):
            md.to_mmd(overrides={"time_coverage_start": "1850-01-01T00:00:00Z"})
        self.assertEqual(md.metadata['temporal_extent']['start_date'],
                         '1850-01-01T00:00:00Z')

    def test_missing_temporal_extent_but_start_and_end_provided_in_dict(self):
        """ToDo: Add docstring"""
        yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader)
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc_missing_attrs.nc'),
                       check_only=True)
        with self.assertRaises(AttributeError):
            md.to_mmd(overrides={"time_coverage_start": "1850-01-01T00:00:00Z",
                                 "time_coverage_end": "1950-01-01T00:00:00Z"})
        self.assertEqual(md.metadata['temporal_extent']['start_date'],
                         '1850-01-01T00:00:00Z')
        self.assertEqual(md.metadata['temporal_extent']['end_date'], '1950-01-01T00:00:00Z')

    def test_missing_temporal_extent_but_start_and_end_provided_in_dict_and_wrong(self):
        """Test that errors are raised when input times are not iso"""
        yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader)
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc_missing_attrs.nc'),
                       check_only=True)
        with self.assertRaises(AttributeError):
            md.to_mmd(overrides={"time_coverage_start": "1850/01/01 00:00:00",
                                 "time_coverage_end": "1950/01/01 00:00:00"})
        self.assertEqual(
            md.missing_attributes['errors'][5],
            "time_coverage_start must be in ISO8601 format: "
            "YYYY-mm-ddTHH:MM:SS<second fraction><time zone>.")
        self.assertEqual(
            md.missing_attributes['errors'][6],
            "time_coverage_end must be in ISO8601 format: "
            "YYYY-mm-ddTHH:MM:SS<second fraction><time zone>.")

    def test_temporal_extent_two_startdates(self):
        """Test that two start dates are handled correctly in the
        translation to MMD.
        """
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc_attrs_multiple.nc'),
                       check_only=True)
        ncin = Dataset(md.netcdf_file)
        value = md.get_temporal_extents(mmd_yaml['temporal_extent'], ncin)
        self.assertEqual(value[0]['start_date'], '2020-11-27T13:40:02.019817Z')
        self.assertEqual(value[1]['start_date'], '2020-12-27T13:40:02.019817Z')
        self.assertEqual(value[2]['start_date'], '2021-01-27T13:40:02.019817Z')
        self.assertEqual(value[0]['end_date'], '2020-11-27T13:51:24.401505Z')
        self.assertEqual(value[1]['end_date'], '2020-12-27T13:51:24.019817Z')

    def test_temporal_extent_two_startdates_one_wrong(self):
        """Test that two start dates are handled correctly in the
        translation to MMD.
        """
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc_attrs_multiple.nc'),
                       check_only=True)
        ncin = Dataset(md.netcdf_file, "w", diskless=True)

        valid_start = '2020-11-27T13:40:02.019817Z'
        invalid_start = '2020-13-27T13:40:02.019817'  # month outside [0,12]
        valid_end = '2020-11-27T13:51:24.401505Z'
        invalid_end = '2020-13-27T13:51:24.019817'  # month outside [0,12]

        ncin.time_coverage_start = '{}, {}'.format(valid_start, invalid_start)
        ncin.time_coverage_end = '{}, {}'.format(valid_end, invalid_end)
        value = md.get_temporal_extents(mmd_yaml['temporal_extent'], ncin)

        template = 'ACDD start/end datetime {} is not valid ISO8601:'
        self.assertEqual(value[0]['start_date'], valid_start)
        self.assertIn(template.format(invalid_start), md.missing_attributes['errors'][0])
        self.assertEqual(value[0]['end_date'], valid_end)
        self.assertIn(template.format(invalid_end), md.missing_attributes['errors'][1])

    def test__normalize_iso8601(self):
        def valid(s):
            ndt, _ = normalize_iso8601(s)
            return ndt is not None

        self.assertFalse(valid(""))
        self.assertFalse(valid(None))

        self.assertTrue(valid("2017"))
        self.assertTrue(valid("2017-01"))
        self.assertTrue(valid("2017-01-01"))

        self.assertFalse(valid("2017-01-01T"))
        self.assertFalse(valid("2017-01-01Z"))

        self.assertTrue(valid("2017-01-01T00"))
        self.assertTrue(valid("2017-01-01T00:00"))
        self.assertTrue(valid("2017-01-01T00:00:00"))

        self.assertTrue(valid("2017-01-01T00Z"))
        self.assertTrue(valid("2017-01-01T00:00Z"))
        self.assertTrue(valid("2017-01-01T00:00:00Z"))

        self.assertTrue(valid("2008-08-30T01:45:36.123Z"))
        self.assertTrue(valid("2016-12-13T21:20:37.593194Z"))
        self.assertFalse(valid("2019-02-29T12:00:00Z"))
        self.assertTrue(valid("2020-12-27 13:40:02.019817"))
        self.assertTrue(valid("2020-11-27T13:40:02.019817Z"))

    def test__normalize_iso8601_0(self):

        dt = '2021-01-01T00:00:00Z'
        ndt_expected = '2021-01-01T00:00:00Z'
        ndt_actual = normalize_iso8601_0(dt)
        self.assertEqual(ndt_expected, ndt_actual)

        dt_invalid = 'foobar'
        ndt_expected = dt_invalid
        ndt_actual = normalize_iso8601_0(dt_invalid)
        self.assertEqual(ndt_expected, ndt_actual)

    def test_temporal_extent(self):
        """ToDo: Add docstring"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc.nc'), check_only=True)
        ncin = Dataset(md.netcdf_file)
        value = md.get_temporal_extents(mmd_yaml['temporal_extent'], ncin)
        self.assertEqual(value[0]['start_date'], '2020-11-27T13:40:02.019817Z')
        self.assertEqual(value[0]['end_date'], '2020-11-27T13:51:24.401505Z')

    def test_personnel_multiple_mixed(self):
        """Test that an error is raised if the creator_* attributes
        don't have the same number of comma separated entries.
        """
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(
            os.path.abspath('tests/data/reference_nc_attrs_multiple_mixed_creator.nc'),
            check_only=True
        )
        ncin = Dataset(md.netcdf_file)
        md.get_personnel(mmd_yaml['personnel'], ncin)
        self.assertEqual(
            md.missing_attributes['errors'][0],
            'ACDD attributes creator_name, creator_role, '
            'creator_email and creator_institution must have the same'
            ' number of (comma separated) entries.'
        )

    def test_personnel_multiple(self):
        """ToDo: Add docstring"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc_attrs_multiple.nc'),
                       check_only=True)
        ncin = Dataset(md.netcdf_file)
        value = md.get_personnel(mmd_yaml['personnel'], ncin)
        self.assertEqual(value[0]['name'], 'Trygve')
        self.assertEqual(value[1]['name'], 'Nina')
        self.assertEqual(value[0]['email'], 'trygve@meti.no')
        self.assertEqual(value[1]['email'], 'post@met.no')
        self.assertEqual(value[0]['role'], 'Investigator')
        self.assertEqual(value[1]['role'], 'Technical contact')

    def test_personnel_multiple_creator_and_contributor(self):
        """Test that we can have multiple people in MMD personnel field"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(
            os.path.abspath('tests/data/reference_nc_attrs_multiple_and_contributor.nc'),
            check_only=True
        )
        ncin = Dataset(md.netcdf_file)
        value = md.get_personnel(mmd_yaml['personnel'], ncin)
        self.assertEqual(value[0]['name'], 'Trygve')
        self.assertEqual(value[1]['name'], 'Nina')
        self.assertEqual(value[2]['name'], 'Morten')
        self.assertEqual(value[0]['email'], 'trygve@meti.no')
        self.assertEqual(value[1]['email'], 'post@met.no')
        self.assertEqual(value[2]['email'], 'morten@met.no')
        self.assertEqual(value[0]['organisation'], 'Norwegian Meteorological Institute')
        self.assertEqual(value[1]['organisation'], 'Norwegian Meteorological Institute')
        self.assertEqual(value[2]['organisation'], 'Norwegian Meteorological Institute')
        self.assertEqual(value[0]['role'], 'Investigator')
        self.assertEqual(value[1]['role'], 'Technical contact')
        self.assertEqual(value[2]['role'], 'Investigator')

    def test_personnel_acdd_roles_not_list(self):
        """Test that we can have multiple people in MMD personnel field"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(
            os.path.abspath('tests/data/reference_nc_attrs_multiple_and_contributor.nc'),
            check_only=True
        )
        ncin = Dataset(md.netcdf_file)
        value = md.get_personnel(mmd_yaml['personnel'], ncin)
        self.assertEqual(value[0]['name'], 'Trygve')
        self.assertEqual(value[1]['name'], 'Nina')
        self.assertEqual(value[0]['role'], 'Investigator')
        self.assertEqual(value[1]['role'], 'Technical contact')
        self.assertEqual(value[0]['email'], 'trygve@meti.no')
        self.assertEqual(value[1]['email'], 'post@met.no')
        self.assertEqual(value[0]['organisation'], 'Norwegian Meteorological Institute')
        self.assertEqual(value[1]['organisation'], 'Norwegian Meteorological Institute')

    def test_get_personnel_role_invalid(self):
        mmd_yaml = yaml.load(
            resource_string("py_mmd_tools", "mmd_elements.yaml"), Loader=yaml.FullLoader
        )
        mmd_element = mmd_yaml["personnel"]
        test_in = os.path.abspath('tests/data/reference_nc.nc')
        md = Nc_to_mmd(test_in, check_only=True)
        ncin = Dataset(test_in, "w", diskless=True)

        # iso_topic_category is not valid
        ncin.creator_role = "abcd"
        md.get_personnel(mmd_element, ncin)
        assert "The ACDD attribute 'contact_roles' must" in md.missing_attributes['errors'][0]

    def test_personnel(self):
        """Test reading of personnel from nc file into MMD"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc.nc'), check_only=True)
        ncin = Dataset(md.netcdf_file)
        value = md.get_personnel(mmd_yaml['personnel'], ncin)
        self.assertEqual(value[0]['email'], 'post@met.no')

    def test_iso_topic_category(self):
        """ToDo: Add docstring"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc.nc'), check_only=True)
        ncin = Dataset(md.netcdf_file)
        value = md.get_acdd_metadata(
            mmd_yaml['iso_topic_category'], ncin, 'iso_topic_category'
        )
        self.assertEqual(value[0], 'climatologyMeteorologyAtmosphere')
        self.assertEqual(value[1], 'environment')
        self.assertEqual(value[2], 'oceans')

    def test_get_iso_topic_category_invalid(self):
        mmd_yaml = yaml.load(
            resource_string("py_mmd_tools", "mmd_elements.yaml"), Loader=yaml.FullLoader
        )
        mmd_element = mmd_yaml["iso_topic_category"]
        test_in = os.path.abspath('tests/data/reference_nc.nc')
        md = Nc_to_mmd(test_in, check_only=True)
        ncin = Dataset(test_in, "w", diskless=True)

        # iso_topic_category is not valid
        ncin.iso_topic_category = "abcd"
        md.get_iso_topic_category(mmd_element, ncin)
        assert "The ACDD attribute 'iso_topic_category' must" in md.missing_attributes['errors'][0]

    def test_get_iso_topic_category_not_available(self):
        mmd_yaml = yaml.load(
            resource_string("py_mmd_tools", "mmd_elements.yaml"), Loader=yaml.FullLoader
        )
        mmd_element = mmd_yaml["iso_topic_category"]
        test_in = os.path.abspath('tests/data/reference_nc.nc')
        md = Nc_to_mmd(test_in, check_only=True)
        ncin = Dataset(test_in, "w", diskless=True)

        # iso_topic_category is not present
        value = md.get_iso_topic_category(mmd_element, ncin)
        assert value == ["Not available"]

    def test_get_activity_type_invalid(self):
        """Test that an error is raised if activity_type is not a valid one, e.g. not in
        the list https://htmlpreview.github.io/?https://github.com/metno/mmd/blob/
        master/doc/mmd-specification.html#activity-type"""
        mmd_yaml = yaml.load(
            resource_string("py_mmd_tools", "mmd_elements.yaml"), Loader=yaml.FullLoader
        )
        mmd_element = mmd_yaml["activity_type"]
        test_in = os.path.abspath('tests/data/reference_nc.nc')
        md = Nc_to_mmd(test_in, check_only=True)
        ncin = Dataset(test_in, "w", diskless=True)

        # activity_type is not valid
        ncin.source = "abcd"
        md.get_activity_type(mmd_element, ncin)
        assert ("The ACDD attribute 'source' in MMD attribute 'activity_type'"
                in md.missing_attributes['errors'][0])

    def test_platform_resource_not_MMD(self):
        """Check that the provided resource remains when a platform
        has the same name in GCMD and MMD but the resource provided
        in the netcdf file is GCMD.
        """
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc_missing_keywords_vocab.nc'),
                       check_only=True)
        # The GCMD resource url
        resource = "https://gcmd.earthdata.nasa.gov/kms/concepts/concept_scheme/platforms"
        # Define dataset
        ncin = Dataset(md.netcdf_file, "w", diskless=True)
        ncin.platform = "Sentinel-1A"
        ncin.platform_vocabulary = resource

        # Get the platform dict
        value = md.get_platforms(mmd_yaml['platform'], ncin)
        self.assertEqual(value[0]['resource'], resource)

    def test_missing_vocabulary_platform_instrument_short_name(self):
        """Test that the resource is added if the name matches with
        the MMD vocabulary, but the instrument does not have a valid
        vocabulary url.
        """
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc_missing_keywords_vocab.nc'),
                       check_only=True)
        # Define dataset
        ncin = Dataset(md.netcdf_file, "w", diskless=True)
        ncin.platform = 'Suomi National Polar-orbiting Partnership (SNPP)'
        ncin.instrument = 'VIIRS'
        ncin.instrument_vocabulary = 'not a valid vocab url'
        ncin.platform_vocabulary = 'https://www.wmo-sat.info/oscar/satellites/view/342'

        value = md.get_platforms(mmd_yaml['platform'], ncin)
        self.assertEqual(value[0]['resource'],
                         'https://www.wmo-sat.info/oscar/satellites/view/342')
        self.assertEqual(value[0]['short_name'], 'SNPP')

        self.assertEqual(value[0]['instrument']['resource'],
                         'https://vocab.met.no/mmd/Instrument/VIIRS')

    def test_platform_vocabulary_invalid_url(self):
        """ Check that a platform not listed in the MMD controlled
        vocabulary for platforms is not registered if there is no
        other valid resource url.
        """
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(self.fail_nc, check_only=True)
        ncin = Dataset(md.netcdf_file, "w", diskless=True)
        ncin.platform = 'Fake Environmental Satellite'
        ncin.platform_vocabulary = 'invalid_url'
        value = md.get_platforms(mmd_yaml['platform'], ncin)
        self.assertEqual(value, [])
        self.assertEqual(
            md.missing_attributes['errors'][0],
            "platform must be formed as <platform long name>(<platform short name>). "
            "Platform short name is optional. The platform must either be present in "
            "https://vocab.met.no/mmd/Platform, or in another controlled vocabulary "
            "referenced by a valid url.")

    def test_wrong_platform_name(self):
        """ Test that an error is issued if the platform field is not
        in the format <platform long name>(<platform short name>).
        However, note that one pair of parentheses is allowed in the
        long name.
        """
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(self.fail_nc, check_only=True)
        ncin = Dataset(md.netcdf_file, "w", diskless=True)
        ncin.platform = 'Suomi National Polar-orbiting Partnership (Suomi NPP)(Too Many)(SNPP)'
        value = md.get_platforms(mmd_yaml['platform'], ncin)
        self.assertEqual(value, [])
        self.assertEqual(
            md.missing_attributes['errors'][0],
            "platform must be formed as <platform long name>(<platform short name>). "
            "Platform short name is optional. The platform must either be present in "
            "https://vocab.met.no/mmd/Platform, or in another controlled vocabulary "
            "referenced by a valid url.")

    def test_wrong_instrument_name(self):
        """ Test that an error is issued if the instrument field is
        not in the format
        <instrument long name>(<instrument short name>).
        """
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(self.fail_nc, check_only=True)
        ncin = Dataset(md.netcdf_file, "w", diskless=True)
        ncin.platform = "Suomi National Polar-orbiting Partnership (SNPP)"
        ncin.instrument = 'InstrName (Instrument Name)(Too Many)(IN)'
        value = md.get_platforms(mmd_yaml['platform'], ncin)
        self.assertEqual(value[0]['short_name'], "SNPP")
        self.assertEqual(
            md.missing_attributes['warnings'][0],
            "instrument must be formed as <instrument long name>(<instrument short name>). "
            "Instrument is optional. The instrument must either be present in "
            "https://vocab.met.no/mmd/Instrument, or in another controlled vocabulary "
            "referenced by a valid url.")

    def test_platform_name_extra_parentheses(self):
        """ Test that parentheses in the platform long name are
        allowed, as long as a velid vocabulary url is provided.

        TODO: Find a platform where this is actually the case...
        """
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(self.fail_nc, check_only=True)
        ncin = Dataset(md.netcdf_file, "w", diskless=True)
        ncin.platform = 'Suomi National Polar-orbiting Partnership (Suomi NPP)(SNPP)'
        # A valid url is required
        ncin.platform_vocabulary = "https://www.validurl.no"
        value = md.get_platforms(mmd_yaml['platform'], ncin)
        self.assertEqual(value[0]['long_name'],
                         'Suomi National Polar-orbiting Partnership (Suomi NPP)')
        self.assertEqual(value[0]['short_name'], 'SNPP')

    def test_instrument_name_extra_parentheses(self):
        """ Test that parentheses in the long name are allowed
        """
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(self.fail_nc, check_only=True)
        ncin = Dataset(md.netcdf_file, "w", diskless=True)
        ncin.platform = "Platform Name (PN)"
        ncin.platform_vocabulary = "https://www.validurl.no"
        # This is an entry in MMD:
        ncin.instrument = 'Synthetic Aperture Radar (C-band) (SAR-C)'
        value = md.get_platforms(mmd_yaml['platform'], ncin)
        self.assertEqual(value[0]['instrument']['short_name'], 'SAR-C')
        self.assertEqual(value[0]['instrument']['long_name'], 'Synthetic Aperture Radar (C-band)')

    def test_missing_platform_vocabulary(self):
        """ Test that an error is issued if the platform vocabulary
        is missing and the platform is not in
        https://vocab.met.no/mmd/en/page/Platform.
        """
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(self.fail_nc, check_only=True)
        ncin = Dataset(md.netcdf_file, "w", diskless=True)
        # Note that Envisat is not in the MMD vocabulary
        ncin.platform = 'FakeEnvisat'
        value = md.get_platforms(mmd_yaml['platform'], ncin)
        self.assertEqual(value, [])
        self.assertEqual(
            md.missing_attributes['errors'][0],
            "platform must be formed as "
            "<platform long name>(<platform short name>). Platform "
            "short name is optional. The platform must either be "
            "present in https://vocab.met.no/mmd/Platform, or in "
            "another controlled vocabulary referenced by a valid "
            "url.")

    def test_missing_vocabulary_platform(self):
        """Check that a platform which is in the MMD vocabulary but
        where the netcdf file does not provide a platform_resource,
        is found in MMD and that the MMD vocabulary resource is
        provided.
        """
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc_missing_keywords_vocab.nc'),
                       check_only=True)
        ncin = Dataset(md.netcdf_file)
        value = md.get_platforms(mmd_yaml['platform'], ncin)
        resource_link = "https://vocab.met.no/mmd/Platform/SNPP"
        self.assertEqual(value[0]['resource'], resource_link)

    def test_get_short_and_long_names(self):
        """Check that get_short_and_long_names method returns the
        correct tuples in different cases.
        """
        field = ""
        self.assertEqual(get_short_and_long_names(field)[0], None)
        self.assertEqual(get_short_and_long_names(field)[1], None)

        field = "long name (short name)"
        self.assertEqual(get_short_and_long_names(field)[0], "long name")
        self.assertEqual(get_short_and_long_names(field)[1], "short name")

        field = "long name (with more) (short name)"
        self.assertEqual(get_short_and_long_names(field)[0], "long name (with more)")
        self.assertEqual(get_short_and_long_names(field)[1], "short name")

    def test_keywords_missing(self):
        """ToDo: Add docstring"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc_fail.nc'), check_only=True)
        ncin = Dataset(md.netcdf_file)
        md.get_keywords(mmd_yaml['keywords'], ncin)
        self.assertEqual(
            md.missing_attributes['errors'][0],
            'keywords_vocabulary is a required ACDD attribute'
        )
        self.assertEqual(
            md.missing_attributes['errors'][1],
            'keywords is a required ACDD attribute'
        )

    def test__keywords_vocabulary__correctly_formatted(self):
        """Check that error massages are added if the
        keywords_vocabulary attribute is not formatted
        as short_name:long_name:url
        """
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(self.fail_nc, check_only=True)
        ncin = Dataset(md.netcdf_file, "w", diskless=True)
        ncin.keywords = "GCMDSK:Earth Science > Atmosphere > Atmospheric radiation, " \
                        "GEMET:Meteorological geographical features, " \
                        "GEMET:Atmospheric conditions, " \
                        "NORTHEMES:Weather and climate"
        ncin.keywords_vocabulary = ""
        md.get_keywords(mmd_yaml['keywords'], ncin)
        self.assertEqual(
            md.missing_attributes['errors'][0],
            'keywords_vocabulary must be formatted as <short_name>:<long_name>:<url>'
        )

    def test_keywords_vocabulary__invalid_url_pattern(self):
        """ Test that an error message is issued if the url pattern
        of a vocabulary is wrong.
        """
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(self.fail_nc, check_only=True)
        ncin = Dataset(md.netcdf_file, "w", diskless=True)
        ncin.keywords = "GCMDSK:Earth Science > Atmosphere > Atmospheric radiation, " \
                        "GEMET:Meteorological geographical features, " \
                        "GEMET:Atmospheric conditions, " \
                        "NORTHEMES:Weather and climate"
        ncin.keywords_vocabulary = (
            "GCMDSK:GCMD Science Keywords:"
            "https://gcmd.earth_data.nasa.gov/kms/concepts/concept_scheme/sciencekeywords, "
            "GEMET:INSPIRE Themes:http://inspire.ec.eur_opa.eu/theme, "
            "NORTHEMES:GeoNorge Themes:"
            "https://register.geonorge.no/metadata-kodelister/nasjonal-temainndeling")
        md.get_keywords(mmd_yaml['keywords'], ncin)
        self.assertEqual(
            md.missing_attributes['errors'][0],
            'https://gcmd.earth_data.nasa.gov/kms/concepts/concept_scheme/sciencekeywords'
            ' in keywords_vocabulary attribute is not a valid url'
        )

    def test_spaces_around_keywords_are_stripped(self):
        """Test that if a keyword is provided as
        'GEMET: Meteorological geographical features ,', then the
        spaces around 'Meteorological geographical features' are
        removed.
        """
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(self.fail_nc, check_only=True)
        ncin = Dataset(md.netcdf_file, "w", diskless=True)
        ncin.keywords = "GCMDSK: Earth Science > Atmosphere > Atmospheric radiation , " \
                        "GEMET: Meteorological geographical features, " \
                        "GEMET: Atmospheric conditions , " \
                        "NORTHEMES:Weather and climate "
        ncin.keywords_vocabulary = (
            "GCMDSK:GCMD Science Keywords:https://vocab.met.no/GCMDSK,"
            "GEMET:INSPIRE Themes:http://inspire.ec.eur_opa.eu/theme, "
            "NORTHEMES:GeoNorge Themes:"
            "https://register.geonorge.no/metadata-kodelister/nasjonal-temainndeling")
        data = md.get_keywords(mmd_yaml['keywords'], ncin)
        self.assertEqual(data[0]["keyword"][0],
                         "Earth Science > Atmosphere > Atmospheric radiation")

    def test_keywords_vocabulary_missing(self):
        """ToDo: Add docstring"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc_missing_keywords_vocab.nc'),
                       check_only=True)
        ncin = Dataset(md.netcdf_file)
        md.get_keywords(mmd_yaml['keywords'], ncin)
        self.assertEqual(
            md.missing_attributes['errors'][0],
            'keywords_vocabulary is a required ACDD attribute'
        )

    def test_keywords_standard_name_not_in_CFSTDN(self):
        """Test that an error is added if the CF standard name does
        not exist.
        """
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc_non_cf_standard_name.nc'),
                       check_only=True)
        ncin = Dataset(md.netcdf_file)
        md.get_keywords(mmd_yaml['keywords'], ncin)
        self.assertEqual(
            md.missing_attributes['errors'][0],
            'The standard name this_is_not_a_cf_standard_name is not a CF standard name '
            '(see https://vocab.met.no/CFSTDN)'
        )

    def test_keywords(self):
        """ToDo: Add docstring"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc.nc'), check_only=True)
        ncin = Dataset(md.netcdf_file)
        value = md.get_keywords(mmd_yaml['keywords'], ncin)
        self.assertEqual(value[0]['vocabulary'], 'GCMDSK')
        self.assertEqual(
            value[0]['resource'],
            'https://gcmd.earthdata.nasa.gov/kms/concepts/concept_scheme/sciencekeywords'
        )
        self.assertEqual(value[0]['keyword'], [
            'Earth Science > Atmosphere > Atmospheric radiation'
        ])
        self.assertEqual(value[1]['vocabulary'], 'GEMET')
        self.assertEqual(value[1]['resource'], 'http://inspire.ec.europa.eu/theme')
        self.assertEqual(value[1]['keyword'], [
            'Meteorological geographical features',
            'Atmospheric conditions', 'Oceanographic geographical features'
        ])
        self.assertEqual(value[3]['vocabulary'], 'CFSTDN')
        self.assertEqual(
            value[3]['resource'],
            'https://vocab.met.no/mmd/Keywords_Vocabulary/CFSTDN'
        )

    def test_keywords_multiple(self):
        """ToDo: Add docstring"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc_attrs_multiple.nc'),
                       check_only=True)
        ncin = Dataset(md.netcdf_file)
        value = md.get_keywords(mmd_yaml['keywords'], ncin)
        self.assertEqual(value[0]['vocabulary'], 'GCMDSK')
        self.assertEqual(
            value[0]['resource'],
            'https://gcmd.earthdata.nasa.gov/kms/concepts/concept_scheme/sciencekeywords'
        )
        self.assertEqual(value[0]['keyword'], [
            'Earth Science > Atmosphere > Atmospheric radiation',
            'EARTH SCIENCE > BIOLOGICAL CLASSIFICATION > ANIMALS/VERTEBRATES'
        ])

    def test_platforms(self):
        """ToDo: Add docstring"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc.nc'), check_only=True)
        ncin = Dataset(md.netcdf_file)
        value = md.get_platforms(mmd_yaml['platform'], ncin)
        self.assertEqual(
            value[0]['long_name'],
            'Suomi National Polar-orbiting Partnership'
        )
        self.assertEqual(
            value[0]['instrument']['long_name'],
            'Visible/Infrared Imager Radiometer Suite'
        )

    def test_platform_with_gcmd_vocabulary(self):
        """Check that the general rules are followed when a
        vocabulary different from MMD is used, and that we use what
        we get."""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc_gcmd_platform.nc'),
                       check_only=True)
        ncin = Dataset(md.netcdf_file)
        value = md.get_platforms(mmd_yaml['platform'], ncin)
        """ The following assertions should fail when we have code to
        check the provided instrument vocabulary (see
        https://gcmd.earthdata.nasa.gov/kms/concepts/concept_scheme/instruments
        and
        https://gcmd.earthdata.nasa.gov/kms/concept/ed400e7c-229e-48be-9a93-84f2fc864448).
        """
        self.assertEqual(value[0]['long_name'], 'Sentinel-1B')
        self.assertEqual(value[0]['instrument']['long_name'], 'Synthetic Aperture Radar')
        self.assertEqual(value[0]['instrument']['short_name'], 'C-band')
        self.assertEqual(
            value[0]['instrument']['resource'],
            'https://gcmd.earthdata.nasa.gov/kms/concepts/concept_scheme/instruments/')

    def test_projects(self):
        """Test getting project information from nc-file"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc.nc'), check_only=True)
        ncin = Dataset(md.netcdf_file)
        value = md.get_projects(mmd_yaml['project'], ncin)
        self.assertEqual(value[0]['long_name'], 'MET Norway core services')

    def test_projects_with_short_name(self):
        """Test getting project information with short name from nc-file"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc_project_with_short_name.nc'),
                       check_only=True)
        ncin = Dataset(md.netcdf_file)
        value = md.get_projects(mmd_yaml['project'], ncin)
        self.assertEqual(value[0]['long_name'], 'MET Norway core services')
        self.assertEqual(value[0]['short_name'], 'METNCS')

    def test_projects_missing(self):
        """Test getting project information when this is missing"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc_missing_project.nc'),
                       check_only=True)
        ncin = Dataset(md.netcdf_file)
        value = md.get_projects(mmd_yaml['project'], ncin)
        self.assertEqual(len(value), 0)

    def test_projects_malformed(self):
        """Test getting project information when this is malformed"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc_malformed_project.nc'),
                       check_only=True)
        ncin = Dataset(md.netcdf_file)
        md.get_projects(mmd_yaml['project'], ncin)
        self.assertEqual(md.missing_attributes['errors'][0],
                         ("project must be formed as <project long name>(<project short name>). "
                          "Project short name is optional"))

    def test_dataset_citation_missing_attrs(self):
        """Test that missing url and other is accepted"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc_missing_keywords_vocab.nc'),
                       check_only=True)
        ncin = Dataset(md.netcdf_file)
        value = md.get_dataset_citations(mmd_yaml['dataset_citation'], ncin)
        self.assertEqual(value[0]['author'],
                         'DIVISION FOR OBSERVATION QUALITY AND DATA PROCESSING')
        """ Not issued unless the warning in nc_to_mmd.py is uncommented:
        self.assertEqual(md.missing_attributes['warnings'][0],
                         'metadata_link attribute is missing')
        """

    def test_dataset_citation_as_kwarg(self):
        """Test that the user can provide a custom dataset citation.
        """
        dc = {
            "author": "No Name",
            "publication_date": "2023-07-06",
            "title": "Some random title"}
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(self.fail_nc, check_only=True)
        ncin = Dataset(md.netcdf_file, "w", diskless=True)
        ncin.creator_name = "Tester Test"
        ncin.date_created = "2022-11-04T11:06:10Z"
        ncin.title = "Test dataset"
        ncin.publisher_name = "Norwegian Meteorological Institute"
        ncin.metadata_link = "invalid_url"
        value = md.get_dataset_citations(mmd_yaml['dataset_citation'], ncin, dataset_citation=dc)
        self.assertEqual(value[0]['author'], 'No Name')

    def test_check_only(self):
        """Run netCDF attributes to MMD translation with check_only
        flag.
        """
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc.nc'), check_only=True)
        req_ok, msg = md.to_mmd()
        self.assertTrue(req_ok)
        self.assertEqual(msg, '')

        # Create custom dataset citation
        dc = {
            "author": "No Name",
            "publication_date": "2023-07-06",
            "title": "Some random title"}
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc.nc'), check_only=True)
        req_ok, msg = md.to_mmd(overrides={"dataset_citation": dc})
        self.assertEqual(md.metadata['dataset_citation'][0]['author'], 'No Name')

    def test_dataset_citation(self):
        """ToDo: Add docstring"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc.nc'), check_only=True)
        ncin = Dataset(md.netcdf_file)
        value = md.get_dataset_citations(mmd_yaml['dataset_citation'], ncin)
        self.assertEqual(
            value[0]['title'],
            'Direct Broadcast data processed in satellite swath to L1C.'
        )
        self.assertEqual(value[0]['publication_date'],
                         '2020-11-27T14:05:56Z')
        self.assertEqual(value[0]['title'],
                         'Direct Broadcast data processed in satellite swath to L1C.')
        self.assertEqual(value[0]['publisher'],
                         'Norwegian Meteorological Institute')
        self.assertEqual(value[0]['url'],
                         'https://data.met.no/dataset/b7cb7934-77ca-4439-812e-f560df3fe7eb')

    def test_dataset_citation_invalid_date(self):
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc.nc'), check_only=True)
        ncin = Dataset(md.netcdf_file, "w", diskless=True)
        ncin.time_coverage_start = "2020-11-27T13:40:02.019817Z"
        ncin.time_coverage_end = "2020-11-27T13:51:24.401505Z"
        ncin.creator_name = 'Kreator Kreatorsen'
        ncin.date_created = "2020-11-28T13:51:24.401505Z"
        ncin.title = "Test dataset"
        ncin.metadata_link = "https://data.met.no/dataset/uuid-for-the-dataset"
        ncin.references = "Some free-text refences"
        value = md.get_dataset_citations(mmd_yaml['dataset_citation'], ncin)
        self.assertEqual(value[0]['author'], 'Kreator Kreatorsen')

        # Test that an error is appended if date created is not in
        # the correct format
        ncin.date_created = "2020-99-28 13:51:24"
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        value = md.get_dataset_citations(mmd_yaml['dataset_citation'], ncin)
        self.assertIn(
            "ACDD attribute date_created contains an invalid ISO8601 date:",
            md.missing_attributes['errors'][0]
        )

    @patch('py_mmd_tools.nc_to_mmd.Dataset')
    def test_oserror_opendap(self, mock_nc_dataset):
        """ToDo: Add docstring"""
        mock_nc_dataset.side_effect = OSError
        fn = os.path.abspath('tests/data/reference_nc.nc')
        url = (
            'http://nbstds.met.no/thredds/dodsC/NBS/S1A/2021/01/31/IW/'
            'S1A_IW_GRDH_1SDV_20210131T172816_20210131T172841_036385_04452D_505F.nc'
        )
        try:
            Nc_to_mmd(fn, url, check_only=True)
        except OSError:
            pass
        mock_nc_dataset.assert_called_with(fn+'#fillmismatch')

    def test_get_metadata_identifier(self):
        """Test that an AttributeError is raised if there are
        inconsistencies between the hardcoded acdd values, and the ones
        from mmd_elements.yaml.
        """
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        # Only one value in the list
        mmd_yaml['metadata_identifier']['acdd'] = {'id': {}}
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc.nc'), check_only=True)
        ncin = Dataset(md.netcdf_file)
        with self.assertRaises(AttributeError) as e:
            md.get_metadata_identifier(mmd_yaml['metadata_identifier'], ncin)
        self.assertEqual(
            "ACDD attribute inconsistency in mmd_elements.yaml. Expected id and "
            "naming_authority but received ['id'].",
            str(e.exception)
        )
        # Inconsistency of ACCD id in mmd_elements.yaml (='jkhakjh')
        # and the hardcoded one (='id')
        mmd_yaml['metadata_identifier']['acdd'] = {'jkhakjh': {}, 'naming_authority': {}}
        with self.assertRaises(AttributeError) as e:
            md.get_metadata_identifier(mmd_yaml['metadata_identifier'], ncin)
        self.assertEqual(
            "ACDD attribute inconsistency in mmd_elements.yaml. Expected id and "
            "naming_authority but received ['jkhakjh', 'naming_authority'].",
            str(e.exception)
        )
        # Inconsistency of ACCD naming_authority in mmd_elements.yaml
        # (='jklhkha') and the hardcoded one (='naming_authority')
        mmd_yaml['metadata_identifier']['acdd'] = {'id': {}, 'jklhkha': {}}
        with self.assertRaises(AttributeError) as e:
            md.get_metadata_identifier(mmd_yaml['metadata_identifier'], ncin)
        self.assertEqual(
            "ACDD attribute inconsistency in mmd_elements.yaml. Expected id and "
            "naming_authority but received ['id', 'jklhkha'].",
            str(e.exception)
        )
        # Change the valid naming authorities to force an error
        md.VALID_NAMING_AUTHORITIES = ['jada.no']
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md.get_metadata_identifier(mmd_yaml['metadata_identifier'], ncin)
        self.assertEqual(
            md.missing_attributes['errors'][0],
            'naming_authority ACDD attribute is not valid.'
        )

    def test_to_mmd_warning_not_empty(self):
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        mmd_yaml['dummy_field'] = {}
        mmd_yaml['dummy_field']['minOccurs'] = '1'
        mmd_yaml['dummy_field']['default'] = 'test'
        mmd_yaml['dummy_field']['acdd_ext'] = {
            'dummy_field': {
                'comment': 'no comment',
                'default': 'hei'}}
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc.nc'), check_only=True)
        md.to_mmd(mmd_yaml=mmd_yaml)
        self.assertEqual(
            md.missing_attributes['warnings'][2],
            'Using default value test for dummy_field'
        )

    def test_create_requires_naming_authority(self):
        """Test that we cannot create an MMD file if naming_authority
        is missing, and that the uuid validation fails for an id which
        is not an uuid.
        """
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        # The id attribute is not a uuid
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc_fail.nc'), check_only=True)
        ncin = Dataset(md.netcdf_file)
        value = md.get_metadata_identifier(mmd_yaml['metadata_identifier'], ncin)
        self.assertFalse(Nc_to_mmd.is_valid_uuid(value))
        self.assertEqual(':', value)
        with self.assertRaises(AttributeError) as context:
            md.to_mmd()
        """
        Note: there will be two 'naming_authority is a required
        attribute' messages, since get_metadata_identifier is called
        twice (first directly in this test, then from the to_mmd
        function.
        """
        self.assertTrue('naming_authority is a required attribute' in str(context.exception))
        self.assertTrue('id ACDD attribute is not valid.' in str(context.exception))

    def test_get_correct_id_from_ncfile(self):
        """ToDo: Add docstring
        """
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        # The id attribute is a uuid
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc.nc'), check_only=True)
        ncin = Dataset(md.netcdf_file)
        value = md.get_metadata_identifier(mmd_yaml['metadata_identifier'], ncin)
        self.assertEqual(value, 'no.met:b7cb7934-77ca-4439-812e-f560df3fe7eb')

    def test__to_mmd__missing_id(self):
        """Test that an AttributeError is raised for missing id
        attribute.
        """
        # nc file is missing the id attribute
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc_id_missing.nc'), check_only=True)
        with self.assertRaises(AttributeError):
            md.to_mmd()
        ncin = Dataset(md.netcdf_file)
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        value = md.get_metadata_identifier(mmd_yaml['metadata_identifier'], ncin)
        self.assertEqual(
            md.missing_attributes['errors'][0], 'id is a required attribute.'
        )
        self.assertEqual(
            md.missing_attributes['errors'][1], 'naming_authority is a required attribute.'
        )
        self.assertFalse(Nc_to_mmd.is_valid_uuid(md.metadata['metadata_identifier']))
        self.assertEqual(':', value)

    def test__to_mmd__invalid_uuid(self):
        """Test that we cannot create an MMD file if the netcdf id
        attribute is not a valid uuid.
        """
        # The id attribute is not a uuid
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc_id_not_uuid.nc'), check_only=True)
        with self.assertRaises(AttributeError):
            md.to_mmd()
        self.assertFalse(Nc_to_mmd.is_valid_uuid(md.metadata['metadata_identifier']))
        self.assertEqual(':', md.metadata['metadata_identifier'])

    def test__to_mmd__error_if_acdd_id_is_invalid(self):
        """Test that metadata_identifier is set to an empty string, and
        that an exception is raised if the ACDD id is not a valid uuid.
        """
        # The id attribute is not a uuid
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc_id_not_uuid.nc'), check_only=True)
        with self.assertRaises(AttributeError):
            md.to_mmd()
        self.assertEqual(
            md.missing_attributes['errors'][0], (
                'naming_authority is a required attribute.'
            )
        )
        self.assertEqual(
            md.missing_attributes['errors'][1], (
                'id ACDD attribute is not valid.'
            )
        )
        self.assertFalse(Nc_to_mmd.is_valid_uuid(md.metadata['metadata_identifier']))
        ncin = Dataset(md.netcdf_file)
        id = ncin.getncattr('id')
        self.assertNotEqual(id, md.metadata['metadata_identifier'])
        self.assertEqual(':', md.metadata['metadata_identifier'])

    def test__to_mmd__get_correct_id_from_ncfile(self):
        """Test that the id attribute in the netcdf file is valid, and
        used in the MMD xml file.
        """
        # The id attribute is a uuid
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc.nc'), check_only=True)
        md.to_mmd()
        ncin = Dataset(md.netcdf_file)
        id = ncin.getncattr('id')
        self.assertEqual(md.missing_attributes['errors'], [])
        self.assertTrue(id in md.metadata['metadata_identifier'])

    def test_get_acdd_metadata_sets_warning_msg(self):
        """Check that a warning is issued by the get_acdd_metadata
        function if a default value is used for a required element.
        """
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc_id_missing.nc'), check_only=True)
        ncin = Dataset(md.netcdf_file)
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        lang = mmd_yaml['dataset_language']
        # Warnings are only issued when the field is required.
        # Currently, this is not the case for any of the fields
        # used in this function, so we force it:
        lang['minOccurs'] = '1'
        md.get_acdd_metadata(lang, ncin, 'dataset_language')
        self.assertEqual(
            md.missing_attributes['warnings'][0],
            'Using default value en for dataset_language'
        )

    def test_create_mmd_2(self):
        """ToDo: Add docstring"""
        self.maxDiff = None
        md = Nc_to_mmd(self.fail_nc, check_only=True)
        with self.assertRaises(AttributeError):
            md.to_mmd()

    def test_all_valid_nc_files_passing(self):
        """Test MMD creation from the valid netcdf files, and validation
        with the mmd_strict.xsd
        """
        """ToDo: Add docstring"""
        valid_files = [
            os.path.join(pathlib.Path.cwd(), 'tests/data/reference_nc.nc'),
            os.path.join(pathlib.Path.cwd(), 'tests/data/reference_nc_attrs_multiple.nc'),
        ]
        for file in valid_files:
            tested = tempfile.mkstemp()[1]
            md = Nc_to_mmd(
                file,
                os.path.join('https://thredds.met.no/thredds/dodsC/', file),
                checksum_calculation=True,
                output_file=tested)
            md.to_mmd()
            xsd_obj = etree.XMLSchema(etree.parse(self.reference_xsd))
            xml_doc = etree.ElementTree(file=tested)
            valid = xsd_obj.validate(xml_doc)
            self.assertTrue(valid, msg='%s' % xsd_obj.error_log)

    def test_create_mmd_missing_publisher_url(self):
        """Test that a missing publisher url does not cause an error"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(self.fail_nc, check_only=True)
        ncin = Dataset(md.netcdf_file)
        value = md.get_data_centers(mmd_yaml['data_center'], ncin)
        self.assertEqual(value, [{
            'data_center_name': {
                'short_name': 'MET Norway',
                'long_name': 'Norwegian Meteorological Institute'
            },
            'data_center_url': ''
        }])

    def test_create_mmd_missing_update_times(self):
        """Test that an error is reported if date_created attribute is
        missing from the netcdf file.
        """
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(self.fail_nc, check_only=True)
        ncin = Dataset(md.netcdf_file)
        md.get_metadata_updates(mmd_yaml['last_metadata_update'], ncin)
        self.assertEqual(
            md.missing_attributes['errors'][0],
            'ACDD attribute date_created is required'
        )

    def test_publication_date__is_a_list_of_dates(self):
        """The publication data can be a list of dates but is set to
        date_created. In most cases it is the only one item, but we
        need to check that what we get from the netcdf file is an
        actual list, and that the items are actual datestrings.
        """
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(self.reference_nc, check_only=True)
        # To overwrite date_created, wihtout saving it to file we use diskless
        ncin = Dataset(md.netcdf_file)
        data = md.get_dataset_citations(mmd_yaml['dataset_citation'], ncin)
        self.assertEqual(
            data[0]['title'],
            'Direct Broadcast data processed in satellite swath to L1C.')

    def test_get_metadata_updates__datetimes_not_iso(self):
        """ Test that an error is raised if datetimes of metadata
        updates are not ISO 8601.
        """
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(self.fail_nc, check_only=True)
        # To overwrite date_created, wihtout saving it to file we use diskless
        ncin = Dataset(md.netcdf_file, "w", diskless=True)
        ncin.date_created = '2019/01/01 00:00:00'
        md.get_metadata_updates(mmd_yaml['last_metadata_update'], ncin)
        self.assertEqual(
            md.missing_attributes['errors'][0],
            "Datetime element must be in ISO8601 format: "
            "YYYY-mm-ddTHH:MM:SS<second fraction><time zone>.")

    def test_ACDD_attr__date_created(self):
        """Test date_created is handled as it should
        """
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(self.fail_nc, check_only=True)
        # To overwrite date_created, wihtout saving it to file we use diskless
        ncin = Dataset(md.netcdf_file, "w", diskless=True)
        ncin.date_created = '2019-01-01T00:00:00Z'
        data = md.get_metadata_updates(mmd_yaml['last_metadata_update'], ncin)
        self.assertIn(
            {'datetime':  ncin.date_created, 'type': 'Created'},
            data['update']
        )
        assert (len(data['update']) == 1)
        self.assertEqual(data['update'][0]['type'], 'Created')

    def test_get_metadata_updates_wrong_input_dict(self):
        """Test that an error is raised if there is inconsistency
        between the fields in mmd_elements.yaml and the hardcoded
        fields in the get_metadata_updates function.
        """
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        in_dict = mmd_yaml['last_metadata_update']
        in_dict['update']['datetime']['acdd'] = {
            'new_name_for_date_created': {},  # this will cause an error
        }
        md = Nc_to_mmd(self.reference_nc, check_only=True)
        ncin = Dataset(md.netcdf_file)
        with self.assertRaises(AttributeError) as context1:
            md.get_metadata_updates(in_dict, ncin)
        self.assertTrue(
            'ACDD attribute inconsistency in mmd_elements.yaml' in str(context1.exception)
        )
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )

    def test_create_mmd_missing_abstract(self):
        """ToDo: Add docstring"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(self.fail_nc, check_only=True)
        ncin = Dataset(md.netcdf_file)
        md.get_abstracts(mmd_yaml['abstract'], ncin)
        self.assertEqual(
            md.missing_attributes['errors'][0],
            'summary is a required ACDD attribute'
        )

    def test_publication_date(self):
        """ToDo: Add docstring"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc.nc'), check_only=True)
        ncin = Dataset(md.netcdf_file)
        value = md.get_dataset_citations(mmd_yaml['dataset_citation'], ncin)
        dt = isoparse(value[0]['publication_date'])
        self.assertEqual(dt.year, 2020)
        self.assertEqual(dt.month, 11)
        self.assertEqual(dt.day, 27)
        self.assertEqual(
            value[0]['title'], 'Direct Broadcast data processed in satellite swath to L1C.'
        )

    def test_checksum_off(self):
        """ToDo: Add docstring"""
        fn = os.path.abspath('tests/data/reference_nc.nc')
        md = Nc_to_mmd(fn, check_only=True)
        md.to_mmd()
        with self.assertRaises(KeyError):
            md.metadata['storage_information']['checksum']
            md.metadata['storage_information']['checksum_type']
        # Check if default is False
        md = Nc_to_mmd(fn, check_only=True)
        md.to_mmd()
        with self.assertRaises(KeyError):
            md.metadata['storage_information']['checksum']
            md.metadata['storage_information']['checksum_type']

    def test_spatial_repr(self):
        """ToDo: Add docstring"""
        tempfile.mkstemp()[1]
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc.nc'), check_only=True)
        md.to_mmd()
        spatial_repr = md.metadata['spatial_representation']
        self.assertEqual(spatial_repr, 'grid')

    def test_spatial_repr_fail(self):
        """ToDo: Add docstring"""
        tempfile.mkstemp()[1]
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc_missing_spatial_repr.nc'),
                       check_only=True)
        with self.assertRaises(AttributeError):
            md.to_mmd()
        self.assertEqual(
            md.missing_attributes['errors'][1],
            'geospatial_lat_max is a required attribute'
        )

    def test_access_constraint(self):
        """ToDo: Add docstring"""
        tempfile.mkstemp()[1]
        md = Nc_to_mmd(os.path.abspath('tests/data/reference_nc.nc'), check_only=True)
        md.to_mmd()
        spatial_repr = md.metadata['access_constraint']
        self.assertEqual(spatial_repr, 'Open')

    def test_check_attributes_not_empty(self):
        md = Nc_to_mmd(self.fail_nc, check_only=True)
        ncin = Dataset(md.netcdf_file, "w", diskless=True)
        ncin.geospatial_bounds = ""
        with self.assertRaises(ValueError) as e:
            md.check_attributes_not_empty(ncin)
        self.assertIn('Global attribute geospatial_bounds is empty - please correct.',
                      str(e.exception))

    def test_check_attributes_not_empty__accepts_0(self):
        """ Previous versions of py-mmd-tools had a Boolean test on
        each global attribute. Since 0 evaluates to False, this was
        a bug. This test checks that 0 is accepted.
        """
        md = Nc_to_mmd(self.fail_nc, check_only=True)
        ncin = Dataset(md.netcdf_file, "w", diskless=True)
        ncin.subswath = 0
        self.assertEqual(None, md.check_attributes_not_empty(ncin))

    def test_check_feature_type__missing(self):
        """ Test that the correct warning is issued if the CF
        attribute featureType is missing.
        """
        md = Nc_to_mmd(self.fail_nc, check_only=True)
        ncin = Dataset(md.netcdf_file, "w", diskless=True)
        ncin.tull = "tull"
        md.check_feature_type(ncin)
        self.assertEqual(
            md.missing_attributes["warnings"][0],
            "CF attribute featureType is missing - one of the feature"
            " types listed in Table 9.1 in https://cfconventions.org/"
            "Data/cf-conventions/cf-conventions-1.10/cf-conventions."
            "html#_features_and_feature_types should be used.")

    def test_check_feature_type__wrong(self):
        """ Test that the correct warning is issued if the CF
        attribute featureType is wrong.
        """
        md = Nc_to_mmd(self.fail_nc, check_only=True)
        ncin = Dataset(md.netcdf_file, "w", diskless=True)
        ncin.featureType = "tull"
        md.check_feature_type(ncin)
        self.assertEqual(
            md.missing_attributes["errors"][0],
            "featureType seems to be wrong - it should be picked from "
            "Table 9.1 in https://cfconventions.org/Data/cf-"
            "conventions/cf-conventions-1.10/cf-conventions."
            "html#_features_and_feature_types should be used.")

    def test_check_conventions__missing(self):
        md = Nc_to_mmd(self.fail_nc, check_only=True)
        ncin = Dataset(md.netcdf_file, "w", diskless=True)
        ncin.tull = "tull"
        md.check_conventions(ncin)
        self.assertEqual(
            md.missing_attributes["errors"][0],
            'Required attribute "Conventions" is missing. This should'
            ' be provided as a comma-separated string of the '
            'conventions that are followed by the dataset.')

    def test_check_conventions__cf_and_acdd_missing(self):
        md = Nc_to_mmd(self.fail_nc, check_only=True)
        ncin = Dataset(md.netcdf_file, "w", diskless=True)
        ncin.Conventions = "tull"
        md.check_conventions(ncin)
        self.assertEqual(
            md.missing_attributes["errors"][0],
            'The dataset should follow the CF-standard. Please '
            'provide the CF standard version in the Conventions '
            'attribute.')
        self.assertEqual(
            md.missing_attributes["errors"][1],
            'The dataset should follow the ACDD convention. '
            'Please provide the ACDD convention version in '
            'the "Conventions" attribute.')

    def test_institution_name_parsing(self):
        """Test that a valid institution string passed as longname (shortname)
        is parsed correctly.
        """
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(self.fail_nc, check_only=True)
        ncin = Dataset(md.netcdf_file, "w", diskless=True)
        ncin.institution = "Norwegian Meteorological Institute (MET Norway)"
        data = md.get_data_centers(mmd_yaml['data_center'], ncin)
        self.assertEqual(data[0]['data_center_name']['long_name'],
                         'Norwegian Meteorological Institute')
        self.assertEqual(data[0]['data_center_name']['short_name'], 'MET Norway')

    def test_institution_short_name_missing(self):
        """Test that if shortname is missing from institution an error is raised."""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(self.fail_nc, check_only=True)
        ncin = Dataset(md.netcdf_file, "w", diskless=True)
        ncin.institution = "Norwegian Meteorological Institute"
        md.get_data_centers(mmd_yaml['data_center'], ncin)
        self.assertEqual(
            md.missing_attributes['errors'][0],
            "institution must be formed as <institution long name> (<institution short name>). "
            "Both are required attributes.")

    def test_acdd_references_as_related_information1(self):
        """ Test that references (doi/uri) are correctly retrieved."""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(self.reference_nc, check_only=True)
        ncin = Dataset(md.netcdf_file)
        data = md.get_related_information(mmd_yaml['related_information'], ncin)
        self.assertEqual(
            data[0]['resource'],
            'https://data.met.no/dataset/b7cb7934-77ca-4439-812e-f560df3fe7eb')
        self.assertEqual(data[0]['type'], 'Dataset landing page')
        self.assertEqual(data[1]['resource'], 'https://ieeexplore.ieee.org/document/7914752')
        self.assertEqual(data[1]['type'], 'Scientific publication')

    def test_acdd_references_as_related_information2(self):
        """ Test that references (doi/uri) are correctly retrieved."""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(self.fail_nc, check_only=True)
        ncin = Dataset(md.netcdf_file, "w", diskless=True)
        ncin.references = (
            "https://data.met.no/dataset/3f9974bf-b073-4c16-81d8-c34fcf3b1f01"
            " (Dataset landing page),"  # added a space
            "https://ieeexplore.ieee.org/document/7914752 (Scientific publication)"  # added space
        )
        data = md.get_related_information(mmd_yaml['related_information'], ncin)
        # Note: A landing page url created from the netcdf id and
        # naming_authority attributes overrides the references information
        self.assertEqual(
            data[0]['resource'],
            'https://data.fake.no/npp-viirs-mband-20201127134002-20201127135124')
        self.assertEqual(data[0]['type'], 'Dataset landing page')
        self.assertEqual(data[1]['resource'], 'https://ieeexplore.ieee.org/document/7914752')
        self.assertEqual(data[1]['type'], 'Scientific publication')

    def test_acdd_references_invalid_type(self):
        """ Test that error messages are created if the reference
        types are not in the MMD controlled vocabulary for related
        information types.
        """
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(self.fail_nc, check_only=True)
        ncin = Dataset(md.netcdf_file, "w", diskless=True)
        ncin.references = (
            "https://data.met.no/dataset/3f9974bf-b073-4c16-81d8-c34fcf3b1f01"
            "(kjhf),"
            "https://ieeexplore.ieee.org/document/7914752(Scientific publication)"
        )
        data = md.get_related_information(mmd_yaml['related_information'], ncin)
        self.assertEqual(data[1]['type'], 'Scientific publication')
        self.assertEqual(
            md.missing_attributes["errors"][0],
            'Reference types must follow a controlled vocabulary from'
            ' MMD (see https://htmlpreview.github.io/?https://github.'
            'com/metno/mmd/blob/master/doc/mmd-specification.html#'
            'related-information-types).')

    def test_acdd_references_invalid_url(self):
        """ Test that an error message is created if the reference
        uri is invalid.
        """
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(self.fail_nc, check_only=True)
        ncin = Dataset(md.netcdf_file, "w", diskless=True)
        ncin.references = (
            "https://data.invalid_domain.no/dataset/3f9974bf-b073-4c16-81d8-c34fcf3b1f01"
            "(Dataset landing page),"
            "https://ieeexplore.ieee__.org/document/7914752(Scientific publication)"
        )
        md.get_related_information(mmd_yaml['related_information'], ncin)
        self.assertEqual(
            md.missing_attributes["errors"][0],
            'references must contain valid uris')
        self.assertEqual(
            md.missing_attributes["errors"][1],
            'references must contain valid uris')

    def test_acdd_references_malformed(self):
        """ Test that an error message is created if the references
        are not valid uris.
        """
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(self.fail_nc, check_only=True)
        ncin = Dataset(md.netcdf_file, "w", diskless=True)
        ncin.references = "landing_page, paper"
        md.get_related_information(mmd_yaml['related_information'], ncin)
        self.assertEqual(
            md.missing_attributes["errors"][0],
            "references must be formed as <uri>(<type>).")


if __name__ == '__main__':
    unittest.main()
