"""
License:

This file is part of the py-mmd-tools repository
<https://github.com/metno/py-mmd-tools>.

py-mmd-tools is licensed under the Apache License 2.0
<https://github.com/metno/py-mmd-tools/blob/master/LICENSE>
"""

import os
import warnings
import tempfile

import pytest

from script.yaml2adoc import create_parser
from script.yaml2adoc import main


@pytest.mark.script
def test_yaml2adoc_script():
    """Test that an adoc file is created"""
    parser = create_parser()
    fd, tested = tempfile.mkstemp()
    parsed = parser.parse_args(['-o', tested])
    main(parsed)
    assert os.path.isfile(tested)
    os.close(fd)
    os.unlink(tested)


@pytest.mark.script
def test_missing_args():
    """Test that SystemExit is raised if no args"""
    warnings.filterwarnings('ignore')
    parser = create_parser()
    parsed = parser.parse_args([])
    with pytest.raises(SystemExit) as cm:
        main(parsed)
        assert cm.exception.code == 2


@pytest.mark.script
def test_create_file():
    """Test that the output file is created and populated"""
    fd, tested = tempfile.mkstemp()
    parser = create_parser()
    parsed = parser.parse_args(['-o', tested])
    main(parsed)
    with open(tested, 'r') as tt:
        first_line = tt.readline()
    assert first_line == '//// \n'
    os.close(fd)
    os.unlink(tested)
