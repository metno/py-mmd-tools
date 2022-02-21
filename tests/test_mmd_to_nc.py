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

    def test_update_nc_with_dataset_citation(self):
        """
        Test NC update with MMD where dataset_citation is present
        """
        tested = tempfile.mkstemp()[1]
        shutil.copy(self.orig_nc, tested)
        # Modify MMD input
        tree = ET.parse(self.reference_xml)
        root = tree.getroot()
        XHTML = "{http://www.met.no/schema/mmd}"
        citation = ET.SubElement(root, XHTML + "dataset_citation")
        ET.SubElement(citation, XHTML + "publication_date").text = '2021-09-15'
        ET.SubElement(citation, XHTML + "author").text = 'toto'
        modified_xml = tempfile.mkstemp()[1]
        tree.write(modified_xml, pretty_print=True)
        # Update NC file
        md = Mmd_to_nc(modified_xml, tested)
        md.update_nc()

    def test_update_nc_with_activity_type(self):
        """
        Test NC update with MMD where dataset_citation is present
        """
        tested = tempfile.mkstemp()[1]
        shutil.copy(self.orig_nc, tested)
        # Modify MMD input
        tree = ET.parse(self.reference_xml)
        root = tree.getroot()
        XHTML = "{http://www.met.no/schema/mmd}"
        ET.SubElement(root, XHTML + "activity_type").text = 'Climate Indicator'
        modified_xml = tempfile.mkstemp()[1]
        tree.write(modified_xml, pretty_print=True)
        # Update NC file
        md = Mmd_to_nc(modified_xml, tested)
        md.update_nc()
        with nc.Dataset(tested, 'r') as f:
            """ Check fields in updated nc file """
            self.assertEqual(f.getncattr('source'), 'Climate Indicator')

    def test_update_nc_with_keyword_resource(self):
        """
        Test NC update with MMD where keyword resource is present
        """
        tested = tempfile.mkstemp()[1]
        shutil.copy(self.orig_nc, tested)
        # Modify MMD input
        tree = ET.parse(self.reference_xml)
        XHTML = "{http://www.met.no/schema/mmd}"
        keyword = tree.find('{*}keywords')
        resource = ET.SubElement(keyword, XHTML + "resource")
        resource.text = 'http://inspire.ec.europa.eu'
        modified_xml = tempfile.mkstemp()[1]
        tree.write(modified_xml, pretty_print=True)
        # Update NC file
        md = Mmd_to_nc(modified_xml, tested)
        md.update_nc()

    def test_title_abstract(self):
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

    def test_personnel_1(self):
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

    def test_personnel_2(self):
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

    def test_dataset_citation(self):
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

    def test_last_metadata_update(self):
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
