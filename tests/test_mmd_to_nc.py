"""
License:

This file is part of the py-mmd-tools repository
<https://github.com/metno/py-mmd-tools>.

py-mmd-tools is licensed under the Apache License 2.0
<https://github.com/metno/py-mmd-tools/blob/master/LICENSE>
"""

import tempfile
import warnings
import unittest
import shutil
import pathlib

import netCDF4 as nc
import lxml.etree as ET
from py_mmd_tools.mmd_to_nc import Mmd_to_nc

warnings.simplefilter("ignore", ResourceWarning)


class TestMMD2NC(unittest.TestCase):

    def setUp(self):
        #
        # run this test from the root directory by running:
        #
        # python3 -m unittest
        #
        # unset the output limit when printing the xml diff
        #
        current_dir = pathlib.Path.cwd()
        self.orig_nc = str(current_dir / 'tests' / 'data' / 'nc_to_update.nc')
        self.reference_xml = str(current_dir / 'tests' / 'data' / 'reference_nc.xml')
        tree = ET.parse(self.reference_xml)
        self.tree = tree
        self.namespaces = tree.getroot().nsmap
        self.namespaces.update({'xml': 'http://www.w3.org/XML/1998/namespace'})

    def test_update_nc_1(self):
        """
        Test NC update from a valid MMD file and a valid NC file.
        Check some fields.
        """
        tested = tempfile.mkstemp()[1]
        shutil.copy(self.orig_nc, tested)
        md = Mmd_to_nc(self.reference_xml, tested)
        md.update_nc()
        """ Get global attributes of updated nc file """
        with nc.Dataset(tested, 'r') as f:
            """ Check some fields"""
            self.assertEqual(f.getncattr('id'), 'npp-viirs-mband-20201127134002-20201127135124')
            self.assertEqual(f.getncattr('institution'), 'MET NORWAY')

    def test_update_nc_2(self):
        """
        Test NC update from a valid MMD file and a valid NC file.
        Check that error is raised if an attribute is defined in both MMD and NC.
        """
        # Initialize
        md = Mmd_to_nc(self.reference_xml, self.orig_nc)
        tested = tempfile.mkstemp()[1]
        shutil.copy(self.orig_nc, tested)
        md = Mmd_to_nc(self.reference_xml, tested)
        # Add id attribute to nc file
        with nc.Dataset(tested, 'a') as f:
            f.id = 'my other id'
        # Check that error is raised
        self.assertRaises(Exception, lambda: md.update_nc())

    def test_process_title_and_abstract(self):
        """
        Test processing of title and abstract MMD elements with different languages.
        Only the English language ones should be translated to ACDD.
        """
        # Initialize
        md = Mmd_to_nc(self.reference_xml, self.orig_nc)
        XML = "{%s}" % self.namespaces['xml']
        MMD = "{%s}" % self.namespaces['mmd']
        # Create title element
        main = ET.Element(MMD+'mmd', nsmap=self.namespaces)
        title = ET.SubElement(main, MMD+'title')
        title.text = 'my title'
        # - Test 1: English language title
        title.set(XML+"lang", "en")
        md.process_title_and_abstract(title)
        # Expected output: English title added to ACDD attributes
        self.assertEqual(md.acdd_metadata['title'], 'my title')
        # - Test 2: Norwegian language title
        title.set(XML+"lang", "no")
        md.process_title_and_abstract(title)
        # Expected output: Norwegian title not added to ACDD attributes
        self.assertEqual(md.acdd_metadata['title'], 'my title')

    def test_process_personnel_1(self):
        """
        Test processing of personnel MMD element with the role Principal Investigator
        """
        # Initialize
        md = Mmd_to_nc(self.reference_xml, self.orig_nc)
        # Create personnel element
        MMD = "{%s}" % self.namespaces['mmd']
        main = ET.Element(MMD+'mmd', nsmap=self.namespaces)
        personnel = ET.SubElement(main, MMD+'personnel')
        # Children that should be translated to ACDD
        ET.SubElement(personnel, MMD+'role').text = 'Principal Investigator'
        ET.SubElement(personnel, MMD+'name').text = 'Pepito'
        # Children that should not be translated to ACDD
        ET.SubElement(personnel, MMD+'organisation').text = 'METNO'
        ET.SubElement(personnel, MMD+'phone').text = '41022512'
        ET.SubElement(personnel, MMD+'email').text = 'pepito@met.no'
        # Run and test
        md.process_personnel(personnel)
        self.assertRaises(KeyError, lambda: md.acdd_metadata['phone'])
        self.assertRaises(KeyError, lambda: md.acdd_metadata['contributor_email'])
        self.assertRaises(KeyError, lambda: md.acdd_metadata['creator_name'])
        self.assertRaises(KeyError, lambda: md.acdd_metadata['contributor_organisation'])
        self.assertEqual(md.acdd_metadata['contributor_name'], 'Pepito')
        self.assertEqual(md.acdd_metadata['contributor_role'], 'Principal Investigator')

    def test_process_personnel_2(self):
        """
        Test processing of personnel MMD element with the role Technical contact
        """
        # Initialize
        md = Mmd_to_nc(self.reference_xml, self.orig_nc)
        # Create personnel element
        MMD = "{%s}" % self.namespaces['mmd']
        main = ET.Element(MMD+'mmd', nsmap=self.namespaces)
        personnel = ET.SubElement(main, MMD+'personnel')
        # Children that should be translated to ACDD
        ET.SubElement(personnel, MMD+'role').text = 'Technical contact'
        ET.SubElement(personnel, MMD+'name').text = 'Pepito'
        ET.SubElement(personnel, MMD+'organisation').text = 'METNO'
        ET.SubElement(personnel, MMD+'email').text = 'pepito@met.no'
        # Child that should not be translated to ACDD
        ET.SubElement(personnel, MMD+'phone').text = '41022512'
        # Run and test
        md.process_personnel(personnel)
        self.assertRaises(KeyError, lambda: md.acdd_metadata['phone'])
        self.assertRaises(KeyError, lambda: md.acdd_metadata['contributor_name'])
        self.assertEqual(md.acdd_metadata['creator_name'], 'Pepito')
        self.assertEqual(md.acdd_metadata['creator_role'], 'Technical contact')
        self.assertEqual(md.acdd_metadata['creator_organisation'], 'METNO')
        self.assertEqual(md.acdd_metadata['creator_email'], 'pepito@met.no')

    def test_process_citation(self):
        """
        Test processing of dataset_citation MMD element
        """
        # Initialize
        md = Mmd_to_nc(self.reference_xml, self.orig_nc)
        # Create dataset_citation element
        MMD = "{%s}" % self.namespaces['mmd']
        main = ET.Element(MMD+'mmd', nsmap=self.namespaces)
        citation = ET.SubElement(main, MMD+'citation')
        # Children that should be ignored
        ET.SubElement(citation, MMD+'author').text = 'Toto'
        ET.SubElement(citation, MMD+'title').text = 'my title'
        # Children that should be translated to ACDD
        ET.SubElement(citation, MMD+'url').text = 'http://metadata.eu'
        ET.SubElement(citation, MMD+'other').text = 'Processed using my tool.'
        # Run and test
        md.process_citation(citation)
        self.assertRaises(KeyError, lambda: md.acdd_metadata['title'])
        self.assertRaises(KeyError, lambda: md.acdd_metadata['creator_name'])
        self.assertEqual(md.acdd_metadata['metadata_link'], 'http://metadata.eu')
        self.assertEqual(md.acdd_metadata['references'], 'Processed using my tool.')

    def test_process_last_metadata_update(self):
        """
        Test processing of last_metadata_update MMD element
        """
        # Initialize
        md = Mmd_to_nc(self.reference_xml, self.orig_nc)
        # Create last_metadata_update element
        MMD = "{%s}" % self.namespaces['mmd']
        main = ET.Element(MMD+'mmd', nsmap=self.namespaces)
        last_metadata_update = ET.SubElement(main, MMD+'last_metadata_update')
        update = ET.SubElement(last_metadata_update, MMD+'update')
        # Date should be translated to ACDD
        ET.SubElement(update, MMD+'datetime').text = '2022-02-18T13:09:44.299926+00:00'
        # Type should not be translated to ACDD
        ET.SubElement(update, MMD+'type').text = 'Created'
        # Run and test
        md.process_last_metadata_update(last_metadata_update)
        self.assertRaises(KeyError, lambda: md.acdd_metadata['date_metadata_modified_type'])
        self.assertEqual(md.acdd_metadata['date_metadata_modified'],
                         '2022-02-18T13:09:44.299926+00:00')

    def test_process_keywords_1(self):
        """
        Test processing of keywords MMD element
        """
        # Initialize
        md = Mmd_to_nc(self.reference_xml, self.orig_nc)
        # Create keywords element
        MMD = "{%s}" % self.namespaces['mmd']
        main = ET.Element(MMD+'mmd', nsmap=self.namespaces)
        keywords = ET.SubElement(main, MMD+'keywords')
        keywords.set("vocabulary", "CFSTDN")
        ET.SubElement(keywords, MMD+'keyword').text = 'precipitation_amount'
        ET.SubElement(keywords, MMD+'resource').text = \
            'https://cfconventions.org/standard-names.html'
        # Run and test
        md.process_keywords(keywords)
        self.assertEqual(md.acdd_metadata['keywords'], 'CFSTDN:precipitation_amount')
        self.assertEqual(md.acdd_metadata['keywords_vocabulary'],
                         'CFSTDN:https://cfconventions.org/standard-names.html')

    def test_process_keywords_2(self):
        """
        Test processing of several keywords MMD element
        """
        # Initialize
        md = Mmd_to_nc(self.reference_xml, self.orig_nc)
        # Create keywords element 1
        MMD = "{%s}" % self.namespaces['mmd']
        main = ET.Element(MMD+'mmd', nsmap=self.namespaces)
        keywords = ET.SubElement(main, MMD+'keywords')
        keywords.set("vocabulary", "CFSTDN")
        ET.SubElement(keywords, MMD+'keyword').text = 'precipitation_amount'
        ET.SubElement(keywords, MMD+'resource').text = \
            'https://cfconventions.org/standard-names.html'
        # Run on element 1
        md.process_keywords(keywords)
        # Create keywords element 2
        keywords = ET.SubElement(main, MMD+'keywords')
        keywords.set("vocabulary", "GEMET")
        ET.SubElement(keywords, MMD+'keyword').text = 'Atmospheric conditions'
        ET.SubElement(keywords, MMD+'resource').text = 'http://inspire.ec.europa.eu/theme'
        # Run on element 2 and test
        md.process_keywords(keywords)
        self.assertEqual(md.acdd_metadata['keywords'], 'CFSTDN:precipitation_amount,'
                                                       'GEMET:Atmospheric conditions')
        self.assertEqual(md.acdd_metadata['keywords_vocabulary'],
                         'CFSTDN:https://cfconventions.org/standard-names.html,'
                         'GEMET:http://inspire.ec.europa.eu/theme')

    def test_update_acdd_1(self):
        """
        Test updating of acdd dictionary - initialization
        """
        # Initialize
        md = Mmd_to_nc(self.reference_xml, self.orig_nc)
        # Run and test with empty acdd_metadata
        dict1 = {'id': '12345'}
        md.update_acdd(dict1)
        self.assertEqual(md.acdd_metadata['id'], '12345')

    def test_update_acdd_2(self):
        """
        Test updating of acdd dictionary - simple dictionary
        """
        # Initialize
        md = Mmd_to_nc(self.reference_xml, self.orig_nc)
        # Run and test with simple new dictionary acdd_metadata
        dict1 = {'id': '12345'}
        md.update_acdd(dict1)
        dict2 = {'author': 'me'}
        md.update_acdd(dict2)
        self.assertEqual(md.acdd_metadata['id'], '12345')
        self.assertEqual(md.acdd_metadata['author'], 'me')

    def test_update_acdd_3(self):
        """
        Test updating of acdd dictionary - append an existing key
        """
        # Initialize
        md = Mmd_to_nc(self.reference_xml, self.orig_nc)
        # Add simple new dictionary acdd_metadata
        dict1 = {'id': '12345'}
        md.update_acdd(dict1)
        # Add new dictionary with key already in acdd_metadata
        dict2 = {'id': '54321'}
        sep = {'id': ';'}
        md.update_acdd(dict2, sep)
        # Both values should be appended using separator
        self.assertEqual(md.acdd_metadata['id'], '12345;54321')
        # Add new dictionary with key already in acdd_metadata - but no separator given
        self.assertRaises(TypeError, lambda: md.update_acdd(dict2))

    def test_get_acdd(self):
        """
        Test function get_acdd, ie get an acdd translation.
        """
        # Initialize
        md = Mmd_to_nc(self.reference_xml, self.orig_nc)
        # Translation dictionary
        translation = {
            # Simple direct translation
            'metadata_identifier': {'acdd': 'id'},
            # MMD element with no ACDD translation
            'mmd_element_with_no_acdd_translation': {'acdd_ext': 'whatever'},
            # MMD element with several ACDD translations
            'mmd_element_with_list': {'acdd': ['translation_1', 'translation_2']},
            # MMD element with repetition allowed
            'mmd_element_with_repetition_allowed': {'acdd': 'whatever', 'separator': ';'}
        }
        # Test translation
        # Simple direct translation
        acdd, sep = md.get_acdd(translation['metadata_identifier'])
        self.assertEqual(acdd, 'id')
        self.assertIsNone(sep)
        # MMD element with no ACDD translation
        acdd, sep = md.get_acdd(translation['mmd_element_with_no_acdd_translation'])
        self.assertIsNone(acdd)
        self.assertIsNone(sep)
        # MMD element with several ACDD translations
        acdd, sep = md.get_acdd(translation['mmd_element_with_list'])
        self.assertEqual(acdd, 'translation_1')
        self.assertIsNone(sep)
        # MMD element with repetition allowed
        acdd, sep = md.get_acdd(translation['mmd_element_with_repetition_allowed'])
        self.assertEqual(acdd, 'whatever')
        self.assertEqual(sep, ';')
