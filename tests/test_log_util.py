import tempfile
import unittest
import pathlib
import logging
from py_mmd_tools.log_util import get_logpath, setup_log
import uuid 

class test_pymmdtools(unittest.TestCase):
    def setUp(self):
        #
        # run this test from the root directory by running:
        #
        # python3 -m unittest 
        #
        # unset the output limit when printing the xml diff
        #
        self.current_dir = pathlib.Path.cwd()
        self.not_a_writable_dir =  pathlib.Path('/') / pathlib.Path(uuid.uuid4().hex[:6].upper())
        # self.not_a_dir = pathlib.Path(current_dir) / 'tests' / 'data' / 'not_a_dir'

    def test_get_logpath_1(self):
        logpath = get_logpath(self.current_dir)
        unittest.TestCase.assertEqual(self, pathlib.Path(logpath).is_dir(), 
                                    True)

    # This works fine locally but fails on codecov:
    #
    # def test_get_logpath_2(self):
    #     self.assertRaises(IOError, get_logpath, self.not_a_writable_dir)

    def test_setup_log_1(self):
        unittest.TestCase.assertEqual(self, type(setup_log('test',  logdirpath=self.current_dir)), 
                                    type(logging.getLogger('test')))

    def test_setup_log_2(self):
        unittest.TestCase.assertEqual(self, type(setup_log('test', logdirpath=self.current_dir, logtype='stream')), 
                                    type(logging.getLogger('test')))

    def test_setup_log_3(self):
        unittest.TestCase.assertEqual(self, type(setup_log('test', logdirpath=self.current_dir, logtype='file')), 
                                    type(logging.getLogger('test')))