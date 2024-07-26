"""
License:

This file is part of the py-mmd-tools repository
<https://github.com/metno/py-mmd-tools>.

py-mmd-tools is licensed under the Apache License 2.0
<https://github.com/metno/py-mmd-tools/blob/master/LICENSE>
"""
import os
import re
import pytz
import uuid
import shutil
import netCDF4
import datetime
import tempfile
import datetime_glob


def add_metadata_update_info(f, note, type="Minor modification"):
    """ Add update information """
    f.write("    <mmd:update>\n"
            "      <mmd:datetime>%s</mmd:datetime>\n"
            "      <mmd:type>%s</mmd:type>\n"
            "      <mmd:note>%s</mmd:note>\n"
            "    </mmd:update>\n" % (datetime.datetime.utcnow().replace(
        tzinfo=pytz.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), type, note))


def get_local_mmd_git_path(nc_file, mmd_repository_path):
    """Return the path to the original MMD file.
    """
    ds = netCDF4.Dataset(nc_file)
    lvlA = "arch_%s" % uuid.UUID(ds.id).hex[7]
    lvlB = "arch_%s" % uuid.UUID(ds.id).hex[6]
    lvlC = "arch_%s" % uuid.UUID(ds.id).hex[5]
    mmd_filename = ds.id + ".xml"
    ds.close()
    return os.path.join(mmd_repository_path, lvlA, lvlB, lvlC, mmd_filename)


def mmd_change_file_location(mmd, new_file_location, copy=True):
    """Copy original MMD file, and make changes. Return the filename
    of the updated file, and a status flag indicating if it has been
    changed or not.
    """
    if copy:
        tmp_path = tempfile.gettempdir()
        shutil.copy2(mmd, tmp_path)
        # Edit copied MMD file
        mmd = os.path.join(tmp_path, os.path.basename(mmd))
    lines = mmd_readlines(mmd)
    # Open the MMD file and add updates
    status = False
    with open(mmd, "w") as f:
        for line in lines:
            if "</mmd:last_metadata_update>" in line:
                add_metadata_update_info(f, "New file location in storage information.")
            if "<mmd:file_location>" in line:
                f.write(f"    <mmd:file_location>{new_file_location}</mmd:file_location>\n")
                status = True
            else:
                f.write(line)
    return mmd, status


def mmd_readlines(filename):
    """ Read lines in MMD file.
    """
    if not os.path.exists(filename):
        raise ValueError("File does not exist: %s" % filename)
    with open(filename, "r") as f:
        lines = f.readlines()
    return lines


def move_data(mmd_repository_path, new_file_location_base, existing_pathname_pattern_or_exact):
    """Update MMD and move data file.
    """
    if os.path.isfile(existing_pathname_pattern_or_exact):
        existing = [existing_pathname_pattern_or_exact]
        existing_pathname_pattern = None
    else:
        existing = [file for match, file in
                    datetime_glob.walk(pattern=existing_pathname_pattern_or_exact)]
        existing_pathname_pattern = existing_pathname_pattern_or_exact

    updated = []
    for file in existing:
        nfl = new_file_location(file, new_file_location_base, existing_pathname_pattern)
        mmd_orig = get_local_mmd_git_path(file, mmd_repository_path)
        mmd_new, mmd_updated = mmd_change_file_location(mmd_orig, nfl)
        if not mmd_updated:
            raise Exception("MMD was not updated..")

        # Update with dmci update
        dmci_updated = True

        # If update was ok - move netcdf file
        # mv file nfl
        nc_moved = True

        # Check by searching CSW and checking data access urls
        ds_found_and_accessible = True

        updated.append(all([mmd_updated, dmci_updated, nc_moved, ds_found_and_accessible]))

    return all(updated), mmd_new


def new_file_location(file, new_base_loc, existing_pathname_pattern=None):
    """Return the new file location. If existing_pathname_pattern is
    None, the returned path will equal the provided parameter
    new_base_loc. This is to allow usage flexibility of the move_data
    function.
    """
    if existing_pathname_pattern == None:
        file_path = os.path.join(new_base_loc, os.path.basename(file))
    else:
        file_path = os.path.join(new_base_loc, file.removeprefix(re.split(r"[^\w/-]",
                                                                 existing_pathname_pattern)[0]))
    if not os.path.isfile(file_path):
        raise ValueError(f"File does not exist: {file_path}")
    return os.path.dirname(os.path.abspath(file_path))
