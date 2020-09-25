import tempfile
import unittest
import pathlib
import confuse
import logging
from py_mmd_tools.log_util import get_logpath, setup_log

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
        # self.not_a_dir = pathlib.Path(current_dir) / 'tests' / 'data' / 'not_a_dir'

    def test_get_logpath_1(self):
        logpath = get_logpath()
        unittest.TestCase.assertEqual(self, pathlib.Path(logpath).is_dir(), 
                                    True)

    def test_get_logpath_2(self):
        logpath = get_logpath(config_name='config_test')
        unittest.TestCase.assertEqual(self, pathlib.Path(logpath).is_dir(), 
                                    True)

    def test_setup_log_1(self):
        unittest.TestCase.assertEqual(self, type(setup_log('test')), 
                                    type(logging.getLogger('test')))

    def test_setup_log_2(self):
        unittest.TestCase.assertEqual(self, type(setup_log('test', logtype='stream')), 
                                    type(logging.getLogger('test')))

    def test_setup_log_3(self):
        unittest.TestCase.assertEqual(self, type(setup_log('test', logtype='file')), 
                                    type(logging.getLogger('test')))