"""
Tool for converting metadata from MMD format to ISO format using a specific xslt.

 License:
     This file is part of the S-ENDA-Prototype repository (https://github.com/metno/py-mmd-tools).
     S-ENDA-Prototype is licensed under GPL-3.0 (https://github.com/metno/py-mmd-tools/blob/master/LICENSE)
"""

import logging
import pathlib
import time

import confuse
import lxml.etree as ET
from confuse.exceptions import NotFoundError
from py_mmd_tools.mmd_util import mmd_check
from py_mmd_tools.log_util import setup_log
import errno
import os

def mmd_to_iso(
    mmd_file,
    outputfile,
    mmd2isocsw=None,
    mmd_validation=False,
    mmd_xsd_schema=None,
    iso_validation=False,
):
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
    logger = setup_log("mmd_to_iso")
    if not pathlib.Path(mmd_file).exists():
        logger.error(
                    f"path to {mmd_file} not found"
                )
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), mmd_file)
        
    if mmd_validation:
        if not mmd_check(mmd_file, mmd_xsd_schema=mmd_xsd_schema):
            return False
    else:
        if not mmd2isocsw:
            try:
                config = confuse.Configuration("mmdtool", __name__)
                mmd2isocsw = config["paths"]["mmd2isocsw"].get()
            except NotFoundError:
                logger.error(
                    f"path to mmd2isocsw not provided and/or not found in the configuration file"
                )
                return False
    
    mmd_doc = ET.ElementTree(file=mmd_file)
    transform_to_iso = ET.XSLT(ET.parse(mmd2isocsw))
    iso_doc = transform_to_iso(mmd_doc)
    mmd_xml_as_string = ET.tostring(iso_doc, pretty_print=True, encoding="unicode")
    if iso_validation:
        try:
            config = confuse.Configuration("mmdtool", __name__)
            iso_xsd_schema = config["paths"]["iso_xsd"].get()
        except NotFoundError:
            logger.error(
                f"path to mmd2isocsw not provided and/or not found in the configuration file"
            )
            return False
        xmlschema_iso = ET.XMLSchema(ET.pardse(iso_xsd_schema))
        if not xmlschema_iso.validate(ET.fromstring(mmd_xml_as_string)):
            logger.error(f"iso validation failed on iso tansformed {mmd_file}")
            return False
    if pathlib.Path(outputfile).is_file():
        logger.warning(f"file {outputfile} already exist and will be overwrite")
        # TODO: give time to hit ctrl+c in case of unwanted file overwriting?
        # or prompt the user to accept overwriting unless a specifig flag/option is used?
    with open(outputfile, "w") as output:
        output.write(mmd_xml_as_string)
        logger.info(f"ISO xml output wrote to: {outputfile}")
        return True
