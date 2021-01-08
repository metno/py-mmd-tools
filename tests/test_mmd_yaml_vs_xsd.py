import os
import yaml
from pkg_resources import resource_string
import xmltodict
import unittest

import py_mmd_tools

class TestMDDElementsInYAMLAndXSD(unittest.TestCase):

    def test_mmd_element(self):
        xml_file = os.path.join(os.environ['MMD_PATH'], 'xsd/mmd.xsd')
        with open(xml_file) as xml:
            mmd_xml = xmltodict.parse(xml.read())

        mmd_yaml = yaml.load(resource_string(py_mmd_tools.__name__, 'mmd_elements.yaml'), Loader=yaml.FullLoader)

        # Get mmd_type elements
        ll = [x for x in mmd_xml['xs:schema']['xs:complexType'] if x['@name']=='mmd_type'][0]
        self.assertEqual(ll['@name'], 'mmd_type')
        # Loop MMD elements and check that they are present in the yaml file
        for elem in ll['xs:sequence']['xs:element']:
            self.assertIn(elem['@name'], mmd_yaml.keys())
            self.assertEqual(elem['@maxOccurs'], mmd_yaml[elem['@name']]['maxOccurs'], msg=elem['@name'])
            self.assertEqual(elem['@minOccurs'], mmd_yaml[elem['@name']]['minOccurs'], msg=elem['@name'])

        # Loop elements under xs:choice
        for elem in ll['xs:sequence']['xs:choice']['xs:element']:
            self.assertIn(elem['@name'], mmd_yaml.keys())
            self.assertEqual(elem['@maxOccurs'], mmd_yaml[elem['@name']]['maxOccurs'], msg=elem['@name'])
            self.assertEqual(elem['@minOccurs'], mmd_yaml[elem['@name']]['minOccurs'], msg=elem['@name'])

if __name__ == '__main__':
    unittest.main()
