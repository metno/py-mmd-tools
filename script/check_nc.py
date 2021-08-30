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

import sys
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

def main(args):
    """Main method for checking netcdf file"""

    # args.input as str, because if pathlib.Path, it is not compatible with URLs
    # Directory containing nc files
    if pathlib.Path(args.input).is_dir():
        inputfiles = pathlib.Path(args.input).glob('*.nc')

    # Single nc file
    elif pathlib.Path(args.input).is_file():
        inputfiles = [args.input]

    # URL to a remote dataset available through OPeNDAP
    elif args.input.startswith('https://thredds.met.no/thredds/dodsC/'):
        inputfiles = [args.input]
    else:
        print(f'Invalid input: {args.input}')
        sys.exit(1)

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


if __name__ == '__main__': # pragma: no cover
    parser = create_parser()
    main(parser.parse_args())
