#!/usr/bin/env python3

"""
Tool for extracting netCDF header to a json. For use with the py-mmd-tools API.


Usage:

ncheader2json -i <path-to-nc-file> |
curl -X POST -H 'Content-Type: application/json'  -d @- "<url-to-api>"


The API can currently be found at https://py-mmd-tools.s-enda-dev.k8s.met.no/nc2mmd

License:

This file is part of the py-mmd-tools repository
<https://github.com/metno/py-mmd-tools>.

py-mmd-tools is licensed under the Apache License 2.0
<https://github.com/metno/py-mmd-tools/blob/master/LICENSE>
"""
import json
import argparse
import pathlib

import numpy as np


from netCDF4 import Dataset


def create_parser():
    """Create parser object"""

    parser = argparse.ArgumentParser(
        description="Extract nc header to json format. Usage in api: ncheader2json"
        " -i <path-to-nc-file> |"
        " curl -X POST -H 'Content-Type: application/json'  -d @- '<url-to-api>'"
    )

    parser.add_argument("-i", "--input", type=str, help="Input file", required=True)

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output json file, if unset the json is dumped to stdout.",
        required=False,
    )

    parser.add_argument(
        "-e", "--file-ending", default="nc", type=str, help="File ending of nc files"
    )

    return parser


def get_header_netCDF(data: Dataset) -> dict:
    """
    This function grabs all global and variable attributes and dumps them into a json file.
    """
    full_attr = {
        "global_variables": {i: data.getncattr(i) for i in data.ncattrs()},
        "variables": {},
    }

    for var_name, variable in data.variables.items():
        full_attr["variables"][var_name] = {
            "attrs": {i: handle_numpy_types(variable.getncattr(i)) for i in variable.ncattrs()},
            "dtype": str(variable.dtype),
            "shape": variable.shape,
        }

    return json.dumps(full_attr)


def handle_numpy_types(inpt):
    """
    Some numpy types can not be converted or parsed to a json object.
    This functions handles conversion from un-parsable types, to parsable ones.
    """
    if isinstance(inpt, np.float32):
        return np.float64(inpt)

    if isinstance(inpt, np.int64):
        return inpt.item()

    if isinstance(inpt, np.int16):
        return inpt.item()

    if isinstance(inpt, np.ndarray):
        return inpt.tolist()

    return inpt


def main(args=None):
    """Main function for this script"""
    if pathlib.Path(args.input).is_file():
        inputfiles = [args.input]
    else:
        raise ValueError(f"Invalid input: {args.input}")

    json_header = [json.loads(get_header_netCDF(Dataset(file))) for file in inputfiles][0]

    if args.output:
        with open(args.output, "w") as fp:
            json.dump(json_header, fp)
    else:
        print(json.dumps(json_header))

    return json_header


def _main():  # pragma: no cover
    main(create_parser().parse_args())  # entry point


if __name__ == "__main__":  # pragma: no cover
    main(create_parser().parse_args())
