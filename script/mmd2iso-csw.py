import argparse

from py_mmd_tools import mmd_to_csw_iso

"""
Script to run the mmd_to_csw_iso.mmd_to_iso method

 License:
     This file is part of the S-ENDA-Prototype repository (https://github.com/metno/py-mmd-tools).
     S-ENDA-Prototype is licensed under GPL-3.0 (https://github.com/metno/py-mmd-tools/blob/master/LICENSE)

Usage: python mmd2iso-csw.py [-h] -i INPUT_MMD -o OUTPUT_ISO -t INPUT_XSLT [--xsd-mmd XSD_MMD] [--mmd-validation [MMD_VALIDATION]]
EXAMPLE: python script/mmd2iso-csw.py -i sentinel-1-mmd.xml -o out.xml --mmd-validation 'False'
"""


def main(mmd_file, outputfile, mmd2isocsw, mmd_xsd_schema, mmd_validation):
    # print(mmd_validation)
    mmd_to_csw_iso.mmd_to_iso(
        mmd_file=mmd_file,
        outputfile=outputfile,
        mmd2isocsw=mmd2isocsw,
        mmd_xsd_schema=mmd_xsd_schema,
        mmd_validation=mmd_validation,
    )


def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ("yes", "true", "t", "y", "1"):
        return True
    elif v.lower() in ("no", "false", "f", "n", "0"):
        return False
    else:
        raise argparse.ArgumentTypeError("Boolean value expected.")


def parse_arguments():
    #
    parser = argparse.ArgumentParser(description="Convert mmd xml files to ISO")
    parser.add_argument("-i", "--input-mmd", help="mmd input file", required=True)
    parser.add_argument("-o", "--output-iso", help="output ISO file", required=True)
    parser.add_argument(
        "-t", "--input-xslt", help="input xslt translation file", required=False
    )
    parser.add_argument(
        "--xsd-mmd", help="input xsd validation file for mmd", required=False
    )
    parser.add_argument(
        "--mmd-validation",
        type=str2bool,
        nargs="?",
        const=True,
        default=False,
        help="validate mmd input file.",
    )
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = parse_arguments()

    # import confuse
    # config = confuse.Configuration('mmdtool', __name__)
    # mmd_file = config['paths']['example_mmd'].get()
    # mmd2isocsw = config['paths']['mmd2isocsw'].get()
    # outputfile = 'out.xml'

    mmd_file = args.input_mmd
    mmd2isocsw = args.input_xslt
    outputfile = args.output_iso
    mmd_xsd_schema = args.xsd_mmd
    mmd_validation = args.mmd_validation

    main(
        mmd_file=mmd_file,
        outputfile=outputfile,
        mmd2isocsw=mmd2isocsw,
        mmd_xsd_schema=mmd_xsd_schema,
        mmd_validation=mmd_validation,
    )

