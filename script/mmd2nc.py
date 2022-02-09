#!/usr/bin/env python3
"""
Script to update an netcdf file from an MMD xml file.

License:

This file is part of the py-mmd-tools repository
<https://github.com/metno/py-mmd-tools>.

py-mmd-tools is licensed under the Apache License 2.0
<https://github.com/metno/py-mmd-tools/blob/master/LICENSE>

Usage:
    mmd_to_nc.py [-h] -i INPUT -o OUTPUT_DIR

Example:
    python mmd_to_nc.py -i ../tests/data/reference_mmd.xml -o ../tests/data/reference_nc.nc
"""

import argparse
import pathlib
from py_mmd_tools import mmd_to_nc


def create_parser():
    """Create parser object"""
    parser = argparse.ArgumentParser(
        description='Update an input netCDF file from an MMD xml file.'
    )

    parser.add_argument(
        '-m', '--mmd', type=str,
        help='MMD xml file.'
    )
    parser.add_argument(
        '-n', '--nc', type=pathlib.Path,
        help='Netcdf file to update.'
    )
    parser.add_argument(
        '-x', '--xsd', type=pathlib.Path,
        help='XSD file.'
    )

    return parser


def main(args):
    """Run tool to update a netCDF-CF file from input MMD xml file"""

    if pathlib.Path(args.mmd).is_file():
        mmdfile = args.mmd
    else:
        raise ValueError(f'Invalid MMD file input: {args.mmd}')

    if pathlib.Path(args.nc).is_file():
        ncfile = args.nc
    else:
        raise ValueError(f'Invalid NetCDF file input: {args.nc}')

    if pathlib.Path(args.xsd).is_file():
        xsdfile = args.xsd
    else:
        raise ValueError(f'Invalid XSD file input: {args.xsd}')

    md = mmd_to_nc.Mmd_to_nc(mmdfile, ncfile, xsdfile)
    md.update_nc()


if __name__ == '__main__':  # pragma: no cover
    parser = create_parser()
    main(parser.parse_args())
