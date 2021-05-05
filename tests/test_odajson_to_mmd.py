"""
 License:
     This file is part of the py-mmd-tools repository (https://github.com/metno/py-mmd-tools).
     py-mmd-tools is licensed under GPL-3.0 (
     https://github.com/metno/py-mmd-tools/blob/master/LICENSE)
"""

import unittest
import pathlib
import tempfile
import yaml
import json
import jinja2

from requests import Response
from requests.exceptions import HTTPError

from unittest.mock import patch, MagicMock, Mock
from unittest.mock import DEFAULT as mock_default
from py_mmd_tools import odajson_to_mmd


class TestODA2MMD(unittest.TestCase):

    def setUp(self):
        current_dir = pathlib.Path.cwd()
        self.reference_in_json = str(current_dir / 'tests' / 'data' / 'reference_json.json')
        self.reference_out_xml = str(current_dir / 'tests' / 'data' / 'reference_mmd_from_json.xml')
        self.xml_template = str(current_dir / 'templates' / 'oda_to_mmd_template.xml')

        env = jinja2.Environment(
            loader=jinja2.PackageLoader('py_mmd_tools', 'templates'),
            autoescape=jinja2.select_autoescape(['html', 'xml']),
            trim_blocks=True, lstrip_blocks=True
        )
        self.default = env.get_template('oda_default.yml').filename

        self.reference_xsd = str(current_dir / 'tests' / 'data' / 'mmd_strict.xsd')
        self.not_a_file = str(current_dir / 'tests' / 'data' / 'not_a_file.xml')
        self.json_with_invalid_elements = str(current_dir / 'tests' / 'data' / 'json_invalid_element.json')
        self.reference_oda_tag = {
                'Metadata_identifier': 564734243385966593,
                'Alternate_identifier': [
                    {'Identifier_type': 'StationID', 'Identifier': '18269'},
                    {'Identifier_type': 'ParameterID', 'Identifier': '106'},
                    {'Identifier_type': 'WigosID', 'Identifier': '0-578-0-18269'}
                ],
                'Last_metadata_update': '2020-09-15T08:35:50Z',
                'Collection': ['ODA'],
                'Temporal_extent': {
                    'Start_date': '2020-06-21T19:00:00Z',
                    'End_date': '2020-09-14T22:44:02Z'
                },
                'Geographic_extent': {
                    'Latitude_min': 59.9535,
                    'Latitude_max': 59.9535,
                    'Longitude_min': 10.9035,
                    'Longitude_max': 10.9035
                },
                'Production_status': 'open',
                'Operational_status': 'operational',
                'Access_constraint': '',
                'Related_information': [''],
                'Keyword': [
                    {'Keyword_type': 'CF name', 'Keywords': ['sum(precipitation_amount PT1H)']}
                ]
            }
        self.maxDiff = None

    def test_lowercase(self):
        dictin = {'Toto': 'TOTO', 'tata': 2, 'TUTU': 'Hello'}
        self.assertEqual(odajson_to_mmd._lowercase(dictin), {'toto': 'TOTO', 'tata': 2, 'tutu': 'Hello'})
        dictin = [{'Toto': 'TOTO', 'tata': 2, 'TUTU': 'Hello'}]
        self.assertEqual(odajson_to_mmd._lowercase(dictin), dictin)

    def test_merge_dicts(self):
        # simple merge
        dict1 = {'A': 1, 'B': 2}
        dict2 = {'A': 2, 'C': 3}
        odajson_to_mmd._merge_dicts(dict1, dict2)
        self.assertEqual(dict1, {'A': 2, 'B': 2, 'C': 3})
        # nested dictionaries
        dict1 = {'A': 1, 'B': {'B1': 5, 'B2': 6}}
        dict2 = {'A': 2, 'C': 3, 'B': {'B1': 7}}
        odajson_to_mmd._merge_dicts(dict1, dict2)
        self.assertEqual(dict1, {'A': 2, 'B': {'B1': 7, 'B2': 6}, 'C': 3})
        # one dictionary key in dict1 is not a dict, but same key in dict2 is a dict
        # -> raise Error
        dict1 = {'A': 1, 'B': {'B1': 5, 'B2': 6}}
        dict2 = {'A': 2, 'C': 3, 'B': 7}
        with self.assertRaises(TypeError) as context:
            odajson_to_mmd._merge_dicts(dict1, dict2)
        # one dictionary key in dict2 is not a dict, but same key in dict1 is a dict
        # -> raise Error
        dict1 = {'A': 2, 'C': 3, 'B': 7}
        dict2 = {'A': 1, 'B': {'B1': 5, 'B2': 6}}
        with self.assertRaises(TypeError) as context:
            odajson_to_mmd._merge_dicts(dict1, dict2)

    def test_to_mmd_1(self):
        # Standard use with Json file as input
        tested = tempfile.mkstemp()[1]
        odajson_to_mmd.to_mmd(input_data=self.reference_in_json, output_file=tested, template_file=self.xml_template)
        with open(self.reference_out_xml) as reference, open(tested) as tested:
            reference_iso_string = reference.read()
            tested_string = tested.read()
            unittest.TestCase.assertMultiLineEqual(self, first=reference_iso_string, second=tested_string)

    def test_to_mmd_2(self):
        # Standard use with dict as input
        tested = tempfile.mkstemp()[1]
        with open(self.reference_in_json, 'r') as file:
            dictin = json.load(file)
        odajson_to_mmd.to_mmd(
            input_data=dictin,
            output_file=tested,
            template_file=self.xml_template,
            xsd_validation=False,
            xsd_schema=self.reference_xsd,
        )
        with open(self.reference_out_xml) as reference, open(tested) as tested:
            reference_iso_string = reference.read()
            tested_string = tested.read()
            unittest.TestCase.assertMultiLineEqual(self, first=reference_iso_string, second=tested_string)

    def test_to_mmd_3(self):
        # Jason input file missing
        tested = tempfile.mkstemp()[1]
        self.assertRaises(TypeError, odajson_to_mmd.to_mmd, self.not_a_file, tested, self.xml_template)

    def test_to_mmd_4(self):
        # XML template missing
        tested = tempfile.mkstemp()[1]
        self.assertRaises(jinja2.exceptions.TemplateNotFound, odajson_to_mmd.to_mmd, self.reference_in_json, tested, self.not_a_file)

    def test_to_mmd_5(self):
        # Validation asked but no XSD schema provided
        tested = tempfile.mkstemp()[1]
        self.assertRaises(TypeError, odajson_to_mmd.to_mmd, self.reference_in_json, tested, self.xml_template,
                          xsd_validation=True)

    def test_to_mmd_6(self):
        # Validation asked but XSD schema not valid file
        tested = tempfile.mkstemp()[1]
        self.assertRaises(FileNotFoundError, odajson_to_mmd.to_mmd, self.reference_in_json, tested, self.xml_template,
                          xsd_validation=True, xsd_schema=self.not_a_file)

    def test_to_mmd_7(self):
        # Validation fails with input Json with invalid elements
        tested = tempfile.mkstemp()[1]
        self.assertIs(odajson_to_mmd.to_mmd(self.json_with_invalid_elements, tested,
                                            self.xml_template, xsd_validation=True, xsd_schema=self.reference_xsd), False)

    def test_prepare_elements_1(self):
        # Required element missing #1
        with open(self.default, 'r') as default_file:
            default = yaml.load(default_file.read(), Loader=yaml.SafeLoader)
        dataset = self.reference_oda_tag
        dataset.pop("Metadata_identifier")
        self.assertIsNone(odajson_to_mmd.prepare_elements(dataset, default))

    def test_prepare_elements_2(self):
        # Required element missing #2
        with open(self.default, 'r') as default_file:
            default = yaml.load(default_file.read(), Loader=yaml.SafeLoader)
        dataset = self.reference_oda_tag
        dataset['Temporal_extent'].pop("Start_date")
        self.assertIsNone(odajson_to_mmd.prepare_elements(dataset, default))

    def test_prepare_elements_3(self):
        # Variables lat/lon = default value
        with open(self.default, 'r') as default_file:
            default = yaml.load(default_file.read(), Loader=yaml.SafeLoader)
        dataset = self.reference_oda_tag
        dataset['Geographic_extent']['Latitude_max'] = 0.
        dataset['Geographic_extent']['Latitude_min'] = 0.
        dataset['Geographic_extent']['Longitude_max'] = 0.
        dataset['Geographic_extent']['Longitude_min'] = 0.
        out = odajson_to_mmd.prepare_elements(dataset, default)
        self.assertEqual(out['geographic_extent']['latitude_max'], default['geographic_extent']['latitude_max'])
        self.assertEqual(out['geographic_extent']['latitude_min'], default['geographic_extent']['latitude_min'])
        self.assertEqual(out['geographic_extent']['longitude_max'], default['geographic_extent']['longitude_max'])
        self.assertEqual(out['geographic_extent']['longitude_min'], default['geographic_extent']['longitude_min'])

    def test_prepare_elements_4(self):
        # Variable 'Production_status' set to sthg not in controlled vocabulary
        with open(self.default, 'r') as default_file:
            default = yaml.load(default_file.read(), Loader=yaml.SafeLoader)
        dataset = self.reference_oda_tag
        dataset['Production_status'] = 'Ongoing'
        self.assertIsNone(odajson_to_mmd.prepare_elements(dataset, default))

    def test_prepare_elements_5(self):
        # Variable 'Operational_status' set to default value
        with open(self.default, 'r') as default_file:
            default = yaml.load(default_file.read(), Loader=yaml.SafeLoader)
        dataset = self.reference_oda_tag
        dataset['Operational_status'] = ''
        out = odajson_to_mmd.prepare_elements(dataset, default)
        self.assertIs('operational_status' in out, False)

    def test_prepare_elements_6(self):
        # Variable 'Keyword' includes Keyword_type that is not CF
        with open(self.default, 'r') as default_file:
            default = yaml.load(default_file.read(), Loader=yaml.SafeLoader)
        dataset = self.reference_oda_tag
        dataset['Keyword'].append({'Keyword_type': 'other type', 'Keywords': [11, 22]})
        out = odajson_to_mmd.prepare_elements(dataset, default)
        self.assertEqual(out['keyword'], dataset['Keyword'])

    @patch('py_mmd_tools.odajson_to_mmd.to_mmd') # avoid writing files..
    @patch('py_mmd_tools.odajson_to_mmd.requests.Response')
    @patch('py_mmd_tools.odajson_to_mmd.requests.get')
    def test_process_station_1(self, mock_get, mock_response, mock_to_mmd):
        mock_response.json.return_value = [self.reference_oda_tag, self.reference_oda_tag]
        mock_get.return_value = mock_response
        odajson_to_mmd.process_station('18269', 'HAUGENSTUA', 'outdir', self.default,
                                                    self.xml_template, 'frost-staging.met.no')
        # Check request to end-point
        mock_get.assert_called_with(
            'https://frost-staging.met.no/api/v1/getlabels/mmd?stationid=18269', timeout=10)
        mock_to_mmd.assert_called()
        # Missing default file
        self.assertRaises(FileNotFoundError, odajson_to_mmd.process_station, '18269', 'HAUGENSTUA',
                        'outdir', self.not_a_file, self.xml_template, 'frost-staging.met.no')

    @patch('py_mmd_tools.odajson_to_mmd.to_mmd') # avoid writing files..
    def test_process_station_2(self, mock_to_mmd):
        # Non existing station
        outdir = tempfile.mkdtemp()
        self.assertFalse(odajson_to_mmd.process_station('AA', 'AA', outdir, self.default,
                                                    self.xml_template, 'frost-staging.met.no'))

    def test_retrieve_frost_stations__invalid_url(self):
        # Request with wrong URL
        self.assertRaises(HTTPError, odajson_to_mmd.retrieve_frost_stations,
                 'https://frost.met.no/sources/v.jsonld', 'id')

    def test_retrieve_frost_stations__invalid_id(self):
        # Request with wrong id
        self.assertRaises(HTTPError, odajson_to_mmd.retrieve_frost_stations,
            'https://frost.met.no/sources/v0.jsonld', 'incorrect_id')

    @patch('py_mmd_tools.odajson_to_mmd.requests.Response')
    @patch('py_mmd_tools.odajson_to_mmd.requests.get')
    def test_retrieve_frost_stations__valid(self, mock_get, mock_response):
        url = 'https://this.is.a.valid.url/v0.jsonld'
        id = 'id'
        mock_response.raise_for_status.return_value = 'hei'
        mock_response.json.return_value = {'data': ['one', 'two', 'three']}
        mock_get.return_value = mock_response
        # 
        self.assertEqual(odajson_to_mmd.retrieve_frost_stations(url, id)[0], 'one')
        self.assertEqual(odajson_to_mmd.retrieve_frost_stations(url, id)[1], 'two')
        self.assertEqual(odajson_to_mmd.retrieve_frost_stations(url, id)[2], 'three')

if __name__ == '__main__':
    unittest.main()
