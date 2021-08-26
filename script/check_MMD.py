#!/usr/bin/env python3
"""
Script to check the validity of MMD files. Input can be either a single
MMD file or a repertory, in which case all the xml files contained in it
will be checked. Validity means that the XML file is valid against the
schema given as reference. Optional in depth checks (-f True).

License:

This file is part of the py-mmd-tools repository
<https://github.com/metno/py-mmd-tools>.

py-mmd-tools is licensed under the Apache License 2.0
<https://github.com/metno/py-mmd-tools/blob/master/LICENSE>

Usage:
    checkMMD.py [-h] -i INPUT -x MMD_XSD -l LOG_DIR [-f FULL]
Example:
    python checkMMD.py -i /home/Data/mmd/Output/ \
        -x /home/mmd/xsd/mmd_strict.xsd -l /home/Logs/ -f False
"""

import sys
import argparse
import logging.handlers
import lxml.etree as ET

from pathlib import Path
from py_mmd_tools.xml_utils import xml_check
from py_mmd_tools.check_mmd import full_check


def parse_arguments():
    """ToDo: Add docstring"""
    parser = argparse.ArgumentParser(description="Check if an xml file is a valid MMD file.")
    parser.add_argument(
        "-i", "--input",
        help="input: XML file or directory containing XML files",
        required=True
    )
    parser.add_argument("-x", "--mmd-xsd", help="MMD schema", required=True)
    # This has probably never been tried as False - the only way to set it to true is by adding
    # the flag, and then it needs to be False as default... Therefore, I comment it out..
    # parser.add_argument("-f", "--full", help="Perform full check?", required=False, default=True)
    parser.add_argument('-l', "--log-dir", help="Logs path", required=False)
    return parser.parse_args()


if __name__ == "__main__":

    args = parse_arguments()

    raise_error_if_invalid = False
    if args.log_dir:
        logDir = Path(args.log_dir)
        log_info = logging.handlers.RotatingFileHandler(
            logDir / 'mmd_check.log', maxBytes=1000000, backupCount=2
        )
        log_info.setLevel(logging.INFO)
        log_debug = logging.handlers.RotatingFileHandler(
            logDir / 'mmd_check_debug.log', maxBytes=1000000, backupCount=10
        )
    else:
        log_info = logging.StreamHandler(sys.stdout)
        log_debug = logging.StreamHandler(sys.stdout)
        raise_error_if_invalid = True

    log_debug.setLevel(logging.DEBUG)
    log_info.setFormatter(
        logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )
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
        logging.error(
            "Invalid input argument (%s) neither an existing file nor an  existing directory",
            args.input
        )
        sys.exit(1)

    fcount = 0
    for xml_file in xml_list:

        fcount += 1
        if not xml_check(str(xml_file)):
            logger.info('Validation not performed: file %s is not a valid XML file.', xml_file)
            continue

        # Read XML file
        xml_doc = ET.ElementTree(file=str(xml_file))

        logger.info('Performing in depth checking.')
        valid = full_check(xml_doc)
        if raise_error_if_invalid and not valid:
            raise Exception('Invalid xml file - please check the log..')

    if fcount == 0:
        logger.info('No xml files found in %s', args.input)

    logger.info('OK - The xml file is valid')
