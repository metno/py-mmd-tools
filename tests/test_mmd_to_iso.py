import tempfile
import os
import unittest
from py_mmd_tools.mmd_to_csw_iso import mmd_to_iso


class test_pymmdtools(unittest.TestCase):
    def setUp(self):
        # run this test from the tests directory by running:
        #
        # python3 test_mmd_to_iso.py
        #
        # or from the root directory by running:
        #
        # python3 -m unittest 
        #
        # unset the output limit when printing the xml diff
        #
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.reference_mmd = os.path.join(current_dir, 'data', 'reference_mmd.xml')
        self.reference_iso = os.path.join(current_dir, 'data', 'reference_iso.xml')
        self.mmd2iso_xslt = os.path.join(current_dir, 'data', 'mmd-to-iso.xsl')

    def test_mmd2iso(self):
        self.maxDiff = None
        tested = tempfile.mkstemp()[1]
        mmd_to_iso(
            mmd_file=self.reference_mmd,
            outputfile=tested,
            mmd2isocsw=self.mmd2iso_xslt,
        )
        with open(self.reference_iso) as reference, open(tested) as tested:
            reference_iso_string = reference.read()
            tested_string = tested.read()
            unittest.TestCase.assertMultiLineEqual(
                self, first=reference_iso_string, second=tested_string
            )

            
if __name__=='__main__':
    unittest.main()

