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


@pytest.mark.py_mmd_tools
def test_main(dataDir, monkeypatch, caplog):
    """
    """
    mmd_repository_path = "/some/folder/mmd-xml-production"
    old_file_location_base = os.path.join(dataDir, "reference_nc.nc")
    new_file_location_base = "/some/where/new"
    parser = create_parser()
    parsed = parser.parse_args([
        mmd_repository_path,
        old_file_location_base,
        new_file_location_base,
    ])

    class MockResponse:

        status_code = 200
        text = "OK"

    with monkeypatch.context() as mp:
        mp.setattr("py_mmd_tools.mmd_operations.os.path.isdir",
                   lambda *a, **k: True)
        mp.setattr("py_mmd_tools.mmd_operations.new_file_location",
                   lambda *a, **k: new_file_location_base)
        mp.setattr("py_mmd_tools.mmd_operations.get_local_mmd_git_path",
                   lambda *a, **k: os.path.join(dataDir, "reference_nc.xml"))
        mp.setattr("py_mmd_tools.mmd_operations.requests.get",
                   lambda *a, **k: MockResponse())
        mp.setattr("py_mmd_tools.mmd_operations.requests.post",
                   lambda *a, **k: MockResponse())
        mp.setattr("py_mmd_tools.mmd_operations.shutil.move", lambda *a, **k: None)
        mp.setattr("py_mmd_tools.mmd_operations.os.makedirs", lambda *a, **k: None)
        mp.setattr("py_mmd_tools.mmd_operations.os.access",
                   lambda *a, **k: True)
        u, n = main(parsed)
        assert len(u) == 1
        subprocess.run(["git", "restore", "tests/data/reference_nc.xml"])

        mp.setattr("py_mmd_tools.mmd_operations.os.path.isdir",
                   lambda *a, **k: False)
        with pytest.raises(ValueError):
            main(parsed)

        map = {
            mmd_repository_path: True,
            new_file_location_base: False,
        }

        def mock_isdir(pp):
            return map[pp]

        mp.setattr("py_mmd_tools.mmd_operations.os.path.isdir", mock_isdir)
        with pytest.raises(ValueError):
            main(parsed)

        map = {
            mmd_repository_path: True,
            new_file_location_base: True,
        }
        mp.setattr("py_mmd_tools.mmd_operations.os.path.isdir", mock_isdir)

        old_file_location_base = dataDir

        """ The following tests are basically testing datetime_glob.walk
        but are included anyway...
        """
        # Day as format code
        ext_pattern = "2024/09/%d/*.nc"
        parser = create_parser()
        parsed = parser.parse_args([
            mmd_repository_path,
            old_file_location_base,
            new_file_location_base,
            "--ext-pattern", ext_pattern,
        ])
        u, n = main(parsed)
        assert len(u) == 1

        subprocess.run(["git", "restore", "tests/data/reference_nc.xml"])

        # Month and day as format codes
        ext_pattern = "2024/%m/%d/*.nc"
        parser = create_parser()
        parsed = parser.parse_args([
            mmd_repository_path,
            old_file_location_base,
            new_file_location_base,
            "--ext-pattern", ext_pattern,
        ])
        u, n = main(parsed)
        assert len(u) == 1

        subprocess.run(["git", "restore", "tests/data/reference_nc.xml"])

        # Year, month and day as format codes
        ext_pattern = "%Y/%m/%d/*.nc"
        parser = create_parser()
        parsed = parser.parse_args([
            mmd_repository_path,
            old_file_location_base,
            new_file_location_base,
            "--ext-pattern", ext_pattern,
        ])
        u, n = main(parsed)
        assert len(u) == 1

        subprocess.run(["git", "restore", "tests/data/reference_nc.xml"])

        # Month as format code
        ext_pattern = "2024/%m/01/*.nc"
        parser = create_parser()
        parsed = parser.parse_args([
            mmd_repository_path,
            old_file_location_base,
            new_file_location_base,
            "--ext-pattern", ext_pattern,
        ])
        u, n = main(parsed)
        assert len(u) == 1

        subprocess.run(["git", "restore", "tests/data/reference_nc.xml"])

        # Year as format code
        ext_pattern = "%Y/09/01/*.nc"
        parser = create_parser()
        parsed = parser.parse_args([
            mmd_repository_path,
            old_file_location_base,
            new_file_location_base,
            "--ext-pattern", ext_pattern,
        ])
        u, n = main(parsed)
        assert len(u) == 1

        subprocess.run(["git", "restore", "tests/data/reference_nc.xml"])

        # No match
        ext_pattern = "%Y/09/02/*.nc"
        parser = create_parser()
        parsed = parser.parse_args([
            mmd_repository_path,
            old_file_location_base,
            new_file_location_base,
            "--ext-pattern", ext_pattern,
        ])
        u, n = main(parsed)
        assert len(u) == 0
