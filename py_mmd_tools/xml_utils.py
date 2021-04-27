"""
Utility tool to work on mmd xml files.

License: This file is part of py-mmd-tools, licensed under the Apache License 2.0 (https://www.apache.org/licenses/LICENSE-2.0)
"""

import pathlib
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



def xsd_check(xml_file, xsd_schema):
    """[validate xml file from filepath]
    Args:
        xmlfile ([str]): [filepath to an xml file]
        xsd_schema ([str]): [filepath to an xsd schema file]
    Returns:
        [bool]: [return True if a valid xml filepath is provided, 
        return False if the xmlfile is invalid, empty, or doesn't exist ]
    """
    if not pathlib.Path(xml_file).exists():
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), xml_file)
    if not pathlib.Path(xsd_schema).exists():
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), xsd_schema)
    xmlschema_mmd = ET.XMLSchema(ET.parse(xsd_schema))
    xml_doc = ET.ElementTree(file=xml_file)
    valid = xmlschema_mmd.validate(xml_doc)
    msg = xmlschema_mmd.error_log
    return valid, msg

def xml_translate_and_write(xml_file, outputfile, xslt, xsd_validation=False, xsd_schema=None):
    """ Translate the provided `xml_file` and write the result to an output xml file.

    Input
    =====
        xml_file : str
            Path to the xml file that should be translated
        outputfile : str
            Path to output xml file
        xslt : str
            Path to an xsl translation file

    Options
    =======
        xsd_validation : boolean
            Validate input `xml_file` if True
        xsd_schema : string
            Path to an xsd schema used in validation

    Returns
    =======
        bool
           True if the output file was successfully written
           False if translation and file creation fails
    """
    if xsd_validation:
        valid, msg = xsd_check(xml_file, xsd_schema)
        if not valid:
            raise Exception(msg)

    if not pathlib.Path(xslt).exists():
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), xslt)

    try:
        xml_as_string = xml_translate(xml_file, xslt)
    except OSError:
        result=False

    with open(outputfile, "w") as output:
        output.write(xml_as_string)
        result=True
    return result

def xml_translate(xml_file, xslt):
    """ Translate XML file using xslt

    Input
    =====
        xml_file : str
            Path to the xml file that should be translated
        xslt : str
            Path to the xsl translation file

    Returns
    =======
        str
            xml document
    """
    if not pathlib.Path(xml_file).exists():
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), xml_file)
        
    xml_doc = ET.ElementTree(file=xml_file)
    transform = ET.XSLT(ET.parse(xslt))
    new_doc = transform(xml_doc)

    return ET.tostring(new_doc, pretty_print=True, encoding="unicode")
