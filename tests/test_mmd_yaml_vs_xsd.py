import os
import yaml
from pkg_resources import resource_string
import xmltodict
import unittest

import py_mmd_tools

#class ParametrizedTestCase(unittest.TestCase):
#    """ TestCase classes that want to be parametrized should
#        inherit from this class.
#    """
#    def __init__(self, methodName='runTest', xsd_eattr=None, yaml_eattr=None):
#        super(ParametrizedTestCase, self).__init__(methodName)
#        self.xsd_eattr = xsd_eattr
#        self.yaml_eattr = yaml_eattr
#
#    @staticmethod
#    def parametrize(testcase_class, xsd_eattr=None, yaml_eattr=None):
#        """ Create a suite containing all tests taken from the given
#            subclass, passing them the parameter 'param'.
#        """
#        testloader = unittest.TestLoader()
#        testnames = testloader.getTestCaseNames(testcase_class)
#        suite = unittest.TestSuite()
#        for name in testnames:
#            suite.addTest(testcase_class(name, xsd_eattr=xsd_eattr, yaml_eattr=yaml_eattr))
#        return suite
#
#class TestMMDYamlVsXSD(ParametrizedTestCase):
#
#    def test_element_attribute(self):
#        self.assertEqual(self.xsd_eattr, self.yaml_eattr)

class TestElementsExistInYAML(unittest.TestCase):

    def test_element_presence(self):
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

#suite = unittest.TestSuite()
#suite.addTest(ParametrizedTestCase.parametrize(TestMMDYamlVsXSD, xsd_eattr=42, yaml_eattr=42))
#suite.addTest(ParametrizedTestCase.parametrize(TestMMDYamlVsXSD, xsd_eattr=13, yaml_eattr=42))
#unittest.TextTestRunner(verbosity=2).run(suite)
