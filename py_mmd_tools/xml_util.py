"""
Utility tool to work on mmd xml files.
 License:
     This file is part of the S-ENDA-Prototype repository (https://github.com/metno/py-mmd-tools).
     S-ENDA-Prototype is licensed under GPL-3.0 (https://github.com/metno/py-mmd-tools/blob/master/LICENSE)
"""

import pathlib
import time
import errno
import os
import lxml.etree as ET
from datetime import datetime

import confuse
from confuse.exceptions import NotFoundError
import logging

def get_logpath(config_name='mmdtool'):
    try:
        config = confuse.Configuration(config_name, __name__)
        logfilepath = config["paths"]["logs"].get()
    except NotFoundError:
        logfilepath = "./logs/"
    if not pathlib.Path(logfilepath).exists():
        pathlib.Path(logfilepath).mkdir(parents=True, exist_ok=True)
    return logfilepath


def setup_log(name, logtype='file'):
    ''' logtype = [file, stream, all]'''
    logfilepath = get_logpath()
    logger = logging.getLogger(name)  # > set up a new name for a new logger
    logger.setLevel(logging.DEBUG)  # here is the missing line
    log_format = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    # filehandler
    filename = pathlib.Path(logfilepath, f"{name}.log")
    fh = logging.FileHandler(filename, mode='w', encoding='utf-8')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(log_format)
    # streamhandler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(log_format)
    if logtype=='file':
        logger.addHandler(fh)
    if logtype=='stream':
        logger.addHandler(ch)
    if logtype=='all':
        logger.addHandler(fh)
        logger.addHandler(ch)
    return logger

def xml_check(xml_file):
    """[validate xml syntax from filepath]
    Args:
        xml_file ([str]): [filepath to an xml file]
    Returns:
        [bool]: [return True if a valid xml filepath is provided, 
        return False if the xmlfile is invalid, empty, or doesn't exist ]
    """
    if pathlib.Path(xml_file).is_file() and os.path.getsize(xml_file) != 0:
        try:
            xml = ET.parse(xml_file)
            return True
        except ET.XMLSyntaxError:
            try:
                xml = ET.XML(bytes(bytearray(xml_file, encoding="utf-8")))
                return True
            except ET.XMLSyntaxError:
                return False
    else:
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), xml_file)


def xsd_check(xml_file, xsd_schema=None):
    """[validate xml file from filepath]
    Args:
        xmlfile ([str]): [filepath to an mmd xml file]
        xsd_schema ([str]): [filepath to an xsd schema file]
    Returns:
        [bool]: [return True if a valid xml filepath is provided, 
        return False if the xmlfile is invalid, empty, or doesn't exist ]
    """
    if not pathlib.Path(xsd_schema).is_file() and os.path.getsize(xsd_schema) != 0:
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), xml_file)
    else:
        if pathlib.Path(xsd_schema).is_file() and xml_check(xsd_schema):
            xmlschema_mmd = ET.XMLSchema(ET.parse(xsd_schema))
            xml_doc = ET.ElementTree(file=xml_file)
            if not xmlschema_mmd.validate(xml_doc):
                return False
            else:
                return True
