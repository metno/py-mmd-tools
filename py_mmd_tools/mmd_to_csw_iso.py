"""
Tool for converting metadata from MMD format to ISO format using a specific xslt.
Author:    Massimo Di Stefano,
Created:   03.10.2020 (dd.mm.YYYY)
Copyright: (c) Norwegian Meteorological Institute
Usage: 
EXAMPLE: 
"""

import lxml.etree as ET
import pathlib
from mmd_util import mmd_check, setup_log
import time
import confuse
from confuse.exceptions import NotFoundError    
import logging

def mmd_to_iso(mmd_file, outputfile, mmd2isocsw=None, mmd_validation=False, mmd_xsd_schema=None, iso_validation=False):
    logger = setup_log('mmd_to_iso')
    """[Transform MMD file to ISO using xslt]
    Args:
        mmd_file ([str]): [filepath to an mmd xml file]
        mmd2isocsw ([str]): [filepath to an mmd to iso xslt file]
        mmd_validation ([bool]): [if true, performs validation on the provided mmd xml file]
        iso_validation ([bool]): [if true, performs validation on the output iso xml file]
        outputfile ([str]): [filepath to output iso xml file]
    Returns:
        [bool]: [return True if a the MMD filepath provided is succesfully converted to ISO, 
        return False if the mmd xmlfile is invalid, or doesn't exist or conversion to iso Failed ]
    """
    if mmd_validation:
        if not mmd_check(mmd_file, mmd_xsd_schema=mmd_xsd_schema):
            return False
    else:
        if not mmd2isocsw:
            try:
                config = confuse.Configuration('mmdtool', __name__)
                mmd2isocsw=config['paths']['mmd2isocsw'].get()
            except NotFoundError:
                logger.error(f'path to mmd2isocsw not provided and/or not found in the configuration file')
                return False
    mmd_doc = ET.ElementTree(file=mmd_file)
    transform_to_iso = ET.XSLT(ET.parse(mmd2isocsw))
    iso_doc = transform_to_iso(mmd_doc)
    mmd_xml_as_string = ET.tostring(iso_doc, pretty_print=True,
                                    encoding='unicode')                                             
    if iso_validation:
        try:
            config = confuse.Configuration('mmdtool', __name__)
            iso_xsd_schema = config['paths']['iso_xsd'].get()
        except NotFoundError:
            logger.error(f'path to mmd2isocsw not provided and/or not found in the configuration file')
            return False
        xmlschema_iso = ET.XMLSchema(ET.pardse(iso_xsd_schema))
        if not xmlschema_iso.validate(ET.fromstring(mmd_xml_as_string)):
            logger.error(f'iso validation failed on iso tansformed {mmd_file}') 
            return False
    if pathlib.Path(outputfile).is_file():
        logger.warning(f'file {outputfile} already exist and will be overwrite')         
        time.sleep(2)
    with open(outputfile, 'w') as output:
        output.write(mmd_xml_as_string)
        logger.info(f'ISO xml output wrote to: {outputfile}')
        return True