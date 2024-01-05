#!/usr/bin/env python3

"""
Tool for extracting netCDF header to a json. For use in py-mmd-tools-api



"""
import os
import json
import argparse
import pathlib

import numpy as np


from netCDF4 import Dataset


def create_parser():
    """Create parser object"""

    parser = argparse.ArgumentParser(description="Extract nc header to json format")

    parser.add_argument(
        '-i', '--input', type=str,
        help='Input file or folder', required=True
    )

    parser.add_argument(
        "-e", "--file-ending", default="nc", type=str,
        help="File ending of nc files"
    )

    return parser


def get_header_netCDF(data) -> dict:
    full_attr = {"global_variables": {i: data.getncattr(
        i) for i in data.ncattrs()}, "variables":  {}}

    for var_name, variable in data.variables.items():
        full_attr["variables"][var_name] = {'attrs': {i: handle_numpy_types(variable.getncattr(i))
                                                      for i in variable.ncattrs()},
                                            'dtype': str(variable.dtype),
                                            'shape': variable.shape
                                            }

    return json.dumps(full_attr)


def handle_numpy_types(inpt):
    if isinstance(inpt, np.float32):
        return np.float64(inpt)

    if isinstance(inpt, np.int64):
        return inpt.item()

    if isinstance(inpt, np.ndarray):
        return inpt.tolist()

    return inpt


def main(args=None):
    """Main function for this script"""
    if pathlib.Path(args.input).is_dir():
        inputfiles = pathlib.Path(args.input).glob('*.nc')
    elif pathlib.Path(args.input).is_file():
        inputfiles = [args.input]
    else:
        raise ValueError(f'Invalid input: {args.input}')

    json_header = [get_header_netCDF(Dataset(file)) for file in inputfiles]

    [print(i) for i in json_header]

    return


def _main():  # pragma: no cover
    try:
        main(create_parser().parse_args())  # entry point
    except ValueError as e:
        print(e)
    except AttributeError as e:
        print(e)


if __name__ == "__main__":
    try:
        main(create_parser().parse_args())
    except ValueError as e:
        print(e)
    except AttributeError as e:
        print(e)
