"""
License:

This file is part of the py-mmd-tools repository
<https://github.com/metno/py-mmd-tools>.

py-mmd-tools is licensed under the Apache License 2.0
<https://github.com/metno/py-mmd-tools/blob/master/LICENSE>
"""
import os
import pytz
import uuid
import shutil
import netCDF4
import datetime
import requests
import tempfile
import warnings
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


def check_csw_catalog(ds_id, nc_file, urls, env, emsg=""):
    """Search for the dataset with id 'ds_id' in the CSW metadata
    catalog.
    """
    ds_found_and_accessible = False
    res = requests.get(url=f"https://{urls[env]['csw']}/csw",
                       params={
                           "service": "CSW",
                           "version": "2.0.2",
                           "request": "GetRepositoryItem",
                           "id": ds_id})
    # TODO: check the data_access urls
    if res.status_code == 200:
        ds_found_and_accessible = True
    else:
        emsg += f"Could not find dataset in CSW catalog: {nc_file} (id: {ds_id})"

    return ds_found_and_accessible, emsg


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
    """Copy original MMD file, and change the file_location field.
    Return the filename of the updated MMD file, and a status flag
    indicating if it has been changed or not.
    """
    if not os.path.isfile(mmd):
        raise ValueError(f"File does not exist: {mmd}")
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
                add_metadata_update_info(f, "Change storage information.")
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


def move_data_file(nc_file, nfl, emsg=""):
    """Move data file from nc_file to nfl.
    """
    nc_moved = False
    try:
        shutil.move(nc_file, nfl)
    except Exception as e:
        nc_moved = False
        emsg = f"Could not move file from {nc_file} to {nfl}.\nError message: {str(e)}\n"
    else:
        nc_moved = True
    return nc_moved, emsg


def move_data(mmd_repository_path, old_file_location_base, new_file_location_base,
              ext_pattern=None, dry_run=True, env="prod"):
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

    if os.path.isfile(old_file_location_base):
        existing = [old_file_location_base]
    else:
        existing = [str(nc_file) for match, nc_file in
                    datetime_glob.walk(pattern=os.path.join(old_file_location_base, ext_pattern))]

    copy_mmd = True
    if dry_run:
        # Not copying the MMD file will make it easy to check changes
        # with git diff
        copy_mmd = False

    updated = []
    not_updated = {}
    for nc_file in existing:
        # Error message
        emsg = ""
        nfl = new_file_location(nc_file, new_file_location_base, old_file_location_base, dry_run)
        mmd_orig = get_local_mmd_git_path(nc_file, mmd_repository_path)

        # Check permissions before doing anything
        remove_file_allowed = os.access(nc_file, os.W_OK)
        write_file_allowed = os.access(nfl, os.W_OK)
        if not remove_file_allowed or not write_file_allowed:
            if not remove_file_allowed and not write_file_allowed:
                raise PermissionError(f"Missing permissions to delete {nc_file} "
                                      f"and to write {nfl}")
            if not remove_file_allowed:
                raise PermissionError(f"Missing permission to delete {nc_file}")
            if not write_file_allowed:
                raise PermissionError(f"Missing permission to write {nfl}")

        mmd_new, mmd_updated = mmd_change_file_location(mmd_orig, nfl, copy=copy_mmd)
        if not mmd_updated:
            raise Exception(f"Could not update MMD file for {nc_file}")

        # Get MMD content as binary data
        with open(mmd_new, "rb") as fn:
            data = fn.read()
        res = requests.post(url=f"https://{urls[env]['dmci']}/v1/validate", data=data)

        # Update with dmci update
        dmci_updated = False
        if res.status_code == 200 and not dry_run:
            # be careful with this...
            res = requests.post(url=f"https://{urls[env]['dmci']}/v1/update", data=data)
        if res.status_code == 200:
            # This should be the case for a dry-run and a valid xml
            dmci_updated = True
        else:
            raise Exception(f"Could not push updated MMD file to the DMCI API: {mmd_new}")

        if dmci_updated and not dry_run:
            nc_moved, emsg = move_data_file(nc_file, nfl)
            if not nc_moved:
                raise Exception(f"Could not move {nc_file} to {nfl}.")
        elif dmci_updated and dry_run:
            nc_moved = True

        ds_id = f"no.met.{urls[env]['id_namespace']}:{os.path.basename(mmd_orig).split('.')[0]}"
        if not dry_run:
            ds_found_and_accessible, emsg = check_csw_catalog(ds_id, nc_file, urls, env, emsg=emsg)
        else:
            ds_found_and_accessible = True

        if not ds_found_and_accessible:
            warnings.warn(f"Could not find data in CSW catalog: {ds_id}")

        if all([mmd_updated, dmci_updated, nc_moved, ds_found_and_accessible]):
            updated.append(mmd_orig)
        else:
            not_updated[mmd_orig] = emsg

    return not_updated, updated


def new_file_location(nc_file, new_base_loc, existing_base_loc, dry_run):
    """Return the name of the new folder where the netcdf file will be
    stored. Subfolders of new_base_loc will be created.
    """
    if not os.path.isdir(new_base_loc):
        raise ValueError(f"Folder does not exist: {new_base_loc}")
    file_path = nc_file.replace(existing_base_loc, new_base_loc)
    new_folder = os.path.dirname(os.path.abspath(file_path))
    if not dry_run:
        try:
            os.makedirs(new_folder)
        except FileExistsError:
            # Do nothing
            pass
    return new_folder
