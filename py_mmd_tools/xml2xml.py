"""
Tool for converting metadata from MMD format to ISO format using a specific xslt.
 License:
     This file is part of the S-ENDA-Prototype repository (https://github.com/metno/py-mmd-tools).
     S-ENDA-Prototype is licensed under GPL-3.0 (https://github.com/metno/py-mmd-tools/blob/master/LICENSE)
"""

import pathlib
import time

import lxml.etree as ET
from py_mmd_tools.xml_util import xml_check, xsd_check
import errno
import os

def xml2xml(
    xml_file,
    outputfile,
    xslt,
    xsd_validation=False,
    xsd_schema=None,
):
    """[Transform MMD file to ISO using xslt]
    Args:
        xml_file ([str]): [filepath to an xml file]
        xslt ([str]): [filepath to a xsl transformation file]
        xsd_validation ([bool]): [if true, performs validation on the provided xml file - requires an xsd schema]
        xsd_schema ([str]): [xsd schema file used if xsd_validation is True]
        outputfile ([str]): [filepath to output iso xml file]
    Returns:
        [bool]: [return True if a the XML filepath provided is succesfully converted using the given XSLT, 
        return False if the xmlfile is invalid, or doesn't exist or the xsl transformation failed ]
    """
    if not pathlib.Path(xml_file).exists():
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), xml_file)
        
    if xsd_validation:
        if xsd_schema is None:
            raise TypeError
        if not pathlib.Path(xsd_schema).exists():
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), xsd_schema)
        else: 
            if not xsd_check(xml_file, xsd_schema=xsd_schema):
                return False
    else:
        if not pathlib.Path(xslt).exists():
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), xslt)
    try:
        xml_doc = ET.ElementTree(file=xml_file)
        transform = ET.XSLT(ET.parse(xslt))
        new_doc = transform(xml_doc)
    except OSError:
        return False
    xml_as_string = ET.tostring(new_doc, pretty_print=True, encoding="unicode")
    with open(outputfile, "w") as output:
        output.write(xml_as_string)
        return True
