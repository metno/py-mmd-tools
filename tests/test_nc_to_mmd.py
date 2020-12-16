from unittest.mock import patch, Mock, DEFAULT
import unittest
import pathlib
import tempfile
from py_mmd_tools.nc_to_mmd import Nc_to_mmd
#from mmd_utils.nc_to_mmd import main as main_nc_to_mmd

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

    ##@patch('py_mmd_utils.nc_to_mmd.Nc_to_mmd.__init__')
    ##@patch('mmd_utils.nc_to_mmd.Nc_to_mmd.to_mmd')
    ##def test__main_with_defaults(self, mock_to_mmd, mock_init):
    ##    mock_init.return_value = None
    ##    self.assertTrue(mock_init.called)
    ##    self.assertTrue(mock_to_mmd.called)

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
        with open(self.reference_xml) as reference, open(tested) as tested:
            reference_string = reference.read()
            tested_string = tested.read()
            unittest.TestCase.assertMultiLineEqual(self, first=reference_string, second=tested_string)

    def test_create_mmd_2(self):
        self.maxDiff = None
        tested = tempfile.mkstemp()[1]
        md = Nc_to_mmd(self.fail_nc, output_file=tested)
        md.to_mmd()
        with open(self.reference_xml) as reference, open(tested) as tested:
            reference_string = reference.read()
            reference_string = reference_string.replace('</mmd:geographic_extent>\n  <mmd:metadata_identifier>npp-viirs-mband-20201127134002-20201127135124</mmd:metadata_identifier>\n  <mmd:data_center>', '</mmd:geographic_extent>\n  <mmd:data_center>')
            reference_string = reference_string.replace('</mmd:title>\n  <!--<mmd:data_access>', '</mmd:title>\n  <!--<mmd:metadata_identifier></mmd:metadata_identifier>-->\n  <!--<mmd:data_access>')
            reference_string = reference_string.replace('</mmd:iso_topic_category>\n  '
                                                        '<mmd:keywords vocabulary="GCMD">\n    '
                                                        '<mmd:keyword>Earth Science &gt; Atmosphere &gt; Atmospheric radiation</mmd:keyword>\n  </mmd:keywords>\n  <mmd:use_constraint>','</mmd:iso_topic_category>\n  <mmd:use_constraint>')
            reference_string = reference_string.replace(
                '</mmd:metadata_identifier>-->\n  <!--<mmd:data_access>', '</mmd:metadata_identifier>-->\n  <!--<mmd:keywords>\n\t\t<mmd:keyword></mmd:keyword>\n\t</mmd:keywords>-->\n  <!--<mmd:data_access>')
            reference_string = reference_string.replace('<mmd:rectangle>', '<mmd:rectangle srsName="EPSG:4326">')
            tested_string = tested.read()
            unittest.TestCase.assertMultiLineEqual(self, first=reference_string, second=tested_string)

    def test_create_mmd_from_url(self):
        tested = tempfile.mkstemp()[1]
        self.maxDiff = None
        md = Nc_to_mmd('https://thredds.met.no/thredds/dodsC/remotesensingsatellite/polar-swath'
                       '/2020/11/27/npp-viirs-mband-20201127134002-20201127135124.nc', output_file=tested)
        md.to_mmd()
        with open(self.reference_xml) as reference, open(tested) as tested:
            reference_string = reference.read()
            reference_string = reference_string.replace('</mmd:title>\n  <!--<mmd:data_access>',
                                     '</mmd:title>\n  <mmd:data_access>\n    '
                                     '<mmd:type>OPeNDAP</mmd:type>\n    '
                                     '<mmd:description>Open-source Project for a Network Data '
                                     'Access Protocol</mmd:description>\n    '
                                     '<mmd:resource>https://thredds.met.no/thredds/dodsC'
                                     '/remotesensingsatellite/polar-swath/2020/11/27/npp-viirs'
                                     '-mband-20201127134002-20201127135124.nc</mmd:resource>\n  '
                                     '</mmd:data_access>\n  <mmd:data_access>\n    <mmd:type>OGC '
                                     'WMS</mmd:type>\n    <mmd:description>OGC Web Mapping '
                                     'Service, URI to GetCapabilities '
                                     'Document.</mmd:description>\n    '
                                     '<mmd:resource>https://thredds.met.no/thredds/wms'
                                     '/remotesensingsatellite/polar-swath/2020/11/27/npp-viirs'
                                     '-mband-20201127134002-20201127135124.nc?service=WMS&amp'
                                     ';version=1.3.0&amp;request=GetCapabilities</mmd:resource>\n '
                                     '   <mmd:wms_layers>\n      '
                                     '<mmd:wms_layer>M09</mmd:wms_layer>\n      '
                                     '<mmd:wms_layer>M01</mmd:wms_layer>\n      '
                                     '<mmd:wms_layer>M04</mmd:wms_layer>\n      '
                                     '<mmd:wms_layer>M02</mmd:wms_layer>\n      '
                                     '<mmd:wms_layer>M16</mmd:wms_layer>\n      '
                                     '<mmd:wms_layer>M13</mmd:wms_layer>\n      '
                                     '<mmd:wms_layer>M14</mmd:wms_layer>\n      '
                                     '<mmd:wms_layer>M12</mmd:wms_layer>\n      '
                                     '<mmd:wms_layer>M07</mmd:wms_layer>\n      '
                                     '<mmd:wms_layer>M10</mmd:wms_layer>\n      '
                                     '<mmd:wms_layer>M08</mmd:wms_layer>\n      '
                                     '<mmd:wms_layer>M15</mmd:wms_layer>\n      '
                                     '<mmd:wms_layer>M03</mmd:wms_layer>\n      '
                                     '<mmd:wms_layer>M05</mmd:wms_layer>\n      '
                                     '<mmd:wms_layer>M06</mmd:wms_layer>\n      '
                                     '<mmd:wms_layer>M11</mmd:wms_layer>\n    </mmd:wms_layers>\n '
                                     ' </mmd:data_access>\n  <mmd:data_access>\n    '
                                     '<mmd:type>HTTP</mmd:type>\n    <mmd:description>Open-source '
                                     'Project for a Network Data Access '
                                     'Protocol.</mmd:description>\n    '
                                     '<mmd:resource>https://thredds.met.no/thredds/fileServer'
                                     '/remotesensingsatellite/polar-swath/2020/11/27/npp-viirs'
                                     '-mband-20201127134002-20201127135124.nc</mmd:resource>\n  '
                                     '</mmd:data_access>\n  <!--<mmd:data_access>')
            tested_string = tested.read()
            unittest.TestCase.assertMultiLineEqual(self, first=reference_string, second=tested_string)

    def test_check_nc(self):
        md = Nc_to_mmd(self.reference_nc, check_only=True)
        self.assertTrue(md.to_mmd())


if __name__ == '__main__':
    unittest.main()
