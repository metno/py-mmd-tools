import tempfile
import unittest
import pathlib
from py_mmd_tools.xml_util import xml_check, xsd_check
from lxml.etree import XMLSyntaxError


class test_pymmdtools(unittest.TestCase):
    def setUp(self):
        #
        # run this test from the root directory by running:
        #
        # python3 -m unittest 
        #
        # unset the output limit when printing the xml diff
        #
        current_dir = pathlib.Path.cwd()
        self.reference_xml = str(current_dir / 'tests' / 'data' / 'reference_mmd.xml')
        self.reference_xsd = str(current_dir / 'tests' / 'data' / 'mmd.xsd')
        self.not_a_file = str(current_dir / 'tests' / 'data' / 'not_a_file.xml')
        self.not_a_valid_xml = str(current_dir / 'tests' / 'data' / 'not_a_valid_xml.xml')
 
    def test_xml_check_1(self):
        unittest.TestCase.assertEqual(self, xml_check(xml_file=self.reference_xml), 
                                    True)

    def test_xml_check_2(self):
        self.assertRaises(FileNotFoundError, xml_check, self.not_a_file)

    def test_xml_check_3(self):
        self.assertRaises(XMLSyntaxError, xml_check, self.not_a_valid_xml)        

    def test_xsl_check_1(self):
        unittest.TestCase.assertEqual(self, xsd_check(xml_file=self.reference_xml, 
                                                    xsd_schema=self.reference_xsd), 
                                    True)

    def test_xsl_check_2(self):
        self.assertRaises(XMLSyntaxError, xsd_check, self.reference_xml, 
                                                    self.not_a_valid_xml)

    def test_xsl_check_3(self):
        self.assertRaises(FileNotFoundError, xsd_check, self.reference_xml, 
                                                    self.not_a_file)

            
if __name__=='__main__':
    unittest.main()

