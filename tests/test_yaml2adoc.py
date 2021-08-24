"""
License:

This file is part of the py-mmd-tools repository
<https://github.com/metno/py-mmd-tools>.

py-mmd-tools is licensed under the Apache License 2.0
<https://github.com/metno/py-mmd-tools/blob/master/LICENSE>
"""

import os, sys
import warnings
import types
import tempfile
import importlib.machinery

from unittest.mock import patch, Mock, DEFAULT
import unittest

#warnings.simplefilter("ignore", ResourceWarning)

class TestYAML2ADOC(unittest.TestCase):

    def setUp(self):
        file = globals()['__file__'].split('/')
        file.pop(-1)
        file.pop(-1)
        file.pop(0)
        ss = '/'
        for folder in file:
            ss = os.path.join(ss, folder)
        self.ss = os.path.join(ss, 'script/yaml2adoc')
        self.loader = importlib.machinery.SourceFileLoader('yaml2adoc', self.ss)
        y2a_mod = types.ModuleType(self.loader.name)


    def test_missing_args(self):
        warnings.filterwarnings('ignore')
        yy = self.loader.load_module()
        with patch.object(sys, 'argv', [self.ss]):
            with self.assertRaises(SystemExit) as cm:
                yy.main()
                self.assertEqual(cm.exception.code, 2)

    def test_create_file(self):
        tested = tempfile.mkstemp()[1]
        warnings.filterwarnings('ignore')
        yy = self.loader.load_module()
        with patch.object(sys, 'argv', [self.ss, '-o', '%s' %tested]):
            yy.main()
        with open(tested) as tt:
            first_line = tt.readline()
        self.assertEqual(first_line, '//// \n')

if __name__ == '__main__':
    unittest.main()
