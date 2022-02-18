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

    def test_update_nc_with_id_and_authority(self):
        """
        Test NC update with MMD where id is in the form naming_authority:id
        """
        tested = tempfile.mkstemp()[1]
        shutil.copy(self.orig_nc, tested)
        # Modify MMD input
        tree = ET.parse(self.reference_xml)
        id = tree.find('{*}metadata_identifier')
        id.text = 'no.met:456'
        modified_xml = tempfile.mkstemp()[1]
        tree.write(modified_xml, pretty_print=True)
        # Update NC file
        md = Mmd_to_nc(modified_xml, tested)
        md.update_nc()
        """ Get global attributes of updated nc file """
        with nc.Dataset(tested, 'r') as f:
            """ Check some fields"""
            self.assertEqual(f.getncattr('id'), '456')
            self.assertEqual(f.getncattr('naming_authority'), 'no.met')

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

    def test_update_nc_with_several_titles(self):
        """
        Test NC update with MMD where titles in different languages are present
        """
        tested = tempfile.mkstemp()[1]
        shutil.copy(self.orig_nc, tested)
        # Modify MMD input
        tree = ET.parse(self.reference_xml)
        root = tree.getroot()
        XHTML = "{http://www.met.no/schema/mmd}"
        title_no = ET.SubElement(root, XHTML + "title")
        title_no.text = 'Min norske tittel'
        title_no.set('{whatever}lang', 'no')
        title_fr = ET.SubElement(root, XHTML + "title")
        title_fr.text = 'Mon titre francais'
        title_fr.set('{whatever}lang', 'fr')
        modified_xml = tempfile.mkstemp()[1]
        tree.write(modified_xml, pretty_print=True)
        # Update NC file
        md = Mmd_to_nc(modified_xml, tested)
        md.update_nc()
        with nc.Dataset(tested, 'r') as f:
            """ Check fields in updated nc file """
            self.assertEqual(f.getncattr('title_no'), 'Min norske tittelen')

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
