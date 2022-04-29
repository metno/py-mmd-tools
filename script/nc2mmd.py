#!/usr/bin/env python3
"""
Script to create an MMD xml file from a netcdf file.

License:

This file is part of the py-mmd-tools repository
<https://github.com/metno/py-mmd-tools>.

py-mmd-tools is licensed under the Apache License 2.0
<https://github.com/metno/py-mmd-tools/blob/master/LICENSE>

Usage:
    nc_to_mmd.py [-h] -i INPUT -o OUTPUT_DIR

Example:
    python nc_to_mmd.py -i ../tests/data/reference_nc.nc -o .
"""

import argparse
import pathlib

from py_mmd_tools import nc_to_mmd


def create_parser():
    """Create parser object"""
    parser = argparse.ArgumentParser(
        description='Create an MMD xml file from an input netCDF file.'
    )

    # Add to parse a whole server?
    parser.add_argument(
        '-i', '--input', type=str,
        help='Input file, folder or OPeNDAP url.'
    )
    parser.add_argument(
        '-o', '--output_dir', type=pathlib.Path,
        help='Output directory.'
    )
    parser.add_argument(
        '-w', '--add_wms_data_access', action='store_true',
        help='Optional add wms in data_access.'
    )
    parser.add_argument(
        '-c', '--checksum_calculation',  action='store_true',
        help="Toggle wether to calculate the checksum of the file"
    )

    return parser


def main(args):
    """Run tool to create MMD xml file from input netCDF-CF file(s)"""

    if pathlib.Path(args.input).is_dir():
        # Directory containing nc files
        inputfiles = pathlib.Path(args.input).glob('*.nc')
    elif 'dodsC' in args.input:
        # A remote OPeNDAP url
        inputfiles = [args.input]
    elif pathlib.Path(args.input).is_file():
        # Single nc file
        inputfiles = [args.input]

    else:
        raise ValueError(f'Invalid input: {args.input}')

    for file in inputfiles:
        outfile = (args.output_dir / pathlib.Path(file).stem).with_suffix('.xml')
        md = nc_to_mmd.Nc_to_mmd(str(file), output_file=outfile)
        md.to_mmd(
            add_wms_data_access=args.add_wms_data_access,
            checksum_calculation=args.checksum_calculation
        )


if __name__ == '__main__':  # pragma: no cover
    parser = create_parser()
    main(parser.parse_args())
