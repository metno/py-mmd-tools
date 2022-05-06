#!/usr/bin/env python3
"""
Script to create documentation about netcdf attributes to be used in the
Data Management Handbook
(DMH; see https://github.com/metno/data-management-handbook).

License:

This file is part of the py-mmd-tools repository
<https://github.com/metno/py-mmd-tools>.

py-mmd-tools is licensed under the Apache License 2.0
<https://github.com/metno/py-mmd-tools/blob/master/LICENSE>

Usage:
    yaml2adoc.py [-h] -o OUTPUT_FILE

Example:
    python yaml2adoc.py -o ncattrs.adoc
"""

import sys
import argparse

from py_mmd_tools import yaml_to_adoc


def create_parser():
    """Create parser object"""
    parser = argparse.ArgumentParser(
        description=(
            'Create an asciidoc file based on '
            'https://github.com/metno/py-mmd-tools/tree/master/py_mmd_tools/mmd_elements.yaml.'
        )
    )
    parser.add_argument('-o', '--output_file', help='Output file.')

    return parser


def main(args):
    """ToDo: Add docstring"""
    if not args.output_file:
        sys.exit()

    adoc = yaml_to_adoc.nc_attrs_from_yaml()
    with open(args.output_file, 'w') as fh:
        fh.write(adoc)


if __name__ == '__main__':  # pragma: no cover
    parser = create_parser()
    main(parser.parse_args())
