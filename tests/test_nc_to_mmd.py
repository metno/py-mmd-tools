"""
License:
     This file is part of the py-mmd-tools repository (https://github.com/metno/py-mmd-tools). py-mmd-tools is licensed under Apache License 2.0 (https://github.com/metno/py-mmd-tools/blob/master/LICENSE).
 """
from unittest.mock import patch, Mock, DEFAULT
import unittest

import os
import pathlib
import tempfile
import yaml
import datetime
from pkg_resources import resource_string

from netCDF4 import Dataset

from py_mmd_tools.xml_utils import xsd_check
from py_mmd_tools.nc_to_mmd import Nc_to_mmd


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

    def test_use_defaults_for_geographic_extent(self):
        mmd_yaml = yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader)
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_missing_attrs.nc')
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_acdd_metadata(mmd_yaml['geographic_extent'], ncin)
        self.assertEqual(value['rectangle']['north'], 90)
        self.assertEqual(value['rectangle']['south'], -90)
        self.assertEqual(value['rectangle']['east'], 180)
        self.assertEqual(value['rectangle']['west'], -180)

    def test_collection_not_set(self):
        mmd_yaml = yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'),
                Loader=yaml.FullLoader)
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_missing_attrs.nc')
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_acdd_metadata(mmd_yaml['collection'], ncin)
        # nc files should normally not have a collection element, as this is
        # set during harvesting
        self.assertEqual(value, [])

    def test_collection_set(self):
        mmd_yaml = yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'),
                Loader=yaml.FullLoader)
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc')
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_acdd_metadata(mmd_yaml['collection'], ncin)
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
        value = None #nc2mmd.get_acdd_metadata(mmd_yaml['data_access'], ncin)
        self.assertEqual(value, None)

    def test_dataset_production_status(self):
        mmd_yaml = yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'),
                Loader=yaml.FullLoader)
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc')
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_acdd_metadata(mmd_yaml['dataset_production_status'], ncin)
        self.assertEqual(value, 'In Work')

    def test_alternate_identifier(self):
        mmd_yaml = yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'),
                Loader=yaml.FullLoader)
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc')
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_acdd_metadata(mmd_yaml['alternate_identifier'], ncin)
        self.assertEqual(value, [])

    def test_metadata_status_is_active(self):
        mmd_yaml = yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'),
                Loader=yaml.FullLoader)
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc')
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_acdd_metadata(mmd_yaml['metadata_status'], ncin)
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

    def test_use_defaults_for_temporal_extent(self):
        mmd_yaml = yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader)
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_missing_attrs.nc')
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_temporal_extents(mmd_yaml['temporal_extent'], ncin)
        self.assertEqual(value[0]['start_date'], '1850-01-01T00:00:00Z')

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
        self.assertEqual(value[0]['name'], 'Trygve')
        self.assertEqual(value[1]['name'], 'Trygve')
        self.assertEqual(value[0]['email'], 'trygve@meti.no')
        self.assertEqual(value[1]['email'], 'trygve@meti.no')
        self.assertEqual(value[0]['role'], 'Investigator')
        self.assertEqual(value[1]['role'], 'Technical contact')

    def test_personnel_multiple(self):
        mmd_yaml = yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader)
        nc2mmd = Nc_to_mmd('tests/data/reference_nc_attrs_multiple.nc')
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_personnel(mmd_yaml['personnel'], ncin)
        self.assertEqual(value[0]['email'], 'trygve@meti.no')
        self.assertEqual(value[1]['email'], 'post@met.no')
        self.assertEqual(value[0]['role'], 'Investigator')
        self.assertEqual(value[1]['role'], 'Technical contact')

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
        value = nc2mmd.get_acdd_metadata(mmd_yaml['iso_topic_category'], ncin)
        self.assertEqual(value[0], 'climatologyMeteorologyAtmosphere')
        self.assertEqual(value[1], 'environment')
        self.assertEqual(value[2], 'oceans')

    def test_keywords(self):
        mmd_yaml = yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader)
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc')
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_keywords(mmd_yaml['keywords'], ncin)
        self.assertEqual(value[0]['resource'], 'GCMD')

    def test_platforms(self):
        mmd_yaml = yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader)
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc')
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_platforms(mmd_yaml['platform'], ncin)
        self.assertEqual(value[0]['long_name'], 'SNPP')
        self.assertEqual(value[0]['instrument']['long_name'], 'VIIRS')

    def test_projects(self):
        mmd_yaml = yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader)
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc')
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_projects(mmd_yaml['project'], ncin)
        self.assertEqual(value[0]['long_name'], 'Govermental core service')

    def test_dataset_citation(self):
        mmd_yaml = yaml.load(resource_string('py_mmd_tools', 'mmd_elements.yaml'), Loader=yaml.FullLoader)
        nc2mmd = Nc_to_mmd('tests/data/reference_nc.nc')
        ncin = Dataset(nc2mmd.netcdf_product)
        value = nc2mmd.get_dataset_citations(mmd_yaml['dataset_citation'], ncin)
        self.assertEqual(value[0]['title'], ncin.getncattr('title'))

    @patch('py_mmd_tools.nc_to_mmd.Nc_to_mmd.__init__')
    def test_required_mmd_elements(self, mock_init):
        mock_init.return_value = None
        nc2mmd = Nc_to_mmd()
        mmd_required_elements = {'metadata_identifier':None,
                           'metadata_status':None,
                            'collection':None,
                            'title': None,
                            'abstract': None,
                            'last_metadata_update': None,
                            'dataset_production_status': None,
                            'operational_status': None,
                            'iso_topic_category': None,
                            'keywords': '\n\t\t<mmd:keyword></mmd:keyword>\n\t',
                            'temporal_extent': '\n\t\t<mmd:start_date></mmd:start_date>\n\t',
                            'geographic_extent': str('\n\t\t<mmd:rectangle srsName=""> \n\t\t\t<mmd:north></mmd:north> \n\t\t\t<mmd:south></mmd:south> \n\t\t\t<mmd:east></mmd:east> \n\t\t\t<mmd:west></mmd:west> \n\t\t</mmd:rectangle>\n\t')
                            }
        self.assertEqual(nc2mmd.required_mmd_elements(), mmd_required_elements)

    @patch('py_mmd_tools.nc_to_mmd.Nc_to_mmd.__init__')
    def test_generate_cf_mmd_lut_missing_acdd(self, mock_init):
        mock_init.return_value = None
        nc2mmd = Nc_to_mmd()
        cf_mmd_expected_elements = {'metadata_status': 'metadata_status',
                                    'collection': 'collection',
                                    'dataset_production_status': 'dataset_production_status',
                                    'iso_topic_category': 'iso_topic_category',
                                    'platform': 'platform,short_name',
                                    'platform_long_name': 'platform,long_name',
                                    'platform_resource': 'platform,resource',
                                    'instrument': 'platform,instrument,short_name',
                                    'instrument_long_name': 'platform,instrument,long_name',
                                    'instrument_resource': 'platform,instrument,resource',
                                    'ancillary_timeliness': 'platform,ancillary,timeliness',
                                    'title_lang': 'attrib_lang',
                                    'summary_lang': 'attrib_lang',
                                    'license': 'use_constraint,identifier',
                                    'license_resource': 'use_constraint,resource',
                                    'publisher_country': 'personnel,country',
                                    'creator_role': 'personnel,role',
                                    'date_metadata_modified': 'last_metadata_update,update,datetime',
                                    'date_metadata_modified_type': 'last_metadata_update,update,type',
                                    'date_metadata_modified_note': 'last_metadata_update,update,note'}

        self.assertEqual(nc2mmd.generate_cf_mmd_lut_missing_acdd(), cf_mmd_expected_elements)

    @patch('py_mmd_tools.nc_to_mmd.Nc_to_mmd.__init__')
    def test_generate_cf_acdd_mmd_lut(self, mock_init):
        mock_init.return_value = None
        nc2mmd = Nc_to_mmd()
        cf_acdd_mmd_lut_expected_elements = {'title': 'title',
                                             'summary': 'abstract',
                                             'keywords': 'keywords,keyword',
                                             'keywords_vocabulary': 'attrib_vocabulary',
                                             'Conventions': None,
                                             'id': 'metadata_identifier',
                                             'naming_authority': 'reference',
                                             'history': None,
                                             'source': 'activity_type',
                                             'processing_level': 'operational_status',
                                             'comment': None,
                                             'acknowledgement': 'reference',
                                             'license': 'use_constraint',
                                             'standard_name_vocabulary': None,
                                             'date_created': None,
                                             'creator_name': 'personnel,name',
                                             'creator_email': 'personnel,email',
                                             'creator_url': None,
                                             'project': 'project,long_name',
                                             'publisher_name': 'personnel,name',
                                             'publisher_email': 'personnel,email',
                                             'publisher_url': None,
                                             'geospatial_bounds': None,
                                             'geospatial_bounds_crs': 'attrib_srsName',
                                             'geospatial_bounds_vertical_crs':  None,
                                             'geospatial_lat_min': 'geographic_extent,rectangle,south',
                                             'geospatial_lat_max': 'geographic_extent,rectangle,north',
                                             'geospatial_lon_min': 'geographic_extent,rectangle,west',
                                             'geospatial_lon_max': 'geographic_extent,rectangle,east',
                                             'geospatial_vertical_min': None,
                                             'geospatial_vertical_max': None,
                                             'geospatial_vertical_positive': None,
                                             'time_coverage_start': 'temporal_extent,start_date',
                                             'time_coverage_end': 'temporal_extent,end_date',
                                             'time_coverage_duration': None,
                                             'time_coverage_resolution': None,
                                             'creator_type': None,
                                             'publisher_type': None,
                                             'publisher_institution': 'personnel,organisation',
                                             'contributor_name': 'data_center,contact,name',
                                             'contributor_role': 'data_center,contact,role',
                                             'institution': 'data_center,data_center_name,long_name',
                                             'creator_institution': 'dataset_citation,dataset_publisher',
                                             'metadata_link': 'dataset_citation,online_resource',
                                             'references': 'dataset_citation,other_citation_details',
                                             'product_version': 'dataset_citation,version',
                                             'geospatial_lat_units': None,
                                             'geospatial_lat_resolution': None,
                                             'geospatial_lon_units': None,
                                             'geospatial_lon_resolution': None,
                                             'geospatial_vertical_units': None,
                                             'geospatial_vertical_resolution': None,
                                             'date_modified': None,
                                             'date_issued': None,
                                             'date_metadata_modified': 'last_metadata_update',
                                             'platform': None,
                                             'platform_vocabulary': None,
                                             'instrument': 'instrument,long_name',
                                             'instrument_vocabulary': None,
                                             'cdm_data_type': None}
        self.assertEqual(nc2mmd.generate_cf_acdd_mmd_lut(), cf_acdd_mmd_lut_expected_elements)

    def test_create_mmd_1(self):
        tested = tempfile.mkstemp()[1]
        md = Nc_to_mmd(self.reference_nc, output_file=tested)
        md.to_mmd()
        valid = xsd_check(xml_file=tested, xsd_schema=self.reference_xsd)
        self.assertTrue(valid[0])

    def test_create_mmd_2(self):
        self.maxDiff = None
        tested = tempfile.mkstemp()[1]
        md = Nc_to_mmd(self.fail_nc, output_file=tested)
        with self.assertRaises(AttributeError):
            md.to_mmd()

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

        #with open(self.reference_xml) as reference, open(tested) as tested:
        #    reference_string = reference.read()
        #    reference_string = reference_string.replace('</mmd:geographic_extent>\n  <mmd:metadata_identifier>npp-viirs-mband-20201127134002-20201127135124</mmd:metadata_identifier>\n  <mmd:data_center>', '</mmd:geographic_extent>\n  <mmd:data_center>')
        #    reference_string = reference_string.replace('</mmd:title>\n  <!--<mmd:data_access>', '</mmd:title>\n  <!--<mmd:metadata_identifier></mmd:metadata_identifier>-->\n  <!--<mmd:data_access>')
        #    reference_string = reference_string.replace('</mmd:iso_topic_category>\n  '
        #                                                '<mmd:keywords vocabulary="GCMD">\n    '
        #                                                '<mmd:keyword>Earth Science &gt; Atmosphere &gt; Atmospheric radiation</mmd:keyword>\n  </mmd:keywords>\n  <mmd:use_constraint>','</mmd:iso_topic_category>\n  <mmd:use_constraint>')
        #    reference_string = reference_string.replace(
        #        '</mmd:metadata_identifier>-->\n  <!--<mmd:data_access>', '</mmd:metadata_identifier>-->\n  <!--<mmd:keywords>\n\t\t<mmd:keyword></mmd:keyword>\n\t</mmd:keywords>-->\n  <!--<mmd:data_access>')
        #    reference_string = reference_string.replace('<mmd:rectangle>', '<mmd:rectangle srsName="EPSG:4326">')
        #    tested_string = tested.read()
        #    unittest.TestCase.assertMultiLineEqual(self, first=reference_string, second=tested_string)

    #def test_create_mmd_from_url(self):
    #    tested = tempfile.mkstemp()[1]
    #    self.maxDiff = None
    #    md = Nc_to_mmd('https://thredds.met.no/thredds/dodsC/remotesensingsatellite/polar-swath'
    #                   '/2020/11/27/npp-viirs-mband-20201127134002-20201127135124.nc', output_file=tested)
    #    md.to_mmd()
    #    with open(self.reference_xml) as reference, open(tested) as tested:
    #        reference_string = reference.read()
    #        reference_string = reference_string.replace('</mmd:title>\n  <!--<mmd:data_access>',
    #                                 '</mmd:title>\n  <mmd:data_access>\n    '
    #                                 '<mmd:type>OPeNDAP</mmd:type>\n    '
    #                                 '<mmd:description>Open-source Project for a Network Data '
    #                                 'Access Protocol</mmd:description>\n    '
    #                                 '<mmd:resource>https://thredds.met.no/thredds/dodsC'
    #                                 '/remotesensingsatellite/polar-swath/2020/11/27/npp-viirs'
    #                                 '-mband-20201127134002-20201127135124.nc</mmd:resource>\n  '
    #                                 '</mmd:data_access>\n  <mmd:data_access>\n    <mmd:type>OGC '
    #                                 'WMS</mmd:type>\n    <mmd:description>OGC Web Mapping '
    #                                 'Service, URI to GetCapabilities '
    #                                 'Document.</mmd:description>\n    '
    #                                 '<mmd:resource>https://thredds.met.no/thredds/wms'
    #                                 '/remotesensingsatellite/polar-swath/2020/11/27/npp-viirs'
    #                                 '-mband-20201127134002-20201127135124.nc?service=WMS&amp'
    #                                 ';version=1.3.0&amp;request=GetCapabilities</mmd:resource>\n '
    #                                 '   <mmd:wms_layers>\n      '
    #                                 '<mmd:wms_layer>M09</mmd:wms_layer>\n      '
    #                                 '<mmd:wms_layer>M01</mmd:wms_layer>\n      '
    #                                 '<mmd:wms_layer>M04</mmd:wms_layer>\n      '
    #                                 '<mmd:wms_layer>M02</mmd:wms_layer>\n      '
    #                                 '<mmd:wms_layer>M16</mmd:wms_layer>\n      '
    #                                 '<mmd:wms_layer>M13</mmd:wms_layer>\n      '
    #                                 '<mmd:wms_layer>M14</mmd:wms_layer>\n      '
    #                                 '<mmd:wms_layer>M12</mmd:wms_layer>\n      '
    #                                 '<mmd:wms_layer>M07</mmd:wms_layer>\n      '
    #                                 '<mmd:wms_layer>M10</mmd:wms_layer>\n      '
    #                                 '<mmd:wms_layer>M08</mmd:wms_layer>\n      '
    #                                 '<mmd:wms_layer>M15</mmd:wms_layer>\n      '
    #                                 '<mmd:wms_layer>M03</mmd:wms_layer>\n      '
    #                                 '<mmd:wms_layer>M05</mmd:wms_layer>\n      '
    #                                 '<mmd:wms_layer>M06</mmd:wms_layer>\n      '
    #                                 '<mmd:wms_layer>M11</mmd:wms_layer>\n    </mmd:wms_layers>\n '
    #                                 ' </mmd:data_access>\n  <mmd:data_access>\n    '
    #                                 '<mmd:type>HTTP</mmd:type>\n    <mmd:description>Open-source '
    #                                 'Project for a Network Data Access '
    #                                 'Protocol.</mmd:description>\n    '
    #                                 '<mmd:resource>https://thredds.met.no/thredds/fileServer'
    #                                 '/remotesensingsatellite/polar-swath/2020/11/27/npp-viirs'
    #                                 '-mband-20201127134002-20201127135124.nc</mmd:resource>\n  '
    #                                 '</mmd:data_access>\n  <!--<mmd:data_access>')
    #        tested_string = tested.read()
    #        unittest.TestCase.assertMultiLineEqual(self, first=reference_string, second=tested_string)

    #def test_check_nc(self):
    #    md = Nc_to_mmd(self.reference_nc, check_only=True)
    #    self.assertTrue(md.to_mmd())


if __name__ == '__main__':
    unittest.main()
