# TODO: need to write unint test to:
# - assert proper conversion is performed, it requires:
#       - oda default file, 
#       - oda template file,
#       - json example file,
#       - trusted and validated conversion of the mmd example file
# - generarted output is a valid mmd (requires mmd xsd schema file)

import unittest
import pathlib
from unittest import mock

from py_mmd_tools import odajson_to_mmd

class TestJSON2MMD(unittest.TestCase):

    @mock.patch('py_mmd_tools.odajson_to_mmd.main')
    def test__main_with_defaults(self, mock_main):
        mock_main.return_value = None
        odajson_to_mmd.main()
        self.assertTrue(mock_main.called)

    #def test_exists_default_metadata(self):
    #def test_exists_template_mmd(self):

    def test_lowercase(self):
        dictin = {'Toto': 'TOTO', 'tata': 2, 'TUTU': 'Hello'}
        self.assertEqual(odajson_to_mmd._lowercase(dictin), {'toto': 'TOTO', 'tata': 2, 'tutu': 'Hello'})
        dictin = [{'Toto': 'TOTO', 'tata': 2, 'TUTU': 'Hello'}]
        self.assertEqual(odajson_to_mmd._lowercase(dictin), dictin)

    def test_merge_dicts(self):
        # simple merge
        dict1 = {'A': 1, 'B': 2}
        dict2 = {'A': 2, 'C': 3}  
        odajson_to_mmd._merge_dicts(dict1, dict2)
        self.assertEqual(dict1, {'A': 2, 'B': 2, 'C': 3})
        # nested dictionaries
        dict1 = {'A': 1, 'B': {'B1': 5, 'B2': 6}}
        dict2 = {'A': 2, 'C': 3, 'B': {'B1': 7}} 
        odajson_to_mmd._merge_dicts(dict1, dict2)
        self.assertEqual(dict1, {'A': 2, 'B':{'B1': 7, 'B2': 6}, 'C': 3})
        # one dictionary key in dict1 is not a dict, but same key in dict2 is a dict
        # -> raise Error
        dict1 = {'A': 1, 'B': {'B1': 5, 'B2': 6}}
        dict2 = {'A': 2, 'C': 3, 'B': 7} 
        with self.assertRaises(TypeError) as context:
            odajson_to_mmd._merge_dicts(dict1, dict2)
        # one dictionary key in dict2 is not a dict, but same key in dict1 is a dict
        # -> raise Error
        dict1 = {'A': 2, 'C': 3, 'B': 7} 
        dict2 = {'A': 1, 'B': {'B1': 5, 'B2': 6}}
        with self.assertRaises(TypeError) as context:
            odajson_to_mmd._merge_dicts(dict1, dict2)


    # test main -> if input == FROST
    @mock.patch('py_mmd_tools.odajson_to_mmd.process_file')
    @mock.patch('py_mmd_tools.odajson_to_mmd.process_all')
    def test_main_with_frost(self, mock_from_frost, mock_from_file):
        odajson_to_mmd.main(input_data='FROST', outdir='toto', oda_default=pathlib.Path("/home/elodief/Work/my_repos/py-mmd-tools_github/templates/oda_default.yml"), oda_mmd_template=pathlib.Path('/home/elodief/Work/my_repos/py-mmd-tools_github/templates/oda_to_mmd_template.xml'), validate=False, mmd_schema=None)
        mock_from_frost.assert_called()
        mock_from_file.assert_not_called()
        #self.assertTrue(mock_from_file.called)
        #self.assertTrue(mock_from_frost.called)

    # test main -> if input == a Jason file 
    @mock.patch('py_mmd_tools.odajson_to_mmd.process_file')
    @mock.patch('py_mmd_tools.odajson_to_mmd.process_all')
    def test_main_with_frost(self, mock_from_frost, mock_from_file):
        odajson_to_mmd.main(input_data=pathlib.Path('/home/elodief/Work/Data/mmd/input/example_oda.json'), outdir='toto', oda_default=pathlib.Path("/home/elodief/Work/my_repos/py-mmd-tools_github/templates/oda_default.yml"), oda_mmd_template=pathlib.Path('/home/elodief/Work/my_repos/py-mmd-tools_github/templates/oda_to_mmd_template.xml'), validate=False, mmd_schema=None)
        mock_from_frost.assert_not_called()
        mock_from_file.assert_called()


        ##@patch('mmd_utils.nc_to_mmd.Nc_to_mmd.__init__')
        ##@patch('mmd_utils.nc_to_mmd.Nc_to_mmd.to_mmd')
        ##def test__main_with_defaults(self, mock_to_mmd, mock_init):
        ##    mock_init.return_value = None
        ##    main_nc_to_mmd()
        ##    self.assertTrue(mock_init.called)
        ##    self.assertTrue(mock_to_mmd.called)

if __name__ == '__main__':
    unittest.main()

