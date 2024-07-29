"""
License:

This file is part of the py-mmd-tools repository
<https://github.com/metno/py-mmd-tools>.

py-mmd-tools is licensed under the Apache License 2.0
<https://github.com/metno/py-mmd-tools/blob/master/LICENSE>
"""
import os
import pytest
import shutil

from py_mmd_tools.mmd_operations import move_data
from py_mmd_tools.mmd_operations import mmd_readlines
from py_mmd_tools.mmd_operations import new_file_location
from py_mmd_tools.mmd_operations import mmd_change_file_location
from py_mmd_tools.mmd_operations import get_local_mmd_git_path


@pytest.mark.script
def test_get_local_mmd_git_path(dataDir):
    """Test that the mmd git path is returned correctly with folders
    composed from its uuid.
    """
    ncfile = os.path.join(dataDir, "reference_nc.nc")
    fn = get_local_mmd_git_path(ncfile, "/some/folder/mmd-xml-production")
    assert fn == "/some/folder/mmd-xml-production/arch_4/arch_3/arch_9/" \
                 "b7cb7934-77ca-4439-812e-f560df3fe7eb.xml"


@pytest.mark.script
def test_mmd_change_file_location(dataDir):
    """Test that an MMD file is created with new file_location, and
    new metadata update.
    """
    mmd = os.path.join(dataDir, "reference_nc_TMP.xml")
    shutil.copy(os.path.join(dataDir, "reference_nc.xml"), mmd)
    new_file_location = "/some/where/else/2024/06/19"

    new_mmd, changed = mmd_change_file_location(mmd, new_file_location)
    assert changed is True
    assert os.path.isfile(new_mmd)
    lines = mmd_readlines(new_mmd)
    for line in lines:
        if "<mmd:file_location>" in line:
            assert "/some/where/else/2024/06/19" in line

    mmd, changed = mmd_change_file_location(mmd, new_file_location, copy=False)
    assert changed is True
    assert os.path.isfile(mmd)
    lines = mmd_readlines(mmd)
    for line in lines:
        if "file_location" in line:
            assert "/some/where/else/2024/06/19" in line

    # Delete tmp files
    os.remove(mmd)
    os.remove(new_mmd)


@pytest.mark.script
def test_mmd_readlines(dataDir):
    """Test that the lines in the MMD file are returned as a list.
    """
    mmd = os.path.join(dataDir, "reference_nc.xml")
    lines = mmd_readlines(mmd)
    assert isinstance(lines, list)
    assert "mmd:mmd" in lines[0]

    mmd = os.path.join(dataDir, "does_not_exist.xml")
    with pytest.raises(ValueError):
        lines = mmd_readlines(mmd)


@pytest.mark.script
def test_move_data(dataDir, monkeypatch):
    """Test the move_data function.
    """
    mmd_repository_path = "/some/folder/mmd-xml-production"
    new_file_location_base = "/some/where/new"
    nc_file = os.path.join(dataDir, "reference_nc.nc")

    class MockResponse:

        status_code = 200

    with pytest.raises(ValueError):
        move_data(mmd_repository_path, new_file_location_base, nc_file, env="hei")

    with pytest.raises(ValueError):
        move_data("/some/folder/mmd-xml-noenv", new_file_location_base, nc_file)

    with monkeypatch.context() as mp:
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
        not_updated, updated = move_data(mmd_repository_path, new_file_location_base, nc_file)
        assert len(not_updated) == 0
        assert len(updated) == 1
        assert os.path.isfile(updated[0])
        lines = mmd_readlines(updated[0])
        for line in lines:
            if "<mmd:file_location>" in line:
                assert "/some/where/new" in line
        # Remove new MMD file
        os.remove(updated[0])

        def mock_walk(*a, **k):
            yield (1, nc_file)

        mp.setattr("py_mmd_tools.mmd_operations.datetime_glob.walk",
                   lambda *a, **k: mock_walk(*a, **k))
        # This pattern is not really used but it should look something
        # like this when used correctly:
        pattern = os.path.join(dataDir, "%Y/%m/%d/*.nc")
        not_updated, updated = move_data(mmd_repository_path, new_file_location_base, pattern,
                                         dry_run=False)
        assert len(not_updated) == 0
        assert len(updated) == 1
        assert os.path.isfile(updated[0])
        lines = mmd_readlines(updated[0])
        for line in lines:
            if "<mmd:file_location>" in line:
                assert "/some/where/new" in line
        # Remove new MMD file
        os.remove(updated[0])

        mp.setattr("py_mmd_tools.mmd_operations.mmd_change_file_location",
                   lambda *a, **k: (nc_file, False))
        not_updated, updated = move_data(mmd_repository_path, new_file_location_base, pattern)
        assert len(not_updated) == 1


@pytest.mark.script
def test_new_file_location(monkeypatch):
    """Test that the returned new location paths are correct.
    """
    file = "/some/old/loc/2024/06/19/" \
           "S1A_IW_GRDM_1SDV_20240619T053156_20240619T053223_054388_069E03_FC95_MEPS.nc"
    new_base = "/some/where/else"
    existing_pathname_pattern = "/some/old/loc/%Y/%m/%d/*.nc"

    with pytest.raises(ValueError):
        new_file_location(file, new_base, existing_pathname_pattern)

    with monkeypatch.context() as mp:
        mp.setattr("py_mmd_tools.mmd_operations.os.path.isfile", lambda *a, **k: True)
        assert new_file_location(file, new_base, existing_pathname_pattern) == \
            "/some/where/else/2024/06/19"
        new_base = "/some/where/else/2024/06/19"
        assert new_file_location(file, new_base) == "/some/where/else/2024/06/19"
