#!/usr/bin/env python3
"""
Script to move one or more datasets from one location to another, and
update its MMD xml file accordingly.

License:

This file is part of the py-mmd-tools repository
<https://github.com/metno/py-mmd-tools>.

py-mmd-tools is licensed under the Apache License 2.0
<https://github.com/metno/py-mmd-tools/blob/master/LICENSE>
"""
import os
import logging
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
        "old_file_location_base", type=str,
        help="Base folder from which the data file(s) will be moved, or exact path to a file.")
    parser.add_argument(
        "new_file_location_base", type=str,
        help="Base or exact path to the folder to which the data file(s) will be moved.")
    parser.add_argument(
        "--ext-pattern", type=str, default=None,
        help="Pathname pattern extending old_file_location_base, i.e., extending the "
             "existing file *base* location(s) with, e.g, the year and month as a "
             "glob pattern intertwined with date/time format akin to "
             "strptime/strftime format (e.g., '%Y/%m').")
    parser.add_argument(
        "--dmci-update", action="store_true",
        help="Directly update the online catalog with the changed MMD files."
    )
    parser.add_argument(
        "--log-file", type=str, default="move_data.log",
        help="Log filename")

    return parser


def main(args=None):
    """Move dataset(s) and update MMD.
    """
    if not os.path.isdir(args.mmd_repository_path):
        raise ValueError(f"Invalid input: {args.mmd_repository_path}")

    if not os.path.isdir(args.new_file_location_base):
        raise ValueError(f"Invalid input: {args.new_file_location_base}")

    logging.basicConfig(filename=args.log_file, level=logging.INFO)

    not_updated, updated = move_data(args.mmd_repository_path,
                                     args.old_file_location_base,
                                     args.new_file_location_base,
                                     args.ext_pattern,
                                     dry_run=not args.dmci_update)

    return updated, not_updated


def _main():  # pragma: no cover
    main(create_parser().parse_args())  # entry point in setup.cfg


if __name__ == '__main__':  # pragma: no cover
    main(create_parser().parse_args())
