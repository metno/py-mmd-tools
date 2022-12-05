#!/usr/bin/env python3
"""
Script to check whether a netcdf file contains all the required elements
to create a valid MMD file.

License:

This file is part of the py-mmd-tools repository
<https://github.com/metno/py-mmd-tools>.

py-mmd-tools is licensed under the Apache License 2.0
<https://github.com/metno/py-mmd-tools/blob/master/LICENSE>

Usage:
    check_nc [-h] -i INPUT

Examples:
    python check_nc.py -i ../tests/data/reference_nc.nc
    python check_nc.py -i ../tests/data/reference_nc_fail.nc
    python check_nc.py -i <url to nc file>
"""

import argparse
import pathlib

from py_mmd_tools import nc_to_mmd


def create_parser():
    """Create argument parser"""
    parser = argparse.ArgumentParser(
        description="Check if a netCDF file contains required elements to create an MMD file."
    )
    parser.add_argument('-i', '--input', type=str, help="Input file, folder or OPeNDAP url.")

    return parser


def main(args=None):
    """Main method for checking netcdf file"""

    # args.input as str, because if pathlib.Path, it is not compatible with URLs
    if pathlib.Path(args.input).is_dir():
        # Directory containing nc files
        inputfiles = pathlib.Path(args.input).glob('*.nc')
    elif 'dodsC' in args.input:
        # URL to a remote dataset available through OPeNDAP
        inputfiles = [args.input]
    elif pathlib.Path(args.input).is_file():
        # Single nc file
        inputfiles = [args.input]
    else:
        raise ValueError(f'Invalid input: {args.input}')

    for file in inputfiles:
        md = nc_to_mmd.Nc_to_mmd(str(file), check_only=True)
        try:
            ok, msg = md.to_mmd()
        except AttributeError as e:
            ok = False
            msg = e
        if ok:
            print(f"OK - file {file} contains all necessary elements.")
        else:
            print(f"Not OK - file {file} does not contain all necessary elements.")
            print(msg)


def _main():  # pragma: no cover
    main(create_parser().parse_args())  # entry point in setup.cfg


if __name__ == '__main__':  # pragma: no cover
    main(create_parser().parse_args())
