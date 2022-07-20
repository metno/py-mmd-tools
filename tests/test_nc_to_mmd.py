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

import pandas as pd

from dateutil.parser import isoparse
from filehash import FileHash
from lxml import etree
from netCDF4 import Dataset
from pkg_resources import resource_string
from unittest.mock import patch

from py_mmd_tools.nc_to_mmd import Nc_to_mmd, validate_iso8601
from py_mmd_tools.yaml_to_adoc import nc_attrs_from_yaml
from py_mmd_tools.yaml_to_adoc import get_attr_info
from py_mmd_tools.yaml_to_adoc import required
from py_mmd_tools.yaml_to_adoc import repetition_allowed
from py_mmd_tools.yaml_to_adoc import set_attribute
from py_mmd_tools.yaml_to_adoc import set_attributes

warnings.simplefilter("ignore", ResourceWarning)


class TestNCAttrsFromYaml(unittest.TestCase):

    def setUp(self):
        """ Sets up class with an attribute `mmd_yaml` containing
        the MMD to ACDD translations.
        """
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
        self.assertEqual(self.attributes['acdd_ext']['not_required'][0],
                {
                    'mmd_field': 'dataset_production_status',
                    'attribute': 'dataset_production_status',
                    'repetition_allowed': False,
                    'comment': 'No repetition allowed',
                    'separator': '',
                    'default': 'Complete'
                    })
        # Test acdd
        mmd_field = 'operational_status'
        val = self.mmd_yaml[mmd_field]
        convention = 'acdd'
        set_attribute(mmd_field, val, convention, self.attributes, req='not_required')
        self.assertEqual(self.attributes['acdd']['not_required'][0],
                {
                    'mmd_field': 'operational_status',
                    'attribute': 'processing_level',
                    'repetition_allowed': False,
                    'comment': 'No repetition allowed. See the MMD docs for valid keywords.',
                    'separator': '',
                    'default': ''
                    })

    def test_set_attribute__two_conv_fields(self):
        """ Test the set_attribute method when two convention fields
        are provided in mmd_yaml.
        """
        mmd_field = 'metadata_identifier'
        val = self.mmd_yaml[mmd_field]
        convention = 'acdd'
        set_attribute(mmd_field, val, convention, self.attributes, req='required')
        self.assertEqual(self.attributes['acdd']['required'][0],
                {
                    'mmd_field': 'metadata_identifier',
                    'attribute': 'id',
                    'repetition_allowed': False,
                    'comment': 'Required, and should be UUID. No repetition allowed.',
                    'separator': '',
                    'default': ''
                    })
        self.assertEqual(self.attributes['acdd']['required'][1],
                {
                    'mmd_field': 'metadata_identifier',
                    'attribute': 'naming_authority',
                    'repetition_allowed': False,
                    'comment': 'Required. We recommend using reverse-DNS naming. ' \
                            'No repetition allowed.',
                    'separator': '',
                    'default': ''
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
        self.assertEqual(self.attributes['acdd']['required'][0],
                {
                    'mmd_field': 'metadata_identifier',
                    'attribute': 'id',
                    'repetition_allowed': False,
                    'comment': 'Required, and should be UUID. No repetition allowed.',
                    'separator': '',
                    'default': ''
                })

    def test_set_attributes__nested(self):
        mmd_field = 'keywords'
        val = self.mmd_yaml[mmd_field]
        set_attributes(mmd_field, val, self.attributes)
        self.assertEqual(self.attributes['acdd']['required'][0],
                {
                    'mmd_field': 'keywords>keyword',
                    'attribute': 'keywords',
                    'repetition_allowed': True,
                    'comment': 'Comma separated list',
                    'separator': ',',
                    'default': ''
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

    def test_get_attr_info__time_coverage(self):
        """Check that time_coverage_start and time_coverage_end are
        required.
        """
        # Flatten dict
        df = pd.json_normalize(self.mmd_yaml, sep='>')
        normalized = df.to_dict(orient='records')[0]
        sd_required, repetition_allowed = get_attr_info(
            'temporal_extent>start_date>acdd', 'acdd', normalized
        )
        ed_required, repetition_allowed = get_attr_info(
            'temporal_extent>end_date>acdd', 'acdd', normalized
        )
        self.assertTrue(sd_required)
        self.assertFalse(ed_required)

    def test_get_attr_info__missing_attrs(self):
        """ 
        - Check that max_occurs is set to an empty string in case
        it is missing in the yaml file, and that repetition is then
        allowed.
        - Check that required is set to 0 if minOccurs is missing in
        the yaml file, and that the attribute is then not required.
        """
        mao = self.mmd_yaml['temporal_extent']['start_date'].pop('maxOccurs')
        mio = self.mmd_yaml['temporal_extent']['start_date'].pop('minOccurs')
        # Flatten dict
        df = pd.json_normalize(self.mmd_yaml, sep='>')
        normalized = df.to_dict(orient='records')[0]
        sd_required, repetition_allowed = get_attr_info(
            'temporal_extent>start_date>acdd', 'acdd', normalized
        )
        self.assertFalse(sd_required)
        self.assertTrue(repetition_allowed)


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

    @patch('metvocab.mmdgroup.MMDGroup.init_vocab')
    def test_init_raises_error_on_mmd_group(self, mock_init_vocab):
        """Nc_to_mmd.__init__ should raise error if mmdgroups are not
        initialised.
        """
        with self.assertRaises(ValueError):
            Nc_to_mmd('tests/data/reference_nc.nc', output_file=None, check_only=True)

    def test_default_when_no_acdd_or_acdd_ext(self):
        """ Test that a default value can be used even if no acdd
        or acdd_ext fields are present.
        """
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc', check_only=True)
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_acdd_metadata(
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
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc', check_only=True)
        ncin = Dataset(nc2mmd.netcdf_product)
        with self.assertRaises(ValueError) as e:
            value = nc2mmd.get_acdd_metadata(
                mmd_yaml['metadata_identifier'],
                ncin, 'metadata_identifier'
            )
        self.assertEqual(str(e.exception), 'Multiple ACDD or ACCD extension fields provided.'
                ' Please use another translation function.')

    # This test doesn't make sense, since we have a separate function
    # for metadata updates. Remove later, following review..
    #def test_date_created_type__not_present(self):
    #    """Test that the line with 'if default' in get_acdd_metadata is
    #    covered. Note that we would normally use the function
    #    get_acdd_metadata to get date_created and date_created_type but
    #    then the line in get_acdd_metadata will not be covered..
    #    """
    #    mmd_yaml = yaml.load(
    #        resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
    #    )
    #    nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc', check_only=True)
    #    ncin = Dataset(nc2mmd.netcdf_product)
    #    value = nc2mmd.get_acdd_metadata(
    #        mmd_yaml['last_metadata_update']['update']['type'],
    #        ncin, 'date_created_type'
    #    )
    #    self.assertEqual(value, 'Created')

    def test_get_acdd_metadata_uses_default_date_created_type(self):
        """Test that the get_acdd_metadata function uses default
        date_created_type."""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc', check_only=True)
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_metadata_updates(mmd_yaml['last_metadata_update'], ncin)
        self.assertEqual(value['update'][0]['type'], 'Created')

    def test_polygon_is_not_wkt(self):
        """The geospatial_bounds nc attribute may not be a proper wkt string.
        Test that this case is properly handled.
        """
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(self.fail_nc, check_only=True)
        ncin = Dataset(md.netcdf_product, "w", diskless=True)
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
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc', check_only=True)
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_geographic_extent_polygon(
            mmd_yaml['geographic_extent']['polygon'], ncin
        )
        self.assertEqual(value['srsName'], 'EPSG:4326')
        self.assertEqual(value['pos'][0], '69.0000 3.7900')

    def test_missing_nc_attrs(self):
        """ToDo: Add docstring"""
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_missing_attrs.nc', check_only=True)
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_acdd_metadata(mmd_yaml['geographic_extent'], ncin, 'geographic_extent')
        self.assertEqual(value['rectangle']['north'], None)
        value = nc2mmd.get_data_centers(mmd_yaml['data_center'], ncin)
        self.assertEqual(
            nc2mmd.missing_attributes['errors'][0], 'geospatial_lat_max is a required attribute'
        )
        self.assertEqual(nc2mmd.missing_attributes['errors'][4],
                         'institution_short_name is a required attribute')
        self.assertEqual(
            nc2mmd.missing_attributes['errors'][5], 'institution is a required attribute'
        )

    def test_missing_geographic_extent_but_provided_as_kwarg(self):
        """Test that the geographic extent rectangle can be added
        as a kwarg.
        """
        yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_missing_rectangle.nc', check_only=True)
        nc2mmd.to_mmd(geographic_extent_rectangle={
                'geospatial_lat_max': 90,
                'geospatial_lat_min': -90,
                'geospatial_lon_min': -180,
                'geospatial_lon_max': 180
            })
        self.assertEqual(nc2mmd.metadata['geographic_extent']['rectangle']['north'], 90)

    def test_collection_is_not_list(self):
        """Test that an error is raised if the collection input
        parameter is wrong type.
        """
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_missing_attrs.nc', check_only=True)
        with self.assertRaises(ValueError) as e:
            nc2mmd.to_mmd(collection=2)
        self.assertEqual(str(e.exception), 'collection must be of type str or list')

    def test_collection_not_set(self):
        """ToDo: Add docstring"""
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_missing_collection.nc', check_only=True)
        req_ok, msg = nc2mmd.to_mmd()
        self.assertTrue(req_ok)
        self.assertEqual(nc2mmd.metadata['collection'], ['ADC', 'METNCS'])

    def test_collection_set(self):
        """ToDo: Add docstring"""
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc', check_only=True)
        status, msg = nc2mmd.to_mmd(collection='ADC')
        # nc files should normally not have a collection element, as this is
        # set during harvesting
        self.assertTrue(status)
        self.assertEqual(nc2mmd.metadata['collection'], ['ADC'])

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
        self.assertEqual(value['alternate_identifier'], None)
        self.assertEqual(value['type'], None)

    def test_alternate_identifier(self):
        """Test that MMD alternate_identifier is equal to the one
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
        self.assertEqual(value['alternate_identifier'][0], 'dummy_id_no1')
        self.assertEqual(value['type'][0], 'dummy_type')

    def test_alternate_identifier_multiple(self):
        """Test that MMD alternate_identifier is equal to the ones
        provided in the nc-file.
        """
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_with_altID_multiple.nc', check_only=True)
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_acdd_metadata(
            mmd_yaml['alternate_identifier'], ncin, 'alternate_identifier'
        )
        self.assertEqual(value['alternate_identifier'][0], 'dummy_id_no1')
        self.assertEqual(value['type'][0], 'dummy_type')
        self.assertEqual(value['type'][1], 'other_type')

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
        self.assertEqual(nc2mmd.metadata['temporal_extent']['start_date'],
                         '1850-01-01T00:00:00Z')

    def test_missing_temporal_extent_but_start_and_end_provided_as_kwargs(self):
        """ToDo: Add docstring"""
        yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader)
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_missing_attrs.nc', check_only=True)
        with self.assertRaises(AttributeError):
            nc2mmd.to_mmd(
                time_coverage_start='1850-01-01T00:00:00Z',
                time_coverage_end='1950-01-01T00:00:00Z'
            )
        self.assertEqual(nc2mmd.metadata['temporal_extent']['start_date'],
                         '1850-01-01T00:00:00Z')
        self.assertEqual(nc2mmd.metadata['temporal_extent']['end_date'], '1950-01-01T00:00:00Z')

    def test_temporal_extent_two_startdates(self):
        """Test that two start dates are handled correctly in the
        translation to MMD.
        """
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

    def test_temporal_extent_two_startdates_one_wrong(self):
        """Test that two start dates are handled correctly in the
        translation to MMD.
        """
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd('tests/data/reference_nc_attrs_multiple.nc', check_only=True)
        ncin = Dataset(md.netcdf_product, "w", diskless=True)
        ncin.time_coverage_start = "2020-11-27T13:40:02.019817Z, 2020-12-27 13:40:02.019817"
        ncin.time_coverage_end = "2020-11-27T13:51:24.401505Z, 2020-12-27 13:51:24.019817"
        value = md.get_temporal_extents(mmd_yaml['temporal_extent'], ncin)
        self.assertEqual(
            md.missing_attributes['errors'][0],
            'ACDD time attributes must contain valid ISO8601 dates. ' \
                    '2020-12-27 13:40:02.019817 is invalid.'
        )

    def test__validate_iso8601(self):
        self.assertFalse(validate_iso8601(""))
        self.assertFalse(validate_iso8601(None))
        self.assertFalse(validate_iso8601("2017-01-01"))
        self.assertTrue(validate_iso8601("2008-08-30T01:45:36.123Z"))
        self.assertTrue(validate_iso8601("2016-12-13T21:20:37.593194+00:00"))
        self.assertFalse(validate_iso8601("2019-02-29T12:00:00+00:00"))
        self.assertFalse(validate_iso8601("2020-12-27 13:40:02.019817"))
        self.assertTrue(validate_iso8601("2020-11-27T13:40:02.019817Z"))

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
        resource_link = 'https://www.wmo-sat.info/oscar/satellites/view/snpp'
        self.assertEqual(value[0]['resource'], resource_link)

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

    def test__keywords_vocabulary__correctly_formatted(self):
        """Check that error massages are added if the
        keywords_vocabulary attribute is not formatted
        as short_name:long_name:url
        """
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(self.fail_nc, check_only=True)
        ncin = Dataset(md.netcdf_product, "w", diskless=True)
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
        self.assertEqual(value[0]['instrument']['long_name'], 'Synthetic Aperture Radar (C-band)')

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

    def test_dataset_citation_invalid_date(self):
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd('tests/data/reference_nc.nc', check_only=True)
        ncin = Dataset(md.netcdf_product, "w", diskless=True)
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
        ncin.date_created = "2020-11-28 13:51:24"
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        value = md.get_dataset_citations(mmd_yaml['dataset_citation'], ncin)
        self.assertEqual(
            md.missing_attributes['errors'][0],
            "ACDD attribute date_created must contain a valid ISO8601 date."
        )

    @patch('py_mmd_tools.nc_to_mmd.Dataset')
    def test_oserror_opendap(self, mock_nc_dataset):
        """ToDo: Add docstring"""
        mock_nc_dataset.side_effect = OSError
        fn = (
            'http://nbstds.met.no/thredds/dodsC/NBS/S1A/2021/01/31/IW/'
            'S1A_IW_GRDH_1SDV_20210131T172816_20210131T172841_036385_04452D_505F.nc'
        )
        try:
            nc2mmd = Nc_to_mmd(fn, check_only=True)
        except Exception as e:
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
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc', check_only=True)
        ncin = Dataset(nc2mmd.netcdf_product)
        with self.assertRaises(AttributeError) as e:
            nc2mmd.get_metadata_identifier(mmd_yaml['metadata_identifier'], ncin)
        self.assertEqual(
            "ACDD attribute inconsistency in mmd_elements.yaml. Expected id and "
            "naming_authority but received ['id'].",
            str(e.exception)
        )
        # Inconsistency of ACCD id in mmd_elements.yaml (='jkhakjh')
        # and the hardcoded one (='id')
        mmd_yaml['metadata_identifier']['acdd'] = {'jkhakjh': {}, 'naming_authority': {}}
        with self.assertRaises(AttributeError) as e:
            nc2mmd.get_metadata_identifier(mmd_yaml['metadata_identifier'], ncin)
        self.assertEqual(
            "ACDD attribute inconsistency in mmd_elements.yaml. Expected id and "
            "naming_authority but received ['jkhakjh', 'naming_authority'].",
            str(e.exception)
        )
        # Inconsistency of ACCD naming_authority in mmd_elements.yaml
        # (='jklhkha') and the hardcoded one (='naming_authority')
        mmd_yaml['metadata_identifier']['acdd'] = {'id': {}, 'jklhkha': {}}
        with self.assertRaises(AttributeError) as e:
            nc2mmd.get_metadata_identifier(mmd_yaml['metadata_identifier'], ncin)
        self.assertEqual(
            "ACDD attribute inconsistency in mmd_elements.yaml. Expected id and "
            "naming_authority but received ['id', 'jklhkha'].",
            str(e.exception)
        )
        # Change the valid naming authorities to force an error
        nc2mmd.VALID_NAMING_AUTHORITIES = ['jada.no']
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        nc2mmd.get_metadata_identifier(mmd_yaml['metadata_identifier'], ncin)
        self.assertEqual(
            nc2mmd.missing_attributes['errors'][0],
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
                    'default': 'hei'
                }
            }
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc', check_only=True)
        nc2mmd.to_mmd(mmd_yaml=mmd_yaml)
        self.assertEqual(
            nc2mmd.missing_attributes['warnings'][0],
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
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_fail.nc', check_only=True)
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_metadata_identifier(mmd_yaml['metadata_identifier'], ncin)
        self.assertFalse(Nc_to_mmd.is_valid_uuid(value))
        self.assertEqual(':', value)
        with self.assertRaises(AttributeError) as context:
            nc2mmd.to_mmd()
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
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc', check_only=True)
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_metadata_identifier(mmd_yaml['metadata_identifier'], ncin)
        self.assertEqual(value, 'no.met:b7cb7934-77ca-4439-812e-f560df3fe7eb')

    def test__to_mmd__missing_id(self):
        """Test that an AttributeError is raised for missing id
        attribute.
        """
        tested = tempfile.mkstemp()[1]
        # nc file is missing the id attribute
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_id_missing.nc', output_file=tested)
        with self.assertRaises(AttributeError):
            nc2mmd.to_mmd()
        ncin = Dataset(nc2mmd.netcdf_product)
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        value = nc2mmd.get_metadata_identifier(mmd_yaml['metadata_identifier'], ncin)
        self.assertEqual(
            nc2mmd.missing_attributes['errors'][0], 'id is a required attribute.'
        )
        self.assertEqual(
            nc2mmd.missing_attributes['errors'][1], 'naming_authority is a required attribute.'
        )
        self.assertEqual(nc2mmd.missing_attributes['warnings'], [])
        self.assertFalse(Nc_to_mmd.is_valid_uuid(nc2mmd.metadata['metadata_identifier']))
        self.assertEqual(':', value)

    def test__to_mmd__invalid_uuid(self):
        """Test that we cannot create an MMD file if the netcdf id
        attribute is not a valid uuid.
        """
        tested = tempfile.mkstemp()[1]
        # The id attribute is not a uuid
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_id_not_uuid.nc', output_file=tested)
        with self.assertRaises(AttributeError):
            nc2mmd.to_mmd()
        self.assertFalse(Nc_to_mmd.is_valid_uuid(nc2mmd.metadata['metadata_identifier']))
        self.assertEqual(':', nc2mmd.metadata['metadata_identifier'])

    def test__to_mmd__error_if_accd_id_is_invalid(self):
        """Test that metadata_identifier is set to an empty string, and
        that an exception is raised if the ACDD id is not a valid uuid.
        """
        tested = tempfile.mkstemp()[1]
        # The id attribute is not a uuid
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_id_not_uuid.nc', output_file=tested)
        with self.assertRaises(AttributeError):
            nc2mmd.to_mmd()
        self.assertEqual(
            nc2mmd.missing_attributes['errors'][0], (
                'naming_authority is a required attribute.'
            )
        )
        self.assertEqual(
            nc2mmd.missing_attributes['errors'][1], (
                'id ACDD attribute is not valid.'
            )
        )
        self.assertEqual(nc2mmd.missing_attributes['warnings'], [])
        self.assertFalse(Nc_to_mmd.is_valid_uuid(nc2mmd.metadata['metadata_identifier']))
        ncin = Dataset(nc2mmd.netcdf_product)
        id = ncin.getncattr('id')
        self.assertNotEqual(id, nc2mmd.metadata['metadata_identifier'])
        self.assertEqual(':', nc2mmd.metadata['metadata_identifier'])

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
        self.assertTrue(id in nc2mmd.metadata['metadata_identifier'])

    def test_create_mmd_1(self):
        """Test MMD creation from a valid netcdf file, validation
        with the mmd_strict.xsd, and that some fields are as expected.
        Please add new fields to test as needed..
        """
        tested = tempfile.mkstemp()[1]
        # md = Nc_to_mmd(self.reference_nc, output_file=tested)
        md = Nc_to_mmd('tests/data/reference_nc_with_altID_multiple.nc', output_file=tested)
        md.to_mmd(checksum_calculation=True)
        xsd_obj = etree.XMLSchema(etree.parse(self.reference_xsd))
        xml_doc = etree.ElementTree(file=tested)
        valid = xsd_obj.validate(xml_doc)
        self.assertTrue(valid)
        """ Check content of the xml_doc """
        # alternate_identifier
        self.assertEqual(
            xml_doc.getroot().find(
                "{http://www.met.no/schema/mmd}alternate_identifier[@type='dummy_type']"
            ).text,
            "dummy_id_no1"
        )
        self.assertEqual(
            xml_doc.getroot().find(
                "{http://www.met.no/schema/mmd}alternate_identifier[@type='other_type']"
            ).text,
            "dummy_id_no2"
        )

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
            md = Nc_to_mmd(file, output_file=tested)
            md.to_mmd(checksum_calculation=True)
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
        """Test that an error is reported if date_created attribute is
        missing from the netcdf file.
        """
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(self.fail_nc, check_only=True)
        ncin = Dataset(md.netcdf_product)
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
        ncin = Dataset(md.netcdf_product)
        #ncin.date_created = '2020-01-01T12:00:00Z'
        #md.metadata['title'] = 'Test dataset'
        data = md.get_dataset_citations(mmd_yaml['dataset_citation'], ncin)
        self.assertEqual(data[0]['title'],
                'Direct Broadcast data processed in satellite swath to L1C.')

    def test_ACDD_attr__date_metadata_modified_type___missing(self):
        """Test that the correct error is raised when date_created
        is missing from the nc-file.
        """
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(self.fail_nc, check_only=True)
        # To overwrite date_created, wihtout saving it to file we use diskless
        ncin = Dataset(md.netcdf_product, "w", diskless=True)
        ncin.date_created = '2019-01-01T00:00:00Z'
        ncin.date_metadata_modified = '2020-01-01T00:00:00Z'
        md.get_metadata_updates(mmd_yaml['last_metadata_update'], ncin)
        self.assertEqual(
            md.missing_attributes['warnings'][0],
            "Using default value 'Minor modification' for date_metadata_modified_type"
        )

    def test_ACDD_attr_date_metadata_modified_not_required(self):
        """Ensure that only date_created is required, and that
        date_metadata_modified is optional.
        """
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        md = Nc_to_mmd(self.fail_nc, check_only=True)
        # To overwrite date_created, wihtout saving it to file we use diskless
        ncin = Dataset(md.netcdf_product, "w", diskless=True)
        ncin.date_created = '2020-01-01T00:00:00Z'
        data = md.get_metadata_updates(mmd_yaml['last_metadata_update'], ncin)
        self.assertIn(
            {'datetime':  ncin.date_created, 'type': 'Created'},
            data['update']
        )
        assert (len(data['update']) == 1)

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
                'date_metadata_modified': {}
            }
        md = Nc_to_mmd(self.reference_nc, check_only=True)
        ncin = Dataset(md.netcdf_product)
        with self.assertRaises(AttributeError) as context1:
            md.get_metadata_updates(in_dict, ncin)
        self.assertTrue(
            'ACDD attribute inconsistency in mmd_elements.yaml' in str(context1.exception)
        )
        mmd_yaml = yaml.load(
            resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        in_dict = mmd_yaml['last_metadata_update']
        in_dict['update']['datetime']['acdd'] = {
                'date_created': {},
                'new_name_for_date_metadata_modified': {}  # this will cause an error
            }
        with self.assertRaises(AttributeError) as context2:
            md.get_metadata_updates(in_dict, ncin)
        self.assertTrue(
            'ACDD attribute inconsistency in mmd_elements.yaml' in str(context2.exception)
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
        dt = isoparse(value[0]['publication_date'])
        self.assertEqual(dt.year, 2020)
        self.assertEqual(dt.month, 11)
        self.assertEqual(dt.day, 27)
        self.assertEqual(
            value[0]['title'], 'Direct Broadcast data processed in satellite swath to L1C.'
        )

    def test_checksum(self):
        """ToDo: Add docstring"""
        tested = tempfile.mkstemp()[1]
        fn = 'tests/data/reference_nc.nc'
        nc2mmd = Nc_to_mmd(fn, check_only=True)
        nc2mmd.to_mmd(checksum_calculation=True)
        checksum = nc2mmd.metadata['storage_information']['checksum']
        with open(tested, 'w') as tt:
            tt.write('%s *%s'%(checksum, fn))
        md5hasher = FileHash('md5')
        self.assertTrue(md5hasher.verify_checksums(tested)[0].hashes_match)

    def test_checksum_off(self):
        """ToDo: Add docstring"""
        fn = 'tests/data/reference_nc.nc'
        nc2mmd = Nc_to_mmd(fn, check_only=True)
        nc2mmd.to_mmd(checksum_calculation=False)
        with self.assertRaises(KeyError):
            nc2mmd.metadata['storage_information']['checksum']
            nc2mmd.metadata['storage_information']['checksum_type']
        # Check if default is False
        nc2mmd = Nc_to_mmd(fn, check_only=True)
        nc2mmd.to_mmd()
        with self.assertRaises(KeyError):
            nc2mmd.metadata['storage_information']['checksum']
            nc2mmd.metadata['storage_information']['checksum_type']

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

    def test_check_attributes_not_empty(self):
        md = Nc_to_mmd(self.fail_nc, check_only=True)
        ncin = Dataset(md.netcdf_product, "w", diskless=True)
        ncin.geospatial_bounds = ""
        with self.assertRaises(ValueError) as e:
            md.check_attributes_not_empty(ncin)
        self.assertIn('Global attribute geospatial_bounds is empty - please correct.',
                str(e.exception))


if __name__ == '__main__':
    unittest.main()
