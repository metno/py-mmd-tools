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
import datetime
import warnings
import unittest

from unittest.mock import patch
from filehash import FileHash
from lxml import etree
from netCDF4 import Dataset
from pkg_resources import resource_string

from py_mmd_tools.nc_to_mmd import Nc_to_mmd, nc_attrs_from_yaml

warnings.simplefilter("ignore", ResourceWarning)


class TestNCAttrsFromYaml(unittest.TestCase):

    def test_nc_attrs_from_yaml(self):
        """ToDo: Add docstring"""
        adoc = nc_attrs_from_yaml()
        self.assertEqual(type(adoc), str)


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

    def test_init_raises_error(self):
        """Nc_to_mmd.__init__ should raise error if check_only=False,
        but output_file is None. Test that this is the case.
        """
        with self.assertRaises(ValueError):
            Nc_to_mmd('tests/data/reference_nc.nc', output_file=None, check_only=False)

    def test_date_created_type__not_present(self):
        """ToDo: Add docstring"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc', check_only=True)
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_acdd_metadata(
            mmd_yaml['last_metadata_update']['update']['type'],
            ncin, 'date_created_type'
        )
        self.assertEqual(value, 'Created')

    def test_geographic_extent_polygon(self):
        """ToDo: Add docstring"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc', check_only=True)
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_geographic_extent_polygon(
            mmd_yaml['geographic_extent']['polygon'], ncin
        )
        self.assertEqual(value['srsName'], 'EPSG:4326')
        self.assertEqual(value['pos'][0], '69.0000 3.7900')

    def test_missing_geographic_extent(self):
        """ToDo: Add docstring"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_missing_attrs.nc', check_only=True)
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_acdd_metadata(mmd_yaml['geographic_extent'], ncin, 'geographic_extent')
        self.assertEqual(value['rectangle']['north'], None)
        self.assertEqual(
            nc2mmd.missing_attributes['errors'][0],
            'geospatial_lat_max is a required attribute'
        )

    def test_missing_geographic_extent_but_provided_as_kwarg(self):
        """ToDo: Add docstring"""
        yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_missing_attrs.nc', check_only=True)
        with self.assertRaises(AttributeError):
            nc2mmd.to_mmd(geographic_extent_rectangle={
                'geospatial_lat_max': 90,
                'geospatial_lat_min': -90,
                'geospatial_lon_min': -180,
                'geospatial_lon_max': 180
            })
        self.assertEqual(nc2mmd.metadata['geographic_extent']['rectangle']['north'], 90)

    def test_collection_not_set(self):
        """ToDo: Add docstring"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_missing_attrs.nc', check_only=True)
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_acdd_metadata(mmd_yaml['collection'], ncin, 'collection')
        # nc files should normally not have a collection element, as this is
        # set during harvesting
        self.assertEqual(value, None)

    def test_collection_set(self):
        """ToDo: Add docstring"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc', check_only=True)
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_acdd_metadata(mmd_yaml['collection'], ncin, 'collection')
        # nc files should normally not have a collection element, as this is
        # set during harvesting
        self.assertEqual(value, ['METNCS', 'SIOS', 'ADC'])

    def test_abstract(self):
        """ToDo: Add docstring"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc', check_only=True)
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_abstracts(mmd_yaml['abstract'], ncin)
        self.assertEqual(type(value), list)
        self.assertTrue('lang' in value[0].keys())
        self.assertTrue('abstract' in value[0].keys())

    def test_title(self):
        """ToDo: Add docstring"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc', check_only=True)
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_titles(mmd_yaml['title'], ncin)
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
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_id_missing.nc', check_only=True)
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_titles(mmd_yaml['title'], ncin)
        self.assertEqual(type(value), list)
        self.assertTrue('lang' in value[0].keys())
        self.assertTrue('title' in value[0].keys())

    def test_data_center(self):
        """Test get_data_centers function"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc', check_only=True)
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_data_centers(mmd_yaml['data_center'], ncin)
        self.assertEqual(type(value), list)
        self.assertEqual(value, [{
            'data_center_name': {
                'long_name': 'Norwegian Meteorological Institute',
                'short_name': 'NO/MET'
            },
            'data_center_url': 'met.no',
        }])

    def test_data_access(self):
        """ToDo: Add docstring"""
        yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader)
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc', check_only=True)
        Dataset(nc2mmd.netcdf_product)
        value = None
        self.assertEqual(value, None)

    def test_dataset_production_status(self):
        """ToDo: Add docstring"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc', check_only=True)
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_acdd_metadata(
            mmd_yaml['dataset_production_status'], ncin, 'dataset_production_status'
        )
        self.assertEqual(value, 'In Work')

    def test_alternate_identifier_missing(self):
        """Test that MMD alternate_identifier is not added when it does
        not exist in nc-file.
        """
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc', check_only=True)
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_acdd_metadata(
            mmd_yaml['alternate_identifier'], ncin, 'alternate_identifier'
        )
        self.assertEqual(value, None)

    def test_alternate_identifier(self):
        """Test that MMD alternate_identifier is not equal to the one
        provided in the nc-file.
        """
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_with_altID.nc', check_only=True)
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_acdd_metadata(
            mmd_yaml['alternate_identifier'], ncin, 'alternate_identifier'
        )
        self.assertEqual(value[0], 'dummy_id_no1')

    def test_metadata_status_is_active(self):
        """ToDo: Add docstring"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc', check_only=True)
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_acdd_metadata(mmd_yaml['metadata_status'], ncin, 'metadata_status')
        self.assertEqual(value, 'Active')

    def test_last_metadata_update(self):
        """ToDo: Add docstring"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc', check_only=True)
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_metadata_updates(mmd_yaml['last_metadata_update'], ncin)
        self.assertEqual(value['update'][0]['datetime'], '2020-11-27T14:05:56Z')

    def test_use_defaults_for_personnel(self):
        """ToDo: Add docstring"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_missing_attrs.nc', check_only=True)
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_personnel(mmd_yaml['personnel'], ncin)
        self.assertEqual(value[0]['role'], 'Investigator')
        self.assertEqual(value[0]['name'], 'Not available')
        self.assertEqual(value[0]['email'], 'Not available')
        self.assertEqual(value[0]['organisation'], 'Not available')

    def test_missing_temporal_extent(self):
        """ToDo: Add docstring"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_missing_attrs.nc', check_only=True)
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_temporal_extents(mmd_yaml['temporal_extent'], ncin)
        self.assertEqual(value, [])
        self.assertEqual(
            nc2mmd.missing_attributes['errors'][0],
            'time_coverage_start is a required ACDD attribute'
        )

    def test_missing_temporal_extent_but_start_provided_as_kwarg(self):
        """ToDo: Add docstring"""
        yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_missing_attrs.nc', check_only=True)
        with self.assertRaises(AttributeError):
            nc2mmd.to_mmd(time_coverage_start='1850-01-01T00:00:00Z')
        self.assertEqual(nc2mmd.metadata['temporal_extent']['start_date'], '1850-01-01T00:00:00Z')

    def test_missing_temporal_extent_but_start_and_end_provided_as_kwargs(self):
        """ToDo: Add docstring"""
        yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader)
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_missing_attrs.nc', check_only=True)
        with self.assertRaises(AttributeError):
            nc2mmd.to_mmd(
                time_coverage_start='1850-01-01T00:00:00Z',
                time_coverage_end='1950-01-01T00:00:00Z'
            )
        self.assertEqual(nc2mmd.metadata['temporal_extent']['start_date'], '1850-01-01T00:00:00Z')
        self.assertEqual(nc2mmd.metadata['temporal_extent']['end_date'], '1950-01-01T00:00:00Z')

    def test_temporal_extent_two_startdates(self):
        """ToDo: Add docstring"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_attrs_multiple.nc', check_only=True)
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_temporal_extents(mmd_yaml['temporal_extent'], ncin)
        self.assertEqual(value[0]['start_date'], '2020-11-27T13:40:02.019817Z')
        self.assertEqual(value[1]['start_date'], '2020-12-27T13:40:02.019817Z')
        self.assertEqual(value[2]['start_date'], '2021-01-27T13:40:02.019817Z')
        self.assertEqual(value[0]['end_date'], '2020-11-27T13:51:24.401505Z')
        self.assertEqual(value[1]['end_date'], '2020-12-27T13:51:24.019817Z')

    def test_temporal_extent(self):
        """ToDo: Add docstring"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc', check_only=True)
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_temporal_extents(mmd_yaml['temporal_extent'], ncin)
        self.assertEqual(value[0]['start_date'], '2020-11-27T13:40:02.019817Z')
        self.assertEqual(value[0]['end_date'], '2020-11-27T13:51:24.401505Z')

    def test_personnel_multiple_mixed(self):
        """ToDo: Add docstring"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        nc2mmd = Nc_to_mmd(
            'tests/data/reference_nc_attrs_multiple_mixed_creator.nc',
            check_only=True
        )
        ncin = Dataset(nc2mmd.netcdf_product)
        nc2mmd.get_personnel(mmd_yaml['personnel'], ncin)
        self.assertEqual(
            nc2mmd.missing_attributes['errors'][0],
            'Attributes must have same number of entries'
        )

    def test_personnel_multiple(self):
        """ToDo: Add docstring"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_attrs_multiple.nc', check_only=True)
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_personnel(mmd_yaml['personnel'], ncin)
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
        nc2mmd = Nc_to_mmd(
            'tests/data/reference_nc_attrs_multiple_and_contributor.nc',
            check_only=True
        )
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_personnel(mmd_yaml['personnel'], ncin)
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
        nc2mmd = Nc_to_mmd(
            'tests/data/reference_nc_attrs_multiple_and_contributor.nc',
            check_only=True
        )
        ncin = Dataset(nc2mmd.netcdf_product)
        mmd_yaml['personnel']['name']['acdd'].pop(-1)
        mmd_yaml['personnel']['name']['acdd'] = mmd_yaml['personnel']['name']['acdd'][0]
        mmd_yaml['personnel']['role']['acdd'].pop(-1)
        mmd_yaml['personnel']['role']['acdd'] = mmd_yaml['personnel']['role']['acdd'][0]
        mmd_yaml['personnel']['email'].pop('acdd_ext')
        mmd_yaml['personnel']['organisation'].pop('acdd_ext')
        value = nc2mmd.get_personnel(mmd_yaml['personnel'], ncin)
        self.assertEqual(value[0]['name'], 'Trygve')
        self.assertEqual(value[1]['name'], 'Nina')
        self.assertEqual(value[0]['role'], 'Investigator')
        self.assertEqual(value[1]['role'], 'Technical contact')
        self.assertEqual(value[0]['email'], 'trygve@meti.no')
        self.assertEqual(value[1]['email'], 'post@met.no')
        self.assertEqual(value[0]['organisation'], 'Norwegian Meteorological Institute')
        self.assertEqual(value[1]['organisation'], 'Norwegian Meteorological Institute')

    def test_personnel(self):
        """Test reading of personnel from nc file into MMD"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc', check_only=True)
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_personnel(mmd_yaml['personnel'], ncin)
        self.assertEqual(value[0]['email'], 'post@met.no')

    def test_iso_topic_category(self):
        """ToDo: Add docstring"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc', check_only=True)
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_acdd_metadata(
            mmd_yaml['iso_topic_category'], ncin, 'iso_topic_category'
        )
        self.assertEqual(value[0], 'climatologyMeteorologyAtmosphere')
        self.assertEqual(value[1], 'environment')
        self.assertEqual(value[2], 'oceans')

    def test_missing_vocabulary_platform_instrument_short_name(self):
        """ToDo: Add docstring"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_missing_keywords_vocab.nc', check_only=True)
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_platforms(mmd_yaml['platform'], ncin)
        self.assertEqual(value[0]['instrument']['short_name'], '')

    def test_missing_vocabulary_platform(self):
        """ToDo: Add docstring"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_missing_keywords_vocab.nc', check_only=True)
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_platforms(mmd_yaml['platform'], ncin)
        self.assertEqual(value[0]['resource'], '')

    def test_keywords_missing(self):
        """ToDo: Add docstring"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_fail.nc', check_only=True)
        ncin = Dataset(nc2mmd.netcdf_product)
        nc2mmd.get_keywords(mmd_yaml['keywords'], ncin)
        self.assertEqual(
            nc2mmd.missing_attributes['errors'][0],
            'keywords_vocabulary is a required ACDD attribute'
        )
        self.assertEqual(
            nc2mmd.missing_attributes['errors'][1],
            'keywords is a required ACDD attribute'
        )

    def test_keywords_vocabulary_missing(self):
        """ToDo: Add docstring"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_missing_keywords_vocab.nc', check_only=True)
        ncin = Dataset(nc2mmd.netcdf_product)
        nc2mmd.get_keywords(mmd_yaml['keywords'], ncin)
        self.assertEqual(
            nc2mmd.missing_attributes['errors'][0],
            'keywords_vocabulary is a required ACDD attribute'
        )

    def test_keywords(self):
        """ToDo: Add docstring"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc', check_only=True)
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_keywords(mmd_yaml['keywords'], ncin)
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

    def test_keywords_multiple(self):
        """ToDo: Add docstring"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_attrs_multiple.nc', check_only=True)
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_keywords(mmd_yaml['keywords'], ncin)
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
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc', check_only=True)
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_platforms(mmd_yaml['platform'], ncin)
        self.assertEqual(
            value[0]['long_name'],
            'Suomi National Polar-orbiting Partnership'
        )
        self.assertEqual(
            value[0]['instrument']['long_name'],
            'Visible/Infrared Imager Radiometer Suite'
        )

    def test_platform_with_gcmd_vocabulary(self):
        """ToDo: Add docstring"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_gcmd_platform.nc', check_only=True)
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_platforms(mmd_yaml['platform'], ncin)
        self.assertEqual(value[0]['short_name'], 'Sentinel-1B')
        self.assertEqual(value[0]['long_name'], 'Sentinel-1B')
        self.assertEqual(value[0]['instrument']['long_name'], 'Synthetic Aperture Radar')

    def test_projects(self):
        """Test getting project information from nc-file"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc', check_only=True)
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_projects(mmd_yaml['project'], ncin)
        self.assertEqual(value[0]['long_name'], 'MET Norway core services')

    def test_dataset_citation_missing_attrs(self):
        """Test that missing url and other is accepted"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_missing_keywords_vocab.nc', check_only=True)
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_dataset_citations(mmd_yaml['dataset_citation'], ncin)
        self.assertEqual(value[0]['url'], '')
        self.assertEqual(value[0]['other'], '')

    def test_check_only(self):
        """Run netCDF attributes to MMD translation with check_only
        flag. Also make sure that the warning about using default
        value 'Active' for the MMD metadata_status field is disabled.
        """
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc', check_only=True)
        req_ok, msg = nc2mmd.to_mmd()
        self.assertFalse(nc2mmd.missing_attributes['warnings'])
        self.assertTrue(req_ok)
        self.assertEqual(msg, '')

    def test_dataset_citation(self):
        """ToDo: Add docstring"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc', check_only=True)
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_dataset_citations(mmd_yaml['dataset_citation'], ncin)
        self.assertEqual(
            value[0]['title'],
            'Direct Broadcast data processed in satellite swath to L1C.'
        )

    @patch('py_mmd_tools.nc_to_mmd.Dataset')
    def test_oserror_opendap(self, mock_nc_dataset):
        """ToDo: Add docstring"""
        mock_nc_dataset.side_effect = OSError
        fn = (
            'http://nbstds.met.no/thredds/dodsC/NBS/S1A/2021/01/31/IW/'
            'S1A_IW_GRDH_1SDV_20210131T172816_20210131T172841_036385_04452D_505F.nc'
        )
        nc2mmd = Nc_to_mmd(fn, check_only=True)
        try:
            nc2mmd.to_mmd()
        except Exception:
            pass
        mock_nc_dataset.assert_called_with(fn+'#fillmismatch')

    def test_get_data_access_dict_with_wms(self):
        """ToDo: Add docstring"""
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc', check_only=True)
        ncin = Dataset(nc2mmd.netcdf_product)
        nc2mmd.netcdf_product = (
            'https://thredds.met.no/thredds/dodsC/arcticdata/'
            'S2S_drift_TCD/SIDRIFT_S2S_SH/2019/07/31/'
        ) + nc2mmd.netcdf_product
        data = nc2mmd.get_data_access_dict(ncin, add_wms_data_access=True)
        self.assertEqual(data[0]['type'], 'OPeNDAP')
        self.assertEqual(data[1]['type'], 'OGC WMS')
        self.assertEqual(data[2]['type'], 'HTTP')

    def test_get_data_access_dict(self):
        """ToDo: Add docstring"""
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc', check_only=True)
        ncin = Dataset(nc2mmd.netcdf_product)
        nc2mmd.netcdf_product = (
            'https://thredds.met.no/thredds/dodsC/arcticdata/'
            'S2S_drift_TCD/SIDRIFT_S2S_SH/2019/07/31/'
        ) + nc2mmd.netcdf_product
        data = nc2mmd.get_data_access_dict(ncin)
        self.assertEqual(data[0]['type'], 'OPeNDAP')
        self.assertEqual(data[1]['type'], 'HTTP')

    def test_related_dataset(self):
        """ToDo: Add docstring"""
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_id_missing.nc', check_only=True)
        ncin = Dataset('tests/data/reference_nc_id_missing.nc')
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        data = nc2mmd.get_related_dataset(mmd_yaml['related_dataset'], ncin)
        self.assertEqual(data[0]['id'], 'b7cb7934-77ca-4439-812e-f560df3fe7eb')
        self.assertEqual(data[0]['relation_type'], 'parent')

    def test_create_do_not_require_uuid(self):
        """Test that we can create an MMD file even if a uuid is missing."""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        # The id attribute is not a uuid
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_fail.nc', check_only=True)
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_metadata_identifier(
            mmd_yaml['metadata_identifier'], ncin
        )
        self.assertFalse(Nc_to_mmd.is_valid_uuid(value))
        self.assertEqual('', value)

    def test_get_correct_id_from_ncfile(self):
        """ToDo: Add docstring"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        # The id attribute is a uuid
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc', check_only=True)
        ncin = Dataset(nc2mmd.netcdf_product)
        id = ncin.getncattr('id')
        value = nc2mmd.get_metadata_identifier(mmd_yaml['metadata_identifier'], ncin)
        self.assertTrue(Nc_to_mmd.is_valid_uuid(value))
        self.assertEqual(id, value)

    def test__to_mmd__missing_id(self):
        """Test that the correct warnings are issued for missing id
        attribute and missing metadata status.
        """
        tested = tempfile.mkstemp()[1]
        # nc file is missing the id attribute
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_id_missing.nc', output_file=tested)
        nc2mmd.to_mmd()
        ncin = Dataset(nc2mmd.netcdf_product)
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        value = nc2mmd.get_metadata_identifier(mmd_yaml['metadata_identifier'], ncin)
        self.assertEqual(
            nc2mmd.missing_attributes['warnings'][0], (
                'id is a required attribute. The MMD xml file will not validate unless the MMD '
                'metadata_identifier is added.'
            )
        )
        self.assertEqual(nc2mmd.missing_attributes['errors'], [])
        self.assertFalse(Nc_to_mmd.is_valid_uuid(nc2mmd.metadata['metadata_identifier']))
        self.assertEqual('', value)

    def test__to_mmd__create_do_not_require_valid_uuid(self):
        """Test that we can create an MMD file even if the netcdf id
        attribute is not a valid uuid.
        """
        tested = tempfile.mkstemp()[1]
        # The id attribute is not a uuid
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_id_not_uuid.nc', output_file=tested)
        nc2mmd.to_mmd(require_uuid=False)
        self.assertFalse(Nc_to_mmd.is_valid_uuid(nc2mmd.metadata['metadata_identifier']))
        self.assertEqual('', nc2mmd.metadata['metadata_identifier'])

    def test__to_mmd__warn_if_accd_id_is_invalid(self):
        """Test that metadata_identifier is set to an empty string, and
        that a warning is issued if the ACDD id is not a valid uuid.
        """
        tested = tempfile.mkstemp()[1]
        # The id attribute is not a uuid
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_id_not_uuid.nc', output_file=tested)
        nc2mmd.to_mmd()
        self.assertEqual(
            nc2mmd.missing_attributes['warnings'][0], (
                'id ACDD attribute is not valid.The MMD xml file will not validate unless '
                'the MMD metadata_identifier is replaced.'
            )
        )
        self.assertEqual(nc2mmd.missing_attributes['errors'], [])
        self.assertFalse(Nc_to_mmd.is_valid_uuid(nc2mmd.metadata['metadata_identifier']))
        ncin = Dataset(nc2mmd.netcdf_product)
        id = ncin.getncattr('id')
        self.assertNotEqual(id, nc2mmd.metadata['metadata_identifier'])
        self.assertEqual('', nc2mmd.metadata['metadata_identifier'])

    def test__to_mmd__get_correct_id_from_ncfile(self):
        """Test that the id attribute in the netcdf file is valid, and
        used in the MMD xml file.
        """
        tested = tempfile.mkstemp()[1]
        # The id attribute is a uuid
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc', output_file=tested)
        nc2mmd.to_mmd()
        ncin = Dataset(nc2mmd.netcdf_product)
        id = ncin.getncattr('id')
        self.assertEqual(nc2mmd.missing_attributes['errors'], [])
        self.assertEqual(id, nc2mmd.metadata['metadata_identifier'])

    def test_create_mmd_1(self):
        """ToDo: Add docstring"""
        tested = tempfile.mkstemp()[1]
        md = Nc_to_mmd(self.reference_nc, output_file=tested)
        md.to_mmd()
        xsd_obj = etree.XMLSchema(etree.parse(self.reference_xsd))
        xml_doc = etree.ElementTree(file=tested)
        valid = xsd_obj.validate(xml_doc)
        self.assertTrue(valid)

    def test_get_acdd_metadata_sets_warning_msg(self):
        """Check that a warning is issued by the get_acdd_metadata
        function if a default value is used for a required element.
        """
        md = Nc_to_mmd('tests/data/reference_nc_id_missing.nc', check_only=True)
        ncin = Dataset(md.netcdf_product)
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
        tested = tempfile.mkstemp()[1]
        md = Nc_to_mmd(self.fail_nc, output_file=tested)
        with self.assertRaises(AttributeError):
            md.to_mmd()

    def test_all_valid_nc_files_passing(self):
        """ToDo: Add docstring"""
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
        ncin = Dataset(md.netcdf_product)
        value = md.get_data_centers(mmd_yaml['data_center'], ncin)
        self.assertEqual(value, [{
            'data_center_name': {
                'short_name': 'NO/MET',
                'long_name': 'Norwegian Meteorological Institute'
            },
            'data_center_url': ''
        }])

    def test_create_mmd_missing_update_times(self):
        """ToDo: Add docstring"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(self.fail_nc, check_only=True)
        ncin = Dataset(md.netcdf_product)
        md.get_metadata_updates(mmd_yaml['last_metadata_update'], ncin)
        self.assertEqual(
            md.missing_attributes['errors'][0],
            'ACDD attribute date_created or date_metadata_modified is required'
        )

    def test_create_mmd_missing_abstract(self):
        """ToDo: Add docstring"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(self.fail_nc, check_only=True)
        ncin = Dataset(md.netcdf_product)
        md.get_abstracts(mmd_yaml['abstract'], ncin)
        self.assertEqual(
            md.missing_attributes['errors'][0],
            'summary is a required ACDD attribute'
        )

    def test_publication_date(self):
        """ToDo: Add docstring"""
        d_format = '%Y-%m-%d'
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc', check_only=True)
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_dataset_citations(mmd_yaml['dataset_citation'], ncin)
        dt = datetime.datetime.strptime(value[0]['publication_date'], d_format)
        self.assertEqual(dt, datetime.datetime(2020, 11, 27, 0, 0))
        self.assertEqual(
            value[0]['title'], 'Direct Broadcast data processed in satellite swath to L1C.'
        )

    def test_checksum(self):
        """ToDo: Add docstring"""
        tested = tempfile.mkstemp()[1]
        fn = 'tests/data/reference_nc.nc'
        nc2mmd = Nc_to_mmd(fn, check_only=True)
        nc2mmd.to_mmd()
        checksum = nc2mmd.metadata['storage_information']['checksum']
        with open(tested, 'w') as tt:
            tt.write('%s *%s'%(checksum, fn))
        md5hasher = FileHash('md5')
        self.assertTrue(md5hasher.verify_checksums(tested)[0].hashes_match)

    def test_spatial_repr(self):
        """ToDo: Add docstring"""
        tempfile.mkstemp()[1]
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc', check_only=True)
        nc2mmd.to_mmd()
        spatial_repr = nc2mmd.metadata['spatial_representation']
        self.assertEqual(spatial_repr, 'grid')

    def test_spatial_repr_fail(self):
        """ToDo: Add docstring"""
        tempfile.mkstemp()[1]
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_missing_spatial_repr.nc', check_only=True)
        with self.assertRaises(AttributeError):
            nc2mmd.to_mmd()
        self.assertEqual(
            nc2mmd.missing_attributes['errors'][0],
            'geospatial_lat_max is a required attribute'
        )

    @patch('py_mmd_tools.nc_to_mmd.wget.download')
    @patch('py_mmd_tools.nc_to_mmd.os.remove')
    def test_file_on_thredds(self, mock_remove, mock_download):
        """Check that file is downloaded for checksum calculation and then removed"""
        fn = 'tests/data/dodsC/reference_nc.nc'
        mock_download.return_value = fn
        nc2mmd = Nc_to_mmd(fn, check_only=True)
        nc2mmd.to_mmd()
        self.assertEqual(
            nc2mmd.metadata['storage_information']['file_name'],
            'reference_nc.nc'
        )

    def test_access_constraint(self):
        """ToDo: Add docstring"""
        tempfile.mkstemp()[1]
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc', check_only=True)
        nc2mmd.to_mmd()
        spatial_repr = nc2mmd.metadata['access_constraint']
        self.assertEqual(spatial_repr, 'Open')


if __name__ == '__main__':
    unittest.main()
