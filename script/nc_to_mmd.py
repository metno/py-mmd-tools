#!/usr/bin/env python3

"""
Script to create an MMD xml file from a netcdf file.

License:
     This file is part of the py-mmd-tools repository (https://github.com/metno/py-mmd-tools).
     py-mmd-tools is licensed under Apache License 2.0 (https://github.com/metno/py-mmd-tools/blob/master/LICENSE)

Usage: nc_to_mmd.py [-h] -i INPUT -o OUTPUT_DIR [-p netcdf_local_path]
Example:
    $ python nc_to_mmd.py -i ../tests/data/reference_nc.nc -o .
"""

import os
import argparse
import pathlib
from py_mmd_tools import nc_to_mmd


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Create an MMD xml file from an input netCDF file.")

    # Add to parse a whole server?
    parser.add_argument('-i', '--input', type=str, help="Input file, folder or OPeNDAP url.")
    parser.add_argument('-o', '--output_dir', type=pathlib.Path, help="Output directory.")
    parser.add_argument('-p', '--netcdf_local_path',
                        type=str,
                        default='',
                        help="Optional local netcdf path. \
                              This can be given together with a remote input location if the files also are \
                              available locally. This will avoid download of the data for md5sum calculation.")
    parser.add_argument('-w', '--add_wms_data_access',
                        action='store_true',
                        help="Optional add wms in data_access.")
    args = parser.parse_args()

    # args.input as str, because if pathlib.Path, it is not compatible with URLs

    netcdf_local_path = args.netcdf_local_path
    if netcdf_local_path and not os.path.isfile(netcdf_local_path):
        print(f'Given netcdf local path {netcdf_local_path} is not a valid file. Can not use this.')
        print('Will download later based on the given input.')
        netcdf_local_path = ''

    # Directory containing nc files
    if pathlib.Path(args.input).is_dir():
        inputfiles = pathlib.Path(args.input).glob('*.nc')
    # Single nc file
    elif pathlib.Path(args.input).is_file():
        inputfiles = [args.input]
    # A remote OPeNDAP url
    elif 'dodsC' in args.input:  # args.input.startswith('https://thredds.met.no/thredds/dodsC/'):
        inputfiles = [args.input]
    else:
        print(f'Invalid input: {args.input}')
        exit(1)

    for file in inputfiles:
        outfile = (args.output_dir / pathlib.Path(file).stem).with_suffix('.xml')
        md = nc_to_mmd.Nc_to_mmd(str(file), output_file=outfile)
        md.to_mmd(netcdf_local_path=netcdf_local_path, add_wms_data_access=args.add_wms_data_access)
