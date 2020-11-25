import unittest
import pathlib
from py_mmd_tools.check_mmd import check_rectangle, check_urls, check_cf, full_check
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
        self.etree_ref = ET.ElementTree(ET.XML(
            "<root>"
            "<a x='123'>https://www.met.no</a>"
            "<geographic_extent>"
            "<rectangle>"
            "<north>76.199661</north>"
            "<south>71.63427</south>"
            "<west>-28.114723</west>"
            "<east>-11.169785</east>"
            "</rectangle>"
            "</geographic_extent>"
            "</root>"))
        self.etree_url_rect_nok = ET.ElementTree(ET.XML(
            "<root>"
            "<a x='123'>https://www.met.not</a>"
            "<geographic_extent>"
            "<rectangle>"
            "<north>76.199661</north>"
            "<south>71.63427</south>"
            "<west>-28.114723</west>"
            "</rectangle>"
            "</geographic_extent>"
            "<keywords vocabulary='Climate and Forecast Standard Names'>"
            "<keyword>sea_surface_temperature</keyword>"
            "<keyword>air_surface_temperature</keyword>"
            "</keywords>"
            "</root>"))
        self.etree_ref_empty = ET.ElementTree(ET.XML(
            "<root>"
            "<a x='123'>'xxx'/><c/><b/></a>"
            "</root>"))

    # Full check
    def test_full_check_1(self):
        self.assertTrue(full_check(self.etree_ref))

    # Full check with no elements to check
    def test_full_check_2(self):
        self.assertTrue(full_check(self.etree_ref_empty))

    # Full check with invalid elements
    def test_full_check_3(self):
        self.assertFalse(full_check(self.etree_url_rect_nok))

    # Check both valid and invalid URLs
    def test_all_urls_1(self):
        self.assertTrue(check_urls(['https://www.met.no']))
        self.assertFalse(check_urls(['http://met.not']))

    # Check lat/lon OK from rectangle
    def test_rectangle_1(self):
        rect = self.etree_ref.findall('./{*}geographic_extent/{*}rectangle')
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

    # Check lat & long OK with namespace
    def test_rectangle_5(self):
        root = ET.Element("rectangle")
        ET.SubElement(root, '{http://www.met.no/schema/mmd}south').text = '20'
        ET.SubElement(root, '{http://www.met.no/schema/mmd}north').text = '50'
        ET.SubElement(root, '{http://www.met.no/schema/mmd}west').text = '50'
        ET.SubElement(root, '{http://www.met.no/schema/mmd}east').text = '0'
        self.assertFalse(check_rectangle([root]))

    # One real standard name and one fake
    def test_cf_1(self):
        self.assertTrue(check_cf(['sea_surface_temperature']))
        self.assertFalse(check_cf(['sea_surace_temperature']))

    # Twice the element keywords for the same vocabulary
    def test_cf_2(self):
        root = ET.Element("toto")
        key1 = ET.SubElement(root, "keywords", vocabulary='Climate and Forecast Standard Names')
        ET.SubElement(key1, "keyword").text = 'air_temperature'
        key2 = ET.SubElement(root, "keywords", vocabulary='Climate and Forecast Standard Names')
        ET.SubElement(key2, "keyword").text = 'air_temperature'
        self.assertFalse(full_check(root))

    # Correct case
    def test_cf_3(self):
        root = ET.Element("toto")
        root1 = ET.SubElement(root, "keywords", vocabulary='Climate and Forecast Standard Names')
        ET.SubElement(root1, "keyword").text = 'sea_surface_temperature'
        self.assertTrue(full_check(root))

    # Two standard names provided
    def test_cf_4(self):
        root = ET.Element("toto")
        root1 = ET.SubElement(root, "keywords", vocabulary='Climate and Forecast Standard Names')
        ET.SubElement(root1, "keyword").text = 'air_temperature'
        ET.SubElement(root1, "keyword").text = 'sea_surface_temperature'
        self.assertFalse(full_check(root))
