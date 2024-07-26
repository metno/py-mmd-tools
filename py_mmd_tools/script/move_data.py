#!/usr/bin/env python3
"""
Script to move one or more datasets from one location to another, and
update its MMD xml file accordingly.

License:

This file is part of the py-mmd-tools repository
<https://github.com/metno/py-mmd-tools>.

py-mmd-tools is licensed under the Apache License 2.0
<https://github.com/metno/py-mmd-tools/blob/master/LICENSE>

Usage:
    move_data [-h] -i INPUT -n OUTPUT_DIR
"""
import os
import re
import glob
import uuid
import netCDF4
import pathlib
import argparse
import tempfile
import datetime_glob

from py_mmd_tools.mmd_operations import move_data
from py_mmd_tools.mmd_operations import mmd_readlines
from py_mmd_tools.mmd_operations import new_file_location
from py_mmd_tools.mmd_operations import get_local_mmd_git_path
from py_mmd_tools.mmd_operations import add_metadata_update_info
from py_mmd_tools.mmd_operations import mmd_change_file_location


def create_parser():
    """Create parser object"""
    parser = argparse.ArgumentParser(description="Move one or more datasets from one location to "
                                                 "another, and update its MMD xml file "
                                                 "accordingly.")
    parser.add_argument(
        "mmd_repository_path", type=str,
        help="Local folder containing all MMD files.")
    parser.add_argument(
        "new_file_location_base", type=str,
        help="Base or exact path to the new file location.")
    parser.add_argument(
        "existing_pathname_pattern", type=str,
        help="Pathname pattern to existing file location(s). Allows "
             "parsing date/times from a path given a glob pattern "
             "intertwined with date/time format akin to "
             "strptime/strftime format.")
    return parser


def main(args=None):
    """Move dataset(s) and update MMD.
    """
    if not os.path.isdir(args.mmd_repository_path):
        raise ValueError(f"Invalid input: {args.mmd_repository_path}")

    if not os.path.isdir(args.new_file_location_base):
        raise ValueError(f"Invalid input: {args.new_file_location_base}")

    return move_data(args.mmd_repository_path,
                     args.new_file_location_base,
                     args.existing_pathname_pattern)


def _main():  # pragma: no cover
    main(create_parser().parse_args())  # entry point in setup.cfg


if __name__ == '__main__':  # pragma: no cover
    main(create_parser().parse_args())
