"""
License:
     This file is part of the py-mmd-tools repository (https://github.com/metno/py-mmd-tools). py-mmd-tools is licensed under Apache License 2.0 (https://github.com/metno/py-mmd-tools/blob/master/LICENSE).
 """
import unittest
from unittest.mock import patch, Mock, DEFAULT

import os
import pathlib
import tempfile
import yaml
import datetime
import warnings

from filehash import FileHash
from pkg_resources import resource_string
from netCDF4 import Dataset

from py_mmd_tools.xml_utils import xsd_check
from py_mmd_tools.nc_to_mmd import Nc_to_mmd, nc_attrs_from_yaml

warnings.simplefilter("ignore", ResourceWarning)

class TestNCAttrsFromYaml(unittest.TestCase):

    def test_nc_attrs_from_yaml(self):
        adoc = nc_attrs_from_yaml()
        self.assertEqual(type(adoc), str)

class TestNC2MMD(unittest.TestCase):

    def setUp(self):
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
        self.reference_xsd = os.path.join(os.environ['MMD_PATH'], 'xsd/mmd.xsd')

    ##@patch('py_mmd_utils.nc_to_mmd.Nc_to_mmd.__init__')
    ##@patch('mmd_utils.nc_to_mmd.Nc_to_mmd.to_mmd')
    ##def test__main_with_defaults(self, mock_to_mmd, mock_init):
    ##    mock_init.return_value = None
    ##    self.assertTrue(mock_init.called)
    ##    self.assertTrue(mock_to_mmd.called)

    def test_geographic_extent_polygon(self):
        mmd_yaml = yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader)
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc')
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_geographic_extent_polygon(mmd_yaml['geographic_extent']['polygon'], ncin)
        self.assertEqual(value['srsName'], 'EPSG:4326')
        self.assertEqual(value['pos'][0], '69.00 3.79')

    def test_missing_geographic_extent(self):
        mmd_yaml = yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader)
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_missing_attrs.nc')
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_acdd_metadata(mmd_yaml['geographic_extent'], ncin, 'geographic_extent')
        self.assertEqual(value['rectangle']['north'], None)
        self.assertEqual(nc2mmd.missing_attributes['errors'][0], 'geospatial_lat_max is a required attribute')

    def test_missing_geographic_extent_but_provided_as_kwarg(self):
        mmd_yaml = yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader)
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_missing_attrs.nc')
        with self.assertRaises(AttributeError):
            nc2mmd.to_mmd(geographic_extent_rectangle={
                'geospatial_lat_max': 90,
                'geospatial_lat_min': -90,
                'geospatial_lon_min': -180,
                'geospatial_lon_max': 180
                })
        self.assertEqual(nc2mmd.metadata['geographic_extent']['rectangle']['north'], 90)

    def test_collection_not_set(self):
        mmd_yaml = yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'),
                Loader=yaml.FullLoader)
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_missing_attrs.nc')
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_acdd_metadata(mmd_yaml['collection'], ncin, 'collection')
        # nc files should normally not have a collection element, as this is
        # set during harvesting
        self.assertEqual(value, [])

    def test_collection_set(self):
        mmd_yaml = yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'),
                Loader=yaml.FullLoader)
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc')
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_acdd_metadata(mmd_yaml['collection'], ncin, 'collection')
        # nc files should normally not have a collection element, as this is
        # set during harvesting
        self.assertEqual(value, ['METNCS', 'SIOS', 'ADC'])

    def test_abstract(self):
        mmd_yaml = yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'),
                Loader=yaml.FullLoader)
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc')
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_abstracts(mmd_yaml['abstract'], ncin)
        self.assertEqual(type(value), list)
        self.assertTrue('lang' in value[0].keys())
        self.assertTrue('abstract' in value[0].keys())

    def test_title(self):
        mmd_yaml = yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'),
                Loader=yaml.FullLoader)
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc')
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_titles(mmd_yaml['title'], ncin)
        self.assertEqual(type(value), list)
        self.assertTrue('lang' in value[0].keys())
        self.assertTrue('title' in value[0].keys())

    def test_title_one_language_only(self):
        mmd_yaml = yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'),
                Loader=yaml.FullLoader)
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_id_missing.nc')
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_titles(mmd_yaml['title'], ncin)
        self.assertEqual(type(value), list)
        self.assertTrue('lang' in value[0].keys())
        self.assertTrue('title' in value[0].keys())

    def test_data_center(self):
        mmd_yaml = yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'),
                Loader=yaml.FullLoader)
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc')
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_data_centers(mmd_yaml['data_center'], ncin)
        self.assertEqual(type(value), list)
        self.assertEqual(value, [{
            'data_center_name': {
                'long_name': 'MET NORWAY',
                'short_name': 'MET NORWAY'},
            'data_center_url': 'met.no',
            }, {
                'data_center_name': {
                    'long_name': 'NASA',
                    'short_name': 'NASA'},
                'data_center_url': '',
                }])

    def test_data_access(self):
        # OBS: this is not relevant before we have added data access in nc_to_mmd.py
        mmd_yaml = yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'),
                Loader=yaml.FullLoader)
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc')
        ncin = Dataset(nc2mmd.netcdf_product)
        value = None
        self.assertEqual(value, None)

    def test_dataset_production_status(self):
        mmd_yaml = yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'),
                Loader=yaml.FullLoader)
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc')
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_acdd_metadata(mmd_yaml['dataset_production_status'], ncin, 'dataset_production_status')
        self.assertEqual(value, 'In Work')

    def test_alternate_identifier(self):
        mmd_yaml = yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'),
                Loader=yaml.FullLoader)
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc')
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_acdd_metadata(mmd_yaml['alternate_identifier'], ncin, 'alternate_identifier')
        self.assertEqual(value, [])

    def test_metadata_status_is_active(self):
        mmd_yaml = yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'),
                Loader=yaml.FullLoader)
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc')
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_acdd_metadata(mmd_yaml['metadata_status'], ncin, 'metadata_status')
        self.assertEqual(value, 'Active')

    def test_last_metadata_update(self):
        mmd_yaml = yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'),
                Loader=yaml.FullLoader)
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc')
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_metadata_updates(mmd_yaml['last_metadata_update'], ncin)
        self.assertEqual(value['update'][0]['datetime'], '2020-11-27T14:05:56Z')

    def test_use_defaults_for_personnel(self):
        mmd_yaml = yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader)
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_missing_attrs.nc')
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_personnel(mmd_yaml['personnel'], ncin)
        self.assertEqual(value[0]['role'], 'unknown')
        self.assertEqual(value[0]['name'], 'unknown')
        self.assertEqual(value[0]['email'], 'unknown')
        self.assertEqual(value[0]['organisation'], 'unknown')

    def test_missing_temporal_extent(self):
        mmd_yaml = yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader)
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_missing_attrs.nc')
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_temporal_extents(mmd_yaml['temporal_extent'], ncin)
        self.assertEqual(value, [])
        self.assertEqual(nc2mmd.missing_attributes['errors'][0], 'time_coverage_start is a required ACDD attribute')

    def test_missing_temporal_extent_but_start_provided_as_kwarg(self):
        mmd_yaml = yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader)
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_missing_attrs.nc')
        with self.assertRaises(AttributeError):
            nc2mmd.to_mmd(time_coverage_start='1850-01-01T00:00:00Z')
        self.assertEqual(nc2mmd.metadata['temporal_extent']['start_date'], '1850-01-01T00:00:00Z')

    def test_missing_temporal_extent_but_start_and_end_provided_as_kwargs(self):
        mmd_yaml = yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader)
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_missing_attrs.nc')
        with self.assertRaises(AttributeError):
            nc2mmd.to_mmd(time_coverage_start='1850-01-01T00:00:00Z', time_coverage_end='1950-01-01T00:00:00Z')
        self.assertEqual(nc2mmd.metadata['temporal_extent']['start_date'], '1850-01-01T00:00:00Z')
        self.assertEqual(nc2mmd.metadata['temporal_extent']['end_date'], '1950-01-01T00:00:00Z')

    def test_temporal_extent_two_startdates(self):
        mmd_yaml = yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader)
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_attrs_multiple.nc')
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_temporal_extents(mmd_yaml['temporal_extent'], ncin)
        self.assertEqual(value[0]['start_date'], '2020-11-27T13:40:02.019817Z')
        self.assertEqual(value[1]['start_date'], '2020-12-27T13:40:02.019817Z')
        self.assertEqual(value[2]['start_date'], '2021-01-27T13:40:02.019817Z')
        self.assertEqual(value[0]['end_date'], '2020-11-27T13:51:24.401505Z')
        self.assertEqual(value[1]['end_date'], '2020-12-27T13:51:24.019817Z')

    def test_temporal_extent(self):
        mmd_yaml = yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader)
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc')
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_temporal_extents(mmd_yaml['temporal_extent'], ncin)
        self.assertEqual(value[0]['start_date'], '2020-11-27T13:40:02.019817Z')
        self.assertEqual(value[0]['end_date'], '2020-11-27T13:51:24.401505Z')

    def test_personnel_multiple_mixed(self):
        mmd_yaml = yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader)
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_attrs_multiple_mixed_creator.nc')
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_personnel(mmd_yaml['personnel'], ncin)
        self.assertEqual(nc2mmd.missing_attributes['errors'][0], 'Attributes must have same number of entries')

    def test_personnel_multiple(self):
        mmd_yaml = yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader)
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_attrs_multiple.nc')
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_personnel(mmd_yaml['personnel'], ncin)
        self.assertEqual(value[0]['name'], 'Trygve')
        self.assertEqual(value[1]['name'], 'Nina')
        self.assertEqual(value[0]['email'], 'trygve@meti.no')
        self.assertEqual(value[1]['email'], 'post@met.no')
        self.assertEqual(value[0]['role'], 'Investigator')
        self.assertEqual(value[1]['role'], 'Technical contact')

    def test_personnel_multiple_creator_and_contributor(self):
        mmd_yaml = yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader)
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_attrs_multiple_and_contributor.nc')
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_personnel(mmd_yaml['personnel'], ncin)
        self.assertEqual(value[0]['name'], 'Trygve')
        self.assertEqual(value[1]['name'], 'Nina')
        self.assertEqual(value[2]['name'], 'Morten')
        self.assertEqual(value[0]['email'], 'trygve@meti.no')
        self.assertEqual(value[1]['email'], 'post@met.no')
        self.assertEqual(value[2]['email'], 'morten@met.no')
        self.assertEqual(value[0]['organisation'], 'MET NORWAY')
        self.assertEqual(value[1]['organisation'], 'MET NORWAY')
        self.assertEqual(value[2]['organisation'], 'MET NORWAY')
        self.assertEqual(value[0]['role'], 'Investigator')
        self.assertEqual(value[1]['role'], 'Technical contact')
        self.assertEqual(value[2]['role'], 'Investigator')

    def test_personnel_acdd_roles_not_list(self):
        mmd_yaml = yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader)
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_attrs_multiple_and_contributor.nc')
        ncin = Dataset(nc2mmd.netcdf_product)
        tmp = mmd_yaml['personnel']['name']['acdd'].pop(-1)
        mmd_yaml['personnel']['name']['acdd'] = mmd_yaml['personnel']['name']['acdd'][0]
        tmp = mmd_yaml['personnel']['role']['acdd'].pop(-1)
        mmd_yaml['personnel']['role']['acdd'] = mmd_yaml['personnel']['role']['acdd'][0]
        tmp = mmd_yaml['personnel']['email'].pop('acdd_ext')
        tmp = mmd_yaml['personnel']['organisation'].pop('acdd_ext')
        value = nc2mmd.get_personnel(mmd_yaml['personnel'], ncin)
        self.assertEqual(value[0]['name'], 'Trygve')
        self.assertEqual(value[1]['name'], 'Nina')
        self.assertEqual(value[0]['role'], 'Investigator')
        self.assertEqual(value[1]['role'], 'Technical contact')
        self.assertEqual(value[0]['email'], 'trygve@meti.no')
        self.assertEqual(value[1]['email'], 'post@met.no')
        self.assertEqual(value[0]['organisation'], 'MET NORWAY')
        self.assertEqual(value[1]['organisation'], 'MET NORWAY')

    def test_personnel(self):
        mmd_yaml = yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader)
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc')
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_personnel(mmd_yaml['personnel'], ncin)
        self.assertEqual(value[0]['email'], 'post@met.no')

    def test_iso_topic_category(self):
        mmd_yaml = yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader)
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc')
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_acdd_metadata(mmd_yaml['iso_topic_category'], ncin, 'iso_topic_category')
        self.assertEqual(value[0], 'climatologyMeteorologyAtmosphere')
        self.assertEqual(value[1], 'environment')
        self.assertEqual(value[2], 'oceans')

    def test_missing_vocabulary_platform_instrument_short_name(self):
        mmd_yaml = yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'), 
                Loader=yaml.FullLoader)
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_missing_keywords_vocab.nc')
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_platforms(mmd_yaml['platform'], ncin)
        self.assertEqual(value[0]['instrument']['short_name'], '')

    def test_missing_vocabulary_platform(self):
        mmd_yaml = yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'), 
                Loader=yaml.FullLoader)
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_missing_keywords_vocab.nc')
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_platforms(mmd_yaml['platform'], ncin)
        self.assertEqual(value[0]['resource'], '')

    def test_keywords_missing(self):
        mmd_yaml = yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'), 
                Loader=yaml.FullLoader)
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_fail.nc')
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_keywords(mmd_yaml['keywords'], ncin)
        self.assertEqual(nc2mmd.missing_attributes['errors'][0], 'keywords_vocabulary is a required ACDD attribute')
        self.assertEqual(nc2mmd.missing_attributes['errors'][1], 'keywords is a required ACDD attribute')

    def test_keywords_vocabulary_missing(self):
        mmd_yaml = yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'), 
                Loader=yaml.FullLoader)
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_missing_keywords_vocab.nc')
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_keywords(mmd_yaml['keywords'], ncin)
        self.assertEqual(nc2mmd.missing_attributes['errors'][0], 'keywords_vocabulary is a required ACDD attribute')

    def test_keywords(self):
        mmd_yaml = yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader)
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc')
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_keywords(mmd_yaml['keywords'], ncin)
        self.assertEqual(value[0]['vocabulary'], 'GCMD')
        self.assertEqual(value[0]['resource'], 'https://gcmdservices.gsfc.nasa.gov/static/kms/')
        self.assertEqual(value[0]['keyword'], ['Earth Science > Atmosphere > Atmospheric radiation'])
        self.assertEqual(value[1]['vocabulary'], 'GEMET')
        self.assertEqual(value[1]['resource'], 'http://inspire.ec.europa.eu/theme')
        self.assertEqual(value[1]['keyword'], ['Meteorological geographical features', 
            'Atmospheric conditions', 'Oceanographic geographical features'])

    def test_keywords_multiple(self):
        mmd_yaml = yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader)
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_attrs_multiple.nc')
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_keywords(mmd_yaml['keywords'], ncin)
        self.assertEqual(value[0]['vocabulary'], 'GCMD')
        self.assertEqual(value[0]['resource'], 'https://gcmdservices.gsfc.nasa.gov/static/kms/')
        self.assertEqual(value[0]['keyword'], ['Earth Science > Atmosphere > Atmospheric radiation', 
            'EARTH SCIENCE > BIOLOGICAL CLASSIFICATION > ANIMALS/VERTEBRATES'])

    def test_platforms(self):
        mmd_yaml = yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader)
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc')
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_platforms(mmd_yaml['platform'], ncin)
        self.assertEqual(value[0]['long_name'], 'Suomi National Polar-orbiting Partnership')
        self.assertEqual(value[0]['instrument']['long_name'], 'Visible/Infrared Imager Radiometer Suite')

    def test_platform_with_gcmd_vocabulary(self):
        mmd_yaml = yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader)
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_gcmd_platform.nc')
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_platforms(mmd_yaml['platform'], ncin)
        self.assertEqual(value[0]['short_name'], 'Sentinel-1B')
        self.assertEqual(value[0]['long_name'], 'Sentinel-1B')
        self.assertEqual(value[0]['instrument']['long_name'], 'Synthetic Aperture Radar')

    def test_projects(self):
        mmd_yaml = yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader)
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc')
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_projects(mmd_yaml['project'], ncin)
        self.assertEqual(value[0]['long_name'], 'Govermental core service')

    def test_dataset_citation_missing_attrs(self):
        mmd_yaml = yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader)
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_missing_keywords_vocab.nc')
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_dataset_citations(mmd_yaml['dataset_citation'], ncin)
        self.assertEqual(value[0]['url'], '')
        self.assertEqual(value[0]['other'], '')

    def test_check_only(self):
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc', check_only=True)
        req_ok, msg = nc2mmd.to_mmd()
        self.assertTrue(req_ok)
        self.assertEqual(msg,'')

    def test_dataset_citation(self):
        mmd_yaml = yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader)
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc')
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_dataset_citations(mmd_yaml['dataset_citation'], ncin)
        self.assertEqual(value[0]['title'], 'Direct Broadcast data processed in satellite swath to L1C.')

    @patch('py_mmd_tools.nc_to_mmd.Dataset')
    def test_oserror_opendap(self, mock_nc_dataset):
        mock_nc_dataset.side_effect = OSError
        fn = 'http://nbstds.met.no/thredds/dodsC/NBS/S1A/2021/01/31/IW/S1A_IW_GRDH_1SDV_20210131T172816_20210131T172841_036385_04452D_505F.nc'
        nc2mmd = Nc_to_mmd(fn)
        try:
            nc2mmd.to_mmd()
        except:
            xx=1
        mock_nc_dataset.assert_called_with(fn+'#fillmismatch')

    def test_get_data_access_dict_with_wms(self):
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc')
        ncin = Dataset(nc2mmd.netcdf_product)
        nc2mmd.netcdf_product = 'https://thredds.met.no/thredds/dodsC/arcticdata/S2S_drift_TCD/SIDRIFT_S2S_SH/2019/07/31/' + nc2mmd.netcdf_product
        data = nc2mmd.get_data_access_dict(ncin, add_wms_data_access=True)
        self.assertEqual(data[0]['type'], 'OPeNDAP')
        self.assertEqual(data[1]['type'], 'OGC WMS')
        self.assertEqual(data[2]['type'], 'HTTP')

    def test_get_data_access_dict(self):
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc')
        ncin = Dataset(nc2mmd.netcdf_product)
        nc2mmd.netcdf_product = 'https://thredds.met.no/thredds/dodsC/arcticdata/S2S_drift_TCD/SIDRIFT_S2S_SH/2019/07/31/' + nc2mmd.netcdf_product
        data = nc2mmd.get_data_access_dict(ncin)
        self.assertEqual(data[0]['type'], 'OPeNDAP')
        self.assertEqual(data[1]['type'], 'HTTP')

    def test_related_dataset(self):
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_id_missing.nc')
        ncin = Dataset('tests/data/reference_nc_id_missing.nc')
        mmd_yaml = yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader)
        data = nc2mmd.get_related_dataset(mmd_yaml['related_dataset'], ncin)
        self.assertEqual(data[0]['id'], 'b7cb7934-77ca-4439-812e-f560df3fe7eb')
        self.assertEqual(data[0]['relation_type'], 'parent')

    def test_missing_id(self):
        mmd_yaml = yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader)
        # nc file is missing the id attribute
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_missing_keywords_vocab.nc')
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_metadata_identifier(mmd_yaml['metadata_identifier'], ncin)
        self.assertTrue(Nc_to_mmd.is_valid_uuid(value))

    def test_create_do_not_require_uuid(self):
        mmd_yaml = yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader)
        # The id attribute is not a uuid
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_fail.nc')
        ncin = Dataset(nc2mmd.netcdf_product)
        id = ncin.getncattr('id')
        value = nc2mmd.get_metadata_identifier(mmd_yaml['metadata_identifier'], ncin, 
                require_uuid=False)
        self.assertFalse(Nc_to_mmd.is_valid_uuid(value))
        self.assertEqual(id, value)

    def test_create_new_id_if_accd_id_is_invalid(self):
        mmd_yaml = yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader)
        # The id attribute is not a uuid
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_fail.nc')
        ncin = Dataset(nc2mmd.netcdf_product)
        id = ncin.getncattr('id')
        value = nc2mmd.get_metadata_identifier(mmd_yaml['metadata_identifier'], ncin)
        self.assertTrue(Nc_to_mmd.is_valid_uuid(value))
        self.assertNotEqual(id, value)

    def test_get_correct_id_from_ncfile(self):
        mmd_yaml = yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader)
        # The id attribute is a uuid
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc')
        ncin = Dataset(nc2mmd.netcdf_product)
        id = ncin.getncattr('id')
        value = nc2mmd.get_metadata_identifier(mmd_yaml['metadata_identifier'], ncin)
        self.assertTrue(Nc_to_mmd.is_valid_uuid(value))
        self.assertEqual(id, value)

    def test__to_mmd__missing_id(self):
        tested = tempfile.mkstemp()[1]
        # nc file is missing the id attribute
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_id_missing.nc', output_file=tested)
        nc2mmd.to_mmd()
        self.assertEqual(nc2mmd.missing_attributes['warnings'][0], 'id ACDD attribute is missing - created metadata_identifier MMD element as uuid.')
        self.assertEqual(nc2mmd.missing_attributes['warnings'][1], 'Using default value Active for metadata_status')
        self.assertEqual(nc2mmd.missing_attributes['errors'], [])
        self.assertTrue(Nc_to_mmd.is_valid_uuid(nc2mmd.metadata['metadata_identifier']))

    def test__to_mmd__create_do_not_require_uuid(self):
        tested = tempfile.mkstemp()[1]
        # The id attribute is not a uuid
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_id_not_uuid.nc', output_file=tested)
        nc2mmd.to_mmd(require_uuid=False)
        ncin = Dataset(nc2mmd.netcdf_product)
        id = ncin.getncattr('id')
        self.assertFalse(Nc_to_mmd.is_valid_uuid(nc2mmd.metadata['metadata_identifier']))
        self.assertEqual(id, nc2mmd.metadata['metadata_identifier'])

    def test__to_mmd__create_new_id_if_accd_id_is_invalid(self):
        tested = tempfile.mkstemp()[1]
        # The id attribute is not a uuid
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_id_not_uuid.nc', output_file=tested)
        nc2mmd.to_mmd()
        self.assertEqual(nc2mmd.missing_attributes['warnings'][0], 'id ACDD attribute is not unique - created metadata_identifier MMD element as uuid.')
        self.assertEqual(nc2mmd.missing_attributes['warnings'][1], 'Using default value Active for metadata_status')
        self.assertEqual(nc2mmd.missing_attributes['errors'], [])
        self.assertTrue(Nc_to_mmd.is_valid_uuid(nc2mmd.metadata['metadata_identifier']))
        ncin = Dataset(nc2mmd.netcdf_product)
        id = ncin.getncattr('id')
        self.assertNotEqual(id, nc2mmd.metadata['metadata_identifier'])

    def test__to_mmd__get_correct_id_from_ncfile(self):
        tested = tempfile.mkstemp()[1]
        # The id attribute is a uuid
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc', output_file=tested)
        nc2mmd.to_mmd()
        self.assertEqual(nc2mmd.missing_attributes['warnings'][0], 'Using default value Active for metadata_status')
        self.assertEqual(nc2mmd.missing_attributes['errors'], [])

    def test_create_mmd_1(self):
        tested = tempfile.mkstemp()[1]
        md = Nc_to_mmd(self.reference_nc, output_file=tested)
        md.to_mmd()
        valid = xsd_check(tested, self.reference_xsd)
        self.assertTrue(valid[0])

    def test_get_acdd_metadata_sets_warning_msg(self):
        mmd_yaml = yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader)
        md = Nc_to_mmd(self.fail_nc)
        ncin = Dataset(md.netcdf_product)
        value = md.get_acdd_metadata(mmd_yaml['metadata_status'], ncin, 'metadata_status')
        self.assertEqual(md.missing_attributes['warnings'][0], 'Using default value Active for metadata_status')

    def test_create_mmd_2(self):
        self.maxDiff = None
        tested = tempfile.mkstemp()[1]
        md = Nc_to_mmd(self.fail_nc, output_file=tested)
        with self.assertRaises(AttributeError):
            md.to_mmd()

    def test_all_valid_nc_files_passing(self):
        valid_files = [
                os.path.join(pathlib.Path.cwd(), 'tests/data/reference_nc.nc'),
                os.path.join(pathlib.Path.cwd(), 'tests/data/reference_nc_id_missing.nc'),
                os.path.join(pathlib.Path.cwd(), 'tests/data/reference_nc_id_not_uuid.nc'),
                os.path.join(pathlib.Path.cwd(), 'tests/data/reference_nc_attrs_multiple.nc'),
            ]
        for file in valid_files:
            tested = tempfile.mkstemp()[1]
            md = Nc_to_mmd(file, output_file=tested)
            md.to_mmd()
            valid = xsd_check(tested, self.reference_xsd)
            self.assertTrue(valid[0], msg='%s'%valid[1])

    def test_create_mmd_missing_publisher_url(self):
        mmd_yaml = yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'), 
                Loader=yaml.FullLoader)
        md = Nc_to_mmd(self.fail_nc)
        ncin = Dataset(md.netcdf_product)
        value = md.get_data_centers(mmd_yaml['data_center'], ncin)
        self.assertEqual(value, [{
            'data_center_name': {
                'short_name': 'MET NORWAY',
                'long_name': 'MET NORWAY'},
            'data_center_url': ''}])

    def test_create_mmd_missing_update_times(self):
        mmd_yaml = yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'), 
                Loader=yaml.FullLoader)
        md = Nc_to_mmd(self.fail_nc)
        ncin = Dataset(md.netcdf_product)
        value = md.get_metadata_updates(mmd_yaml['last_metadata_update'], ncin)
        self.assertEqual(md.missing_attributes['errors'][0],
                'ACDD attribute date_created or date_metadata_modified is required')

    def test_create_mmd_missing_abstract(self):
        mmd_yaml = yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'), 
                Loader=yaml.FullLoader)
        md = Nc_to_mmd(self.fail_nc)
        ncin = Dataset(md.netcdf_product)
        value = md.get_abstracts(mmd_yaml['abstract'], ncin)
        self.assertEqual(md.missing_attributes['errors'][0],
                'summary is a required ACDD attribute')

    def test_publication_date(self):
        format = '%Y-%m-%d'
        mmd_yaml = yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader)
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc')
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_dataset_citations(mmd_yaml['dataset_citation'], ncin)
        dt = datetime.datetime.strptime(value[0]['publication_date'], format)
        self.assertEqual(dt, datetime.datetime(2020, 11, 27, 0, 0))
        self.assertEqual(value[0]['title'], 'Direct Broadcast data processed in satellite swath to L1C.')

    def test_checksum(self):
        tested = tempfile.mkstemp()[1]
        fn = 'tests/data/reference_nc.nc'
        nc2mmd = Nc_to_mmd(fn, check_only=True)
        nc2mmd.to_mmd()
        checksum = nc2mmd.metadata['storage_information']['checksum']
        with open(tested, 'w') as tt:
            tt.write('%s *%s'%(checksum, fn))
        md5hasher = FileHash('md5')
        self.assertTrue(md5hasher.verify_checksums(tested)[0].hashes_match)

    def test_file_on_thredds(self):
        fn = 'https://thredds.met.no/thredds/dodsC/remotesensingsatellite/polar-swath/2020/12/01/metopb-avhrr-20201201155244-20201201160030.nc'
        nc2mmd = Nc_to_mmd(fn, check_only=True)
        try:
            nc2mmd.to_mmd()
        except OSError as e:
            warnings.warn('%s is not available' %fn)
            self.assertEqual(e.strerror, 'NetCDF: file not found')
        else:
            self.assertEqual(nc2mmd.metadata['storage_information']['file_name'], 'metopb-avhrr-20201201155244-20201201160030.nc')

    def test_file_on_faked_thredds(self):
        fn = 'tests/data/dodsC/reference_nc.nc'
        nc2mmd = Nc_to_mmd(fn, check_only=True)
        nc2mmd.to_mmd(netcdf_local_path=fn)
        self.assertEqual(nc2mmd.metadata['storage_information']['file_name'], 'reference_nc.nc')

if __name__ == '__main__':
    unittest.main()
