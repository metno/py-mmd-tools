import tempfile
import unittest
import pathlib
from py_mmd_tools.xml2xml import xml2xml
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
        self.reference_mmd = str(current_dir / 'tests' / 'data' / 'reference_mmd.xml')
        self.reference_iso = str(current_dir / 'tests' / 'data' / 'reference_iso.xml')
        self.mmd2iso_xslt = str(current_dir / 'tests' / 'data' / 'mmd-to-iso.xsl')
        self.reference_xsd = str(current_dir / 'tests' / 'data' / 'mmd.xsd')
        self.not_a_file = str(current_dir / 'tests' / 'data' / 'not_a_file.xml')
        self.not_a_valid_xml = str(current_dir / 'tests' / 'data' / 'not_a_valid_xml.xml')

    def test_xml2xml_1(self):
        self.maxDiff = None
        tested = tempfile.mkstemp()[1]
        xml2xml(
            xml_file=self.reference_mmd,
            outputfile=tested,
            xslt=self.mmd2iso_xslt,
        )
        with open(self.reference_iso) as reference, open(tested) as tested:
            reference_iso_string = reference.read()
            tested_string = tested.read()
            unittest.TestCase.assertMultiLineEqual(
                self, first=reference_iso_string, second=tested_string
            ) 

    def test_xml2xml_2(self):
        self.maxDiff = None
        tested = tempfile.mkstemp()[1]
        xml2xml(
            xml_file=self.reference_mmd,
            outputfile=tested,
            xslt=self.mmd2iso_xslt,
            xsd_validation=True,
            xsd_schema=self.reference_xsd,
        )
        with open(self.reference_iso) as reference, open(tested) as tested:
            reference_iso_string = reference.read()
            tested_string = tested.read()
            unittest.TestCase.assertMultiLineEqual(self, 
                                                    first=reference_iso_string, 
                                                    second=tested_string
                                                    )

    def test_xml2xml_3(self):
        self.maxDiff = None
        tested = tempfile.mkstemp()[1]
        self.assertRaises(FileNotFoundError, 
                            xml2xml, 
                            self.not_a_file, 
                            tested, 
                            self.mmd2iso_xslt, 
                            True, 
                            self.reference_xsd) 


    def test_xml2xml_4(self):
        self.maxDiff = None
        tested = tempfile.mkstemp()[1]
        self.assertRaises(FileNotFoundError, xml2xml, self.reference_mmd, tested, self.mmd2iso_xslt, True, self.not_a_file)

    def test_xml2xml_5(self):
        self.maxDiff = None
        tested = tempfile.mkstemp()[1]
        self.assertRaises(TypeError, xml2xml, self.reference_mmd, tested, self.mmd2iso_xslt, True)

if __name__=='__main__':
    unittest.main()

