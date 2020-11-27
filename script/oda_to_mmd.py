#!/usr/bin/env python3

import argparse
import os
from py_mmd_tools import odajson_to_mmd
import logging.handlers
import pathlib

"""
Script to run the odajson_to_mmd method

 License:
     This file is part of the py-mmd-tools repository (https://github.com/metno/py-mmd-tools).
     py-mmd-tools is licensed under GPL-3.0 (
     https://github.com/metno/py-mmd-tools/blob/master/LICENSE)

Usage: python script/oda_to_mmd.py [-h] -o OUTPUT_DIRECTORY -l LOG_DIRECTORY -d ODA_DEFAULT_YML 
-t ODA_TEMPLATE_XML [-f FROST_URL] [--mmd-validation [MMD_VALIDATION]] [--xsd-mmd XSD_MMD] 
EXAMPLE: python script/oda_to_mmd.py -o '~/Data/Output/' -l '~/Logs/' -d 'oda_default.yml' -t 
'oda_to_mmd_template.xml'
"""


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Create mmd xml for ODA data (from request to FROST API).',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-o',
                        dest='output_dir',
                        required=True,
                        help="Output path.")
    parser.add_argument('-l',
                        dest='log_dir',
                        required=True,
                        help="Logs path.")
    parser.add_argument('-d',
                        dest='oda_default',
                        required=True,
                        help="YML file containing ODA default metadata.")
    parser.add_argument('-t',
                        dest='oda_mmd_template',
                        required=True,
                        help="Template mmd for ODA data.")
    parser.add_argument('-f',
                        dest='frost_url',
                        required=False,
                        default='frost-staging.met.no',
                        help="FROST URL.")
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
    return parser.parse_args()


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

    logDir = pathlib.Path(args.log_dir)
    log_info = logging.handlers.RotatingFileHandler(logDir / 'oda.log', maxBytes=1000000,
                                                    backupCount=2)
    log_info.setLevel(logging.INFO)
    log_debug = logging.handlers.RotatingFileHandler(logDir / 'oda_debug.log', maxBytes=1000000,
                                                     backupCount=10)
    log_debug.setLevel(logging.DEBUG)
    log_info.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    log_debug.setFormatter(
        logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(log_info)
    logger.addHandler(log_debug)

    # Get list of available stations
    # For now, request frost.met.no instead of frost_url as this service is not available on the
    # staging API
    frost_id = os.getenv('FROST_ID')
    if frost_id is None:
        logger.error("Environment variable FROST_ID not set. Exiting.")
        exit(1)
    stations_list = odajson_to_mmd.retrieve_frost_stations('https://frost.met.no/sources/v0.jsonld',
                                                           frost_id)

    # Looping over available stations
    for station in stations_list:
        if all(k in station for k in ("name", "id")):
            logger.info("Processing station %s (id %s)" % (station['name'], station['id']))
            odajson_to_mmd.process_station(station['id'][2:], station['name'],
                                           os.path.join(args.output_dir,
                                                        station['id']), args.oda_default,
                                           args.oda_mmd_template, args.frost_url,
                                           args.mmd_validation, args.xsd_mmd)
        else:
            logger.info(
                "Not processing this station as 'name' and/or 'id' are missing.\n Station data: %s" % station)
            continue
