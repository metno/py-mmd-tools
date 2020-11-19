import unittest
import pathlib
from py_mmd_tools.check_mmd import check_rectangle, full_check
import lxml.etree as ET


class testMmdCheck(unittest.TestCase):
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
        self.doc = ET.ElementTree(file=self.reference_xml)

    # Check rom rectangle
    def test_full_check_1(self):
        self.assertTrue(full_check(self.doc))

    # Check lat/lon OK from rectangle
    def test_rectangle_1(self):
        root = self.doc.getroot()
        rect = self.doc.findall('./mmd:geographic_extent/mmd:rectangle', namespaces=root.nsmap)
        self.assertTrue(check_rectangle(rectangle=rect))

    # Check longitude NOK
    def test_rectangle_2(self):
        root = ET.Element("rectangle")
        ET.SubElement(root, "south").text = '20'
        ET.SubElement(root, "north").text = '50'
        ET.SubElement(root, 'west').text = '50'
        ET.SubElement(root, 'east').text = '0'
        self.assertFalse(check_rectangle([root]))

    # Check latitude NOK
    def test_rectangle_3(self):
        root = ET.Element("rectangle")
        ET.SubElement(root, "south").text = '-182'
        ET.SubElement(root, "north").text = '50'
        ET.SubElement(root, 'west').text = '0'
        ET.SubElement(root, 'east').text = '180'
        self.assertFalse(check_rectangle([root]))

    # Check more than one rectangle as input
    def test_rectangle_4(self):
        self.assertFalse(check_rectangle(['elem1', 'elem2']))


