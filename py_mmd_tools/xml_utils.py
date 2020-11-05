"""
Utility tool to work on mmd xml files.
 License:
     This file is part of py-mmd-tools, licensed under the Apache License 2.0 (https://www.apache.org/licenses/LICENSE-2.0)
"""

import pathlib
import errno
import os
import lxml.etree as ET
from datetime import datetime
from lxml.etree import XMLSyntaxError
import errno
import os


def xml_check(xml_file):
    """ Validate xml syntax from filepath.

    Args:
        xml_file ([str]): [filepath to an xml file]
    Returns:
        [bool]: [return True if a valid xml filepath is provided, 
        raises an exception if the xmlfile is invalid, empty, or doesn't exist ]
    """
    if pathlib.Path(xml_file).is_file() and os.path.getsize(xml_file) != 0:
        try:
            # ET.parse will raise an OSError if the file does not exist
            xml = ET.parse(xml_file)
        except XMLSyntaxError:
            raise 
    else:
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), xml_file)
    
    return True



def xsd_check(xml_file, xsd_schema=None):
    """[validate xml file from filepath]
    Args:
        xmlfile ([str]): [filepath to an xml file]
        xsd_schema ([str]): [filepath to an xsd schema file]
    Returns:
        [bool]: [return True if a valid xml filepath is provided, 
        return False if the xmlfile is invalid, empty, or doesn't exist ]
    """
    xmlschema_mmd = ET.XMLSchema(ET.parse(xsd_schema))
    xml_doc = ET.ElementTree(file=xml_file)
    if not xmlschema_mmd.validate(xml_doc):
        passing=False
    else:
        passing=True
    return passing

def xml_translate(
    xml_file,
    outputfile,
    xslt,
    xsd_validation=False,
    xsd_schema=None,
):
    """[Transform XML file using xslt]
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
                raise
    else:
        if not pathlib.Path(xslt).exists():
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), xslt)
    try:
        xml_doc = ET.ElementTree(file=xml_file)
        transform = ET.XSLT(ET.parse(xslt))
        new_doc = transform(xml_doc)
    except OSError:
        result=False
    xml_as_string = ET.tostring(new_doc, pretty_print=True, encoding="unicode")
    with open(outputfile, "w") as output:
        output.write(xml_as_string)
        result=True
    return result
