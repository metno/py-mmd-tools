import os
import tempfile
import unittest
import pathlib
from py_mmd_tools.xml_utils import xml_check, xsd_check, xml_translate_and_write, xml_translate
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
        self.reference_iso = str(current_dir / 'tests' / 'data' / 'reference_iso.xml')
        self.mmd2iso_xslt = str(current_dir / 'tests' / 'data' / 'mmd-to-iso.xsl')
        self.reference_xsd = os.path.join(os.environ['MMD_PATH'], 'xsd/mmd_strict.xsd')
        self.not_a_file = str(current_dir / 'tests' / 'data' / 'not_a_file.xml')
        self.not_a_valid_xml = str(current_dir / 'tests' / 'data' / 'not_a_valid_xml.xml')
        self.not_a_valid_mmd = str(current_dir / 'tests' / 'data' / 'not_a_valid_mmd.xml')
 
    def test_xml_translate_and_write__raises_exception(self):
        tested = tempfile.mkstemp()[1]
        self.assertRaises(Exception, xml_translate_and_write, self.not_a_valid_mmd, tested, self.mmd2iso_xslt, True, self.reference_xsd)

    def test_xml_check_assertTrue(self):
        self.assertTrue(xml_check(xml_file=self.reference_xml))

    def test_xml_check_assertRaises_FileNotFoundError(self):
        self.assertRaises(FileNotFoundError, xml_check, self.not_a_file)

    def test_xml_check_assertRaises_XMLSyntaxError(self):
        self.assertRaises(XMLSyntaxError, xml_check, self.not_a_valid_xml)        

    def test_xsl_check_assertTrue(self):
        self.assertTrue(xsd_check(self.reference_xml, self.reference_xsd)[0])

    def test_xsl_check_assertRaises_XMLSyntaxError_opt_xslschema(self):
        self.assertRaises(XMLSyntaxError, xsd_check, self.reference_xml, 
                                                    self.not_a_valid_xml)

    def test_xsl_check_assertRaises_OSError_opt_xslschema(self):
        self.assertRaises(OSError, xsd_check, self.reference_xml, 
                                                    self.not_a_file)

    def test_xsl_check_assertRaises_XMLSyntaxError_opt_xmlfile(self):
        self.assertRaises(XMLSyntaxError, xsd_check, self.not_a_valid_xml, 
                                                    self.reference_xsd)

    def test_xsl_check_assertRaises_OSError_opt_xmlfile(self):
        self.assertRaises(OSError, xsd_check, self.not_a_file, 
                                                    self.not_a_file)                               

    def test_xml_translate_and_write_assertMultiLineEqual_validation_false(self):
        self.maxDiff = None
        tested = tempfile.mkstemp()[1]
        xml_translate_and_write(
            xml_file=self.reference_xml,
            outputfile=tested,
            xslt=self.mmd2iso_xslt,
        )
        with open(self.reference_iso) as reference, open(tested) as tested:
            reference_iso_string = reference.read()
            tested_string = tested.read()
            unittest.TestCase.assertMultiLineEqual(
                self, first=reference_iso_string, second=tested_string
            ) 

    def test_xml_translate_and_write_assertMultiLineEqual_validation_true(self):
        self.maxDiff = None
        tested = tempfile.mkstemp()[1]
        xml_translate_and_write(
            xml_file=self.reference_xml,
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

    def test_xml_translate_and_write_assertRaises_FileNotFoundError_opt_xmlfile(self):
        self.maxDiff = None
        tested = tempfile.mkstemp()[1]
        self.assertRaises(FileNotFoundError, 
                            xml_translate_and_write, 
                            self.not_a_file, 
                            tested, 
                            self.mmd2iso_xslt, 
                            True, 
                            self.reference_xsd) 

    def test_xml_translate__assertRaises_FileNotFoundError_opt_xml(self):
        self.assertRaises(FileNotFoundError, xml_translate, self.not_a_file, self.mmd2iso_xslt)

    def test_xml_translate__assertRaises_FileNotFoundError_opt_xslt(self):
        self.assertRaises(FileNotFoundError, xml_translate, self.reference_xml, self.not_a_file)

    def test_xml_translate_and_write_assertRaises_FileNotFoundError_opt_xslt(self):
        self.maxDiff = None
        tested = tempfile.mkstemp()[1]
        self.assertRaises(FileNotFoundError, xml_translate_and_write, self.reference_xml, tested, self.not_a_file, True, self.reference_xsd)

    def test_xml_translate_and_write_assertRaises_FileNotFoundError_opt_xsdschema(self):
        self.maxDiff = None
        tested = tempfile.mkstemp()[1]
        self.assertRaises(FileNotFoundError, xml_translate_and_write, self.reference_xml, tested, self.mmd2iso_xslt, True, self.not_a_file)

    def test_xml_translate_and_write_assertRaises_TypeError(self):
        self.maxDiff = None
        tested = tempfile.mkstemp()[1]
        self.assertRaises(TypeError, xml_translate_and_write, self.reference_xml, tested, self.mmd2iso_xslt, True)

if __name__=='__main__':
    unittest.main()

