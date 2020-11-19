#!/usr/bin/env python3

"""
Script to check the validity of MMD files.
Input can be either a single MMD file or a repertory, in which case all the xml files contained
in it will be checked.
Validity means that the XML file is valid against the schema given as reference.
Optional in depth checks (-f True)

License:
     This file is part of the S-ENDA-Prototype repository (https://github.com/metno/py-mmd-tools).
     S-ENDA-Prototype is licensed under GPL-3.0 (https://github.com/metno/py-mmd-tools/blob/master/LICENSE)

Usage: checkMMD.py [-h] -i INPUT -x MMD_XSD -l LOG_DIR [-f FULL]
Example: python checkMMD.py -i /home/Data/mmd/Output/ -x /home/mmd/xsd/mmd.xsd -l /home/Logs/ -f False
"""

import argparse
import logging.handlers
import lxml.etree as ET
from pathlib import Path
from py_mmd_tools.xml_utils import xml_check, full_check


def parse_arguments():
    parser = argparse.ArgumentParser(description="Check if an xml file is a valid MMD file.")
    parser.add_argument("-i", "--input", help="input: XML file or directory containing XML files",
                        required=True)
    parser.add_argument("-x", "--mmd-xsd", help="MMD schema", required=True)
    parser.add_argument("-f", "--full", help="Perform full check?", required=False, default=True)
    parser.add_argument('-l', "--log-dir", help="Logs path", required=True)
    return parser.parse_args()


if __name__ == "__main__":

    args = parse_arguments()

    logDir = Path(args.log_dir)
    log_info = logging.handlers.RotatingFileHandler(logDir / 'mmd_check.log', maxBytes=1000000,
                                                    backupCount=2)
    log_info.setLevel(logging.INFO)
    log_debug = logging.handlers.RotatingFileHandler(logDir / 'mmd_check_debug.log',
                                                     maxBytes=1000000, backupCount=10)
    log_debug.setLevel(logging.DEBUG)
    log_info.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    log_debug.setFormatter(
        logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(log_info)
    logger.addHandler(log_debug)

    # Get list of input XML files
    if Path(args.input).is_file():
        xml_list = [args.input]
    elif Path(args.input).is_dir():
        xml_list = Path(args.input).glob('*.xml')
    else:
        logging.error(f"Invalid input argument ({args.input}) neither an existing file nor an "
                      f"existing directory")
        exit(1)

    # Read MMD schema
    mmd_schema = ET.XMLSchema(ET.parse(args.mmd_xsd))

    fcount = 0
    for xml_file in xml_list:

        fcount += 1
        if not xml_check(str(xml_file)):
            logger.info(f'Validation not performed: file {xml_file} is not a valid XML file.')
            continue

        # Read XML file
        xml_doc = ET.ElementTree(file=str(xml_file))

        # Validate XML file against schema
        try:
            mmd_schema.assertValid(xml_doc)
            logger.info(f'OK - File {xml_file} valid.')
        except ET.DocumentInvalid as e:
            logger.info(f'NOK - File {xml_file} not valid.')
            logger.debug(e)

        if args.full:
            logger.info('Performing in depth checking.')
            full = full_check(xml_doc)

    if fcount == 0:
        logger.info(f'No xml files found in {args.input}')
