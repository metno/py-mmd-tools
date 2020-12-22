import unittest

class ParametrizedTestCase(unittest.TestCase):
    """ TestCase classes that want to be parametrized should
        inherit from this class.
    """
    def __init__(self, methodName='runTest', xsd_eattr=None, yaml_eattr=None):
        super(ParametrizedTestCase, self).__init__(methodName)
        self.xsd_eattr = xsd_eattr
        self.yaml_eattr = yaml_eattr

    @staticmethod
    def parametrize(testcase_class, xsd_eattr=None, yaml_eattr=None):
        """ Create a suite containing all tests taken from the given
            subclass, passing them the parameter 'param'.
        """
        testloader = unittest.TestLoader()
        testnames = testloader.getTestCaseNames(testcase_class)
        suite = unittest.TestSuite()
        for name in testnames:
            suite.addTest(testcase_class(name, xsd_eattr=xsd_eattr, yaml_eattr=yaml_eattr))
        return suite

class TestMMDYamlVsXSD(ParametrizedTestCase):

    def test_element_attribute(self):
        self.assertEqual(self.xsd_eattr, self.yaml_eattr)

suite = unittest.TestSuite()
suite.addTest(ParametrizedTestCase.parametrize(TestMMDYamlVsXSD, xsd_eattr=42, yaml_eattr=42))
suite.addTest(ParametrizedTestCase.parametrize(TestMMDYamlVsXSD, xsd_eattr=13, yaml_eattr=42))
unittest.TextTestRunner(verbosity=2).run(suite)
