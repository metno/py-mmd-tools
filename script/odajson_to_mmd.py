import argparse

from py_mmd_tools import odajson_to_mmd

"""
Script to run the odajson_to_mmd method

 License:
     This file is part of the py-mmd-tools repository (https://github.com/metno/py-mmd-tools).
     py-mmd-tools is licensed under GPL-3.0 (https://github.com/metno/py-mmd-tools/blob/master/LICENSE)

Usage: python script/odajson_to_mmd.py [-h] -i INPUT_JSON or FROST -o OUTPUT_DIRECTORY -d ODA_DEFAULT_YML -t ODA_TEMPLATE_XML [--mmd-validation [MMD_VALIDATION]] [--xsd-mmd XSD_MMD] 
EXAMPLE: python script/odajson_to_mmd.py -i 'FROST' -o '~/Data/Output/' -d 'oda_default.yml' -t 'oda_to_mmd_template.xml'
"""


def parse_arguments():
    parser = argparse.ArgumentParser(description='Create mmd xml for ODA data (from request to FROST API).', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i', 
                        dest='input_data',
                        required=True,
                        #default='FROST',
                        help="Input data: FROST or single Json input file.")
    parser.add_argument('-o', 
                        dest='output_dir',
                        required=True,
                        help="Output path.")
    parser.add_argument('-d',
                        dest='oda_default',
                        required=True,
                        help="YML file containing ODA default metadata.")
    parser.add_argument('-t', 
                        dest='oda_mmd_template',
                        required=True,
                        help="Template mmd for ODA data.")
    parser.add_argument('--mmd-validation',
                        type=str2bool,
                        nargs="?",
                        default=False,
                        required=False,
                        const=True,
                        help="Validate against MMD schema? (True/False)")
    parser.add_argument('--xsd-mmd',
                        required=False,
                        help="XSD MMD.")
    args = parser.parse_args()
    return args


def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ("yes", "true", "t", "y", "1"):
        return True
    elif v.lower() in ("no", "false", "f", "n", "0"):
        return False
    else:
        raise argparse.ArgumentTypeError("Boolean value expected.")


if __name__ == '__main__':

    args = parse_arguments()
    input_data = args.input_data
    output_dir = args.output_dir
    oda_default = args.oda_default
    oda_mmd_template = args.oda_mmd_template
    xsd_mmd = args.xsd_mmd
    validate = args.mmd_validation

    ##import confuse
    ##config = confuse.Configuration('mmdtool', __name__)
    ##input_data = config['paths']['example_input_json'].get()
    ##input_data = 'FROST'
    ##output_dir = config['paths']['output_dir'].get()
    ##oda_default = config['paths']['oda_default_yml'].get()
    ##oda_mmd_template = config['paths']['oda_template_xml'].get()
    ##xsd_mmd = config['paths']['xsd_mmd'].get()
    ##validate = True

    odajson_to_mmd.main(input_data, output_dir, oda_default, oda_mmd_template, validate, xsd_mmd)


