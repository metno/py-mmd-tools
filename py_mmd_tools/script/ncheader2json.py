#!/usr/bin/env python3

"""
Tool for extracting netCDF header to a json. For use in py-mmd-tools-api

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

    parser = argparse.ArgumentParser(description="Extract nc header to json format")

    parser.add_argument("-i", "--input", type=str, help="Input file or folder", required=True)

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output json file, if unset the json is dumped to stdout. "
        "If a folder is input, the original file name will be appended.",
        required=False,
    )

    parser.add_argument(
        "-e", "--file-ending", default="nc", type=str, help="File ending of nc files"
    )

    return parser


def get_header_netCDF(data: Dataset) -> dict:
    """
    This function grapb all global and variable attributes and dumps it in to a json.
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

    if isinstance(inpt, np.ndarray):
        return inpt.tolist()

    return inpt


def main(args=None):
    """Main function for this script"""
    if pathlib.Path(args.input).is_dir():
        inputfiles = pathlib.Path(args.input).glob("*.nc")
    elif pathlib.Path(args.input).is_file():
        inputfiles = [args.input]
    else:
        raise ValueError(f"Invalid input: {args.input}")

    json_header = [json.loads(get_header_netCDF(Dataset(file))) for file in inputfiles]

    if args.output:
        if len(json_header) > 1:
            for i, j in zip(inputfiles, json_header):
                with open(args.output + inputfiles.split("/")[-1], "w") as fp:
                    json.dump(i, fp)
        else:
            with open(args.output, "w") as fp:
                json.dump(json_header[0], fp)
    else:
        print(json_header)

    return json_header[0] if len(json_header) == 1 else json_header


def _main():  # pragma: no cover
    main(create_parser().parse_args())  # entry point


if __name__ == "__main__":  # pragma: no cover
    main(create_parser().parse_args())
