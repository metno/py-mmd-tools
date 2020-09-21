import tempfile
import unittest
import confuse
from py_mmd_tools.xml2xml import xml2xml


class test_pymmdtools(unittest.TestCase):
    def setUp(self):
        # Note:
        # The "confuse" library is used to pass the path string for static files
        # used to perform the test.
        #
        # On linux systems, by default, it reads a configuration file from:
        # $HOME/.config/appname/config.yaml (in this case appname=mdtool)
        #
        # The confuse configurationfile uses yaml syntax, example:
        #
        # """
        # paths:
        #     reference_mmd: 'path/to/reference_mmd.xml'
        #     reference_iso: 'path/to/reference_iso.xml'
        #     mmd2isocsw: 'path/to/mmd-to-iso.xsl'
        # """
        #
        # -- see the confuse documentation for more details. --
        #
        #
        # If you do not want (or can not) use the 'confuse' library,
        # replace the values of:
        #
        # reference_mmd
        # reference_iso
        # mmd2iso_xslt
        #
        # with the path strings to the files provided by your testing environment, and comment/remove the following lines:
        #
        # """
        # import confuse
        # config = confuse.Configuration('mmdtool', __name__)
        # """
        #
        # example file used in this test can be found at:
        # https://gist.github.com/934db4d3cf4e7a52985a3e231e0d36cf
        #
        # run this test from the module directory by running:
        #
        # python3 test_xml2xml.py
        #
        # unset the output limit when printing the xml diff
        #
        config = confuse.Configuration('mmdtool', __name__)
        self.reference_mmd = config['paths']['reference_mmd'].get()
        self.reference_iso = config['paths']['reference_iso'].get()
        self.mmd2iso_xslt = config['paths']['mmd2isocsw'].get()

    def test_xml2xml(self):
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

            
if __name__=='__main__':
    unittest.main()

