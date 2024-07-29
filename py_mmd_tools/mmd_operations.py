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
import requests
import tempfile
import datetime_glob


def add_metadata_update_info(f, note, type="Minor modification"):
    """ Add update information """
    f.write(
        "    <mmd:update>\n"
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


def move_data(mmd_repository_path, new_file_location_base, existing_pathname_pattern_or_exact,
              dry_run=True, env="prod"):
    """Update MMD and move data file.
    """
    if env not in ["dev", "staging", "prod"]:
        raise ValueError("Invalid env input")
    if env not in mmd_repository_path:
        raise ValueError("Invalid mmd_repository path")

    urls = {
        "prod": {
            "dmci": "dmci.s-enda.k8s.met.no",
            "csw": "data.csw.met.no",
            "id_namespace": "no.met",
        },
        "staging": {
            "dmci": "dmci.s-enda-staging.k8s.met.no",
            "csw": "https://csw.s-enda-staging.k8s.met.no/",
            "id_namespace": "no.met.staging",
        },
        "dev": {
            "dmci": "dmci.s-enda-dev.k8s.met.no",
            "csw": "https://csw.s-enda-dev.k8s.met.no/",
            "id_namespace": "no.met.dev",
        }
    }

    if os.path.isfile(existing_pathname_pattern_or_exact):
        existing = [existing_pathname_pattern_or_exact]
        existing_pathname_pattern = None
    else:
        existing = [file for match, file in
                    datetime_glob.walk(pattern=existing_pathname_pattern_or_exact)]
        existing_pathname_pattern = existing_pathname_pattern_or_exact

    copy_mmd = False
    if dry_run:
        # Not copying the file will make it easy to check changes
        # with git diff
        existing_pathname_pattern = None
        copy_mmd = True

    updated = []
    not_updated = []
    for file in existing:
        nfl = new_file_location(file, new_file_location_base, existing_pathname_pattern)
        mmd_orig = get_local_mmd_git_path(file, mmd_repository_path)
        mmd_new, mmd_updated = mmd_change_file_location(mmd_orig, nfl, copy=copy_mmd)

        # Get MMD content as binary data
        with open(mmd_new, "rb") as fn:
            data = fn.read()

        res = requests.post(url=f"https://{urls[env]['dmci']}/v1/validate", data=data)

        # Update with dmci update
        dmci_updated = False
        if not dry_run:
            # be careful with this...
            res = requests.post(url=f"https://{urls[env]['dmci']}/v1/update", data=data)
        if res.status_code == 200:
            # This intentionally becomes True in case of dry-run and
            # a valid xml
            dmci_updated = True

        # If update was ok - move netcdf file
        nc_moved = False
        if dmci_updated and not dry_run:
            shutil.move(file, nfl)
            nc_moved = True
        elif dmci_updated and dry_run:
            nc_moved = True

        # Check by searching CSW and checking data access urls
        ds_found_and_accessible = False
        if not dry_run:
            res = requests.get(url=f"https://{urls[env]['csw']}/csw",
                               params={
                                   "service": "CSW",
                                   "version": "2.0.2",
                                   "request": "GetRepositoryItem",
                                   "id": f"no.met.{urls[env]['id_namespace']}"
                                         f"{os.path.basename(file).split('.')[0]}"})
            if res.status_code == 200:
                ds_found_and_accessible = True
        else:
            ds_found_and_accessible = True

        if all([mmd_updated, dmci_updated, nc_moved, ds_found_and_accessible]):
            updated.append(mmd_new)
        else:
            not_updated.append(mmd_new)

    return not_updated, updated


def new_file_location(file, new_base_loc, existing_pathname_pattern=None):
    """Return the name of the new folder where the netcdf file will be
    stored. If existing_pathname_pattern is None, the returned path
    will equal the provided parameter new_base_loc. This is to allow
    usage flexibility of the move_data function.
    """
    if existing_pathname_pattern is None:
        file_path = os.path.join(new_base_loc, os.path.basename(file))
    else:
        file_path = os.path.join(new_base_loc, file.removeprefix(re.split(r"[^\w/-]",
                                                                 existing_pathname_pattern)[0]))
    new_folder = os.path.dirname(os.path.abspath(file_path))
    if not os.path.isdir(new_folder):
        raise ValueError(f"Folder does not exist: {file_path}")
    return new_folder
