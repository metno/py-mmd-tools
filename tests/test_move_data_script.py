"""
License:

This file is part of the py-mmd-tools repository
<https://github.com/metno/py-mmd-tools>.

py-mmd-tools is licensed under the Apache License 2.0
<https://github.com/metno/py-mmd-tools/blob/master/LICENSE>
"""
import os
import pytest
import subprocess

from py_mmd_tools.script.move_data import main
from py_mmd_tools.script.move_data import create_parser


@pytest.mark.script
def test_main(dataDir, monkeypatch):
    """
    """
    mmd_repository_path = "/some/folder/mmd-xml-production"
    new_file_location_base = "/some/where/new"
    existing_pathname_pattern = os.path.join(dataDir, "reference_nc.nc")
    parser = create_parser()
    parsed = parser.parse_args([
        mmd_repository_path,
        new_file_location_base,
        existing_pathname_pattern
    ])

    class MockResponse:

        status_code = 200

    with monkeypatch.context() as mp:
        mp.setattr("py_mmd_tools.mmd_operations.os.path.isdir",
                   lambda *a, **k: True)
        mp.setattr("py_mmd_tools.mmd_operations.new_file_location",
                   lambda *a, **k: new_file_location_base)
        mp.setattr("py_mmd_tools.mmd_operations.get_local_mmd_git_path",
                   lambda *a, **k: os.path.join(dataDir, "reference_nc.xml"))
        mp.setattr("py_mmd_tools.mmd_operations.shutil.move",
                   lambda *a, **k: None)
        mp.setattr("py_mmd_tools.mmd_operations.requests.get",
                   lambda *a, **k: MockResponse())
        mp.setattr("py_mmd_tools.mmd_operations.requests.post",
                   lambda *a, **k: MockResponse())
        main(parsed)

        mp.setattr("py_mmd_tools.mmd_operations.os.path.isdir",
                   lambda *a, **k: False)
        with pytest.raises(ValueError):
            main(parsed)

        map = {
            mmd_repository_path: True,
            new_file_location_base: False
        }

        def mock_isdir(pp):
            return map[pp]

        mp.setattr("py_mmd_tools.mmd_operations.os.path.isdir", mock_isdir)
        with pytest.raises(ValueError):
            main(parsed)

    subprocess.run(["git", "restore", "tests/data/reference_nc.xml"])
