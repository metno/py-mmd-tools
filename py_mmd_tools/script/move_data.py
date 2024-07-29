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
import argparse

from py_mmd_tools.mmd_operations import move_data


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
        help="Base or exact path to the folder to which the new file will be moved.")
    parser.add_argument(
        "existing_pathname_pattern", type=str,
        help="Pathname pattern to existing file location(s). Allows "
             "parsing date/times from a path given a glob pattern "
             "intertwined with date/time format akin to "
             "strptime/strftime format.")
    parser.add_argument(
        '--dmci-update', action='store_true',
        help='Directly update the online catalog with the changed MMD files.'
    )

    return parser


def main(args=None):
    """Move dataset(s) and update MMD.
    """
    if not os.path.isdir(args.mmd_repository_path):
        raise ValueError(f"Invalid input: {args.mmd_repository_path}")

    if not os.path.isdir(args.new_file_location_base):
        raise ValueError(f"Invalid input: {args.new_file_location_base}")

    not_updated, updated =  move_data(args.mmd_repository_path,
                                      args.new_file_location_base,
                                      args.existing_pathname_pattern,
                                      dry_run=not args.dmci_update)
    print(f"Updated: {len(updated)}")
    print(f"Not updated: {len(not_updated)}")


def _main():  # pragma: no cover
    main(create_parser().parse_args())  # entry point in setup.cfg


if __name__ == '__main__':  # pragma: no cover
    main(create_parser().parse_args())
