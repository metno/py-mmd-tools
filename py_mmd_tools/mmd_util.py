"""
Utility tool to work on mmd xml files.

 License:
     This file is part of the S-ENDA-Prototype repository (https://github.com/metno/S-ENDA-Prototype).
     S-ENDA-Prototype is licensed under GPL-3.0 (https://github.com/metno/S-ENDA-Prototype/blob/master/LICENSE)
"""

import lxml.etree as ET
import pathlib
import time

import confuse
from confuse.exceptions import NotFoundError    

import logging

def get_logpath():
    try:
        config = confuse.Configuration('mmdtool', __name__)
        logfilepath=config['paths']['logs'].get()
    except NotFoundError:
        logfilepath = './logs/'
    if not pathlib.Path(logfilepath).exists():
       pathlib.Path(logfilepath).mkdir(parents=True, exist_ok=True)
    return logfilepath



import logging

def setup_log(name):
    logfilepath=get_logpath()
    logger = logging.getLogger(name)   # > set up a new name for a new logger

    logger.setLevel(logging.DEBUG)  # here is the missing line

    log_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    filename = pathlib.Path(logfilepath, f"{name}.log")
    log_handler = logging.FileHandler(filename)
    log_handler.setLevel(logging.DEBUG)
    log_handler.setFormatter(log_format)
    logger.addHandler(log_handler)
    return logger


def xml_check(xml_file):
    logger = setup_log('xml_check')
    """[validate xml syntax from filepath]
    Args:
        xml_file ([str]): [filepath to an xml file]
    Returns:
        [bool]: [return True if a valid xml filepath is provided, 
        return False if the xmlfile is invalid, or doesn't exist ]
    """
    if pathlib.Path(xml_file).is_file():
        try:
            xml = ET.parse(xml_file)
            logger.info(f'valid xml file {xml_file} passed to xml_check')
            return True
        except ET.XMLSyntaxError:
            try:
                xml = ET.XML(bytes(bytearray(xml_file, encoding='utf-8')))
                logger.info(f'valid xml file {xml_file} passed to xml_check')
                return True
            except ET.XMLSyntaxError:
                logger.warning(f'invalid xml file {xml_file} passed to xml_check')
                return False
    else:
        logger.warning(f'xml file {xml_file} not found')
        return False


    
def mmd_check(mmd_file, mmd_xsd_schema=None):
    logger = setup_log('mmd_check')
    """[validate MMD file from filepath]
    Args:
        mmd_file ([str]): [filepath to an mmd xml file]
        mmd_xsd_schema ([str]): [filepath to an mmd xsd schema file]
    Returns:
        [bool]: [return True if a valid MMD filepath is provided, 
        return False if the mmd xmlfile is invalid, or doesn't exist ]
    """
    if not xml_check(mmd_file):
        logger.error(f'invalid xml file {mmd_file} passed to mmd_check')
        return False
    else:
        if not mmd_xsd_schema:
            try:
                config = confuse.Configuration('mmdtool', __name__)
                mmd_xsd_schema=config['paths']['mmd_xsd'].get()
            except NotFoundError:
                logger.error(f'path to mmd_xsd not provided and/or not found in the configuration file')
                return False
        if pathlib.Path(mmd_xsd_schema).is_file() and xml_check(mmd_xsd_schema):
            xmlschema_mmd = ET.XMLSchema(ET.parse(mmd_xsd_schema))
            mmd_doc = ET.ElementTree(file=mmd_file)
            if not xmlschema_mmd.validate(mmd_doc):
                logger.error(f'mmd validation failed')
                return False
            else:
                logger.info(f'valid mmd file {mmd_file} passed to mmd_check')
                return True
        else:
            logger.error(f'provided path to mmd_xsd: {mmd_xsd_schema} - not found')
            return False

