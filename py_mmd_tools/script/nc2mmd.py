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
import netCDF4
import os
import pathlib
import yaml
import warnings

from pkg_resources import resource_string

from py_mmd_tools import nc_to_mmd


def create_parser():
    """Create parser object"""
    parser = argparse.ArgumentParser(
        description='Create an MMD xml file from an input netCDF file.'
    )

    # Add to parse a whole server?
    parser.add_argument(
        '-i', '--input', type=str,
        help='Input file or folder.'
    )
    parser.add_argument(
        '--dry-run', action='store_true',
        help='Dry-run to check the netcdf metadata content.'
    )
    parser.add_argument(
        '-u', '--url', type=str,
        help='OPeNDAP url. If multiple files shall be processed, '
             'this should be their base url.'
    )
    parser.add_argument(
        '-o', '--output_dir', type=pathlib.Path,
        help='Output directory.'
    )
    parser.add_argument(
        '-w', '--add_wms_data_access', action='store_true',
        help='Add wms data access (optional).'
    )
    parser.add_argument(
        '-l', '--wms_link', default=None,
        help=('Specify a custom WMS link. '
              'Default will generate a link to ncwms based on the input data. '
              'Should be use together with wms_layer_names. '
              'Please note \'?service=WMS&version=1.3.0&request=GetCapabilities\' '
              'will be added to the link automatically.')
    )
    parser.add_argument(
        '-n', '--wms_layer_names', default=[], nargs='*',
        help=('Specify a custom WMS layer names. Default will use the netcdf variable names as '
              'layer names. Only applied if wms_link also is given')
    )
    parser.add_argument(
        '-c', '--checksum_calculation',  action='store_true',
        help="Toggle whether to calculate the checksum of the file"
    )
    parser.add_argument(
        '--collection', default=None,
        help="Specify MMD collection field (default is METNCS)"
    )
    parser.add_argument(
        '--parent', default=None,
        help="Metadata ID of a parent dataset"
    )
    parser.add_argument(
        '--log-ids', default=None,
        help='Store the metadata IDs in a file'
    )
    parser.add_argument(
        '--print_warnings',  action='store_true',
        help="Toggle whether to print warnings"
    )

    return parser


def main(args=None):
    """Run tool to create MMD xml file from input netCDF-CF file(s)"""
    if not args.dry_run:
        if args.url is None:
            raise ValueError('OPeNDAP url must be provided')
        if args.output_dir is None:
            raise ValueError('MMD XML output directory must be provided')

    if not args.print_warnings:
        warnings.filterwarnings("ignore")

    assume_same_url_basename = False
    if pathlib.Path(args.input).is_dir():
        # Directory containing nc files
        inputfiles = pathlib.Path(args.input).glob('*.nc')
        # If the input is a directory, we need to assume that the
        # file and url basenames are the same
        assume_same_url_basename = True
    elif pathlib.Path(args.input).is_file():
        # Single nc file
        inputfiles = [args.input]
    else:
        raise ValueError(f'Invalid input: {args.input}')

    url = None  # dry-run option
    ids = []
    for file in inputfiles:
        if not args.dry_run:
            if assume_same_url_basename:
                url = os.path.join(args.url, file)
            else:
                url = args.url
            outfile = (args.output_dir / pathlib.Path(file).stem).with_suffix('.xml')
            md = nc_to_mmd.Nc_to_mmd(str(file), opendap_url=url, output_file=outfile)
        else:
            md = nc_to_mmd.Nc_to_mmd(str(file), check_only=True)
        mmd_yaml = yaml.load(
            resource_string(md.__module__.split('.')[0], 'mmd_elements.yaml'),
            Loader=yaml.FullLoader
        )
        metadata_id = md.get_metadata_identifier(mmd_yaml['metadata_identifier'],
                                                 netCDF4.Dataset(file))
        if metadata_id in ids:
            raise ValueError("Unique ID repetition. Please check your ID's.")
        else:
            ids.append(metadata_id)
        req_ok, msg = md.to_mmd(
            add_wms_data_access=args.add_wms_data_access,
            wms_link=args.wms_link,
            wms_layer_names=args.wms_layer_names,
            checksum_calculation=args.checksum_calculation,
            collection=args.collection,
            parent=args.parent
        )
    if args.log_ids:
        with open(args.log_ids, 'a') as f:
            for mid in ids:
                f.write(mid+'\n')


def _main():  # pragma: no cover
    # Why should this catch errors and print them afterwards? Seems strange...
    try:
        main(create_parser().parse_args())  # entry point in setup.cfg
    except ValueError as e:
        print(e)
    except AttributeError as e:
        print(e)


if __name__ == '__main__':  # pragma: no cover
    try:
        main(create_parser().parse_args())
    except ValueError as e:
        print(e)
    except AttributeError as e:
        print(e)
