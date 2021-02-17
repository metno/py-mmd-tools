"""
License:
     This file is part of the py-mmd-tools repository (https://github.com/metno/py-mmd-tools). py-mmd-tools is licensed under Apache License 2.0 (https://github.com/metno/py-mmd-tools/blob/master/LICENSE).
 """
import os, sys
import warnings
import types
import tempfile
import importlib.machinery

from unittest.mock import patch, Mock, DEFAULT
import unittest

#warnings.simplefilter("ignore", ResourceWarning)

file = globals()['__file__'].split('/')
file.pop(-1)
file.pop(-1)
file.pop(0)
ss = '/'
for folder in file:
    ss = os.path.join(ss, folder)
ss = os.path.join(ss, 'script/yaml2adoc')
loader = importlib.machinery.SourceFileLoader('yaml2adoc', ss)
y2a_mod = types.ModuleType(loader.name)

class TestYAML2ADOC(unittest.TestCase):

    def test_missing_args(self):
        warnings.filterwarnings('ignore')
        yy = loader.load_module()
        out = sys.stdout
        with self.assertRaises(SystemExit) as cm:
            yy.main()
        self.assertEqual(cm.exception.code, 2)

    def test_create_file(self):
        tested = tempfile.mkstemp()[1]
        warnings.filterwarnings('ignore')
        tmpargs = sys.argv
        sys.argv = [sys.argv[0]]
        sys.argv += ['-o', '%s' %tested]
        yy = loader.load_module()
        out = sys.stdout
        yy.main()
        sys.argv = tmpargs
        with open(tested) as tt:
            first_line = tt.readline()
        self.assertEqual(first_line, '//// \n')

if __name__ == '__main__':
    unittest.main()
