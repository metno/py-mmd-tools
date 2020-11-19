"""
Tools for checking if an XML MMD file is valid.

License:
     This file is part of the py-mmd-tools repository (https://github.com/metno/py-mmd-tools).
     py-mmd-tools is licensed under GPL-3.0 (
     https://github.com/metno/py-mmd-tools/blob/master/LICENSE)
"""

import logging

logger = logging.getLogger(__name__)


def check_rectangle(rectangle):
    """
    Check if element geographic extent/rectangle is valid:
        - only 1 existing rectangle element
        - -180 <= min_lat <= max_lat <= 180
        -    0 <= min_lon <= max_lon <= 360
    Args:
        rectangle: list of elements found when requesting node(s) geographic_extent/rectangle
          (output of ET request findall)
    Returns:
        True / False
    """

    directions = dict.fromkeys(['north', 'south', 'west', 'east'], 0)

    err = 0
    if len(rectangle) > 1:
        logger.debug("NOK - Multiple rectangle elements in file.")
        return False

    for child in rectangle[0]:
        # Remove namespace if any
        if child.tag.startswith("{"):
            child.tag = child.tag.split('}', 1)[1]
        directions[child.tag] = float(child.text)

    if not (-180 <= directions['west'] <= directions['east'] <= 180):
        logger.debug('NOK - Longitudes not ok')
        err += 1
    if not (-90 <= directions['south'] <= directions['north'] <= 90):
        logger.debug('NOK - Latitudes not ok')
        err += 1
    if err > 0:
        logger.debug(directions)
        return False

    return True


def full_check(doc):
    """
    Main checking scripts for in depth checking of XML file.
    Args:
        doc:  ElementTree containing the full XML document
    Returns:
       True / False
    """

    valid = True
    root = doc.getroot()

    # If there is an element geographic_extent/rectangle, check that lat/lon are valid
    rectangle = doc.findall('./mmd:geographic_extent/mmd:rectangle', namespaces=root.nsmap)
    rect = True
    if len(rectangle) > 0:
        logger.debug('Checking element geographic_extent/rectangle')
        rect = check_rectangle(rectangle)
        if rect:
            logger.info('OK - geographic_extent/rectangle')
    valid = valid * rect

    return valid
