import tempfile
import unittest
from mmd_to_csw_iso import mmd_to_iso
import confuse


class test_pymmdtools(unittest.TestCase):
    def test_mmd2iso(self):
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
        # python3 -m unittest test_mmdtoiso.py
        #
        config = confuse.Configuration("mmdtool", __name__)
        reference_mmd = config["paths"]["reference_mmd"].get()
        reference_iso = config["paths"]["reference_iso"].get()
        mmd2iso_xslt = config["paths"]["mmd2isocsw"].get()
        # unset the output limit when printing the xml diff
        self.maxDiff = None
        tested = tempfile.mkstemp()[1]
        mmd_to_iso(
            mmd_file=reference_mmd,
            outputfile=tested,
            mmd2isocsw=mmd2iso_xslt,
        )
        with open(reference_iso) as reference, open(tested) as tested:
            reference_iso_string = reference.read()
            tested_string = tested.read()
            unittest.TestCase.assertMultiLineEqual(
                self, first=reference_iso_string, second=tested_string
            )

