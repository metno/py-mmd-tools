"""
Tools for checking if an XML MMD file is valid.

License:
     This file is part of the py-mmd-tools repository (https://github.com/metno/py-mmd-tools).
     py-mmd-tools is licensed under GPL-3.0 (
     https://github.com/metno/py-mmd-tools/blob/master/LICENSE)
"""

import logging
import requests
import pythesint as pti

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


def check_urls(url_list):
    """
    Check that a list of URLs is valid
    Args:
        url_list: list of URLs
    Returns:
        True / False
    """

    errs = 0

    for url in url_list:

        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            logger.debug(f'OK - {url}')
            r.close()
        except Exception as e:
            logger.debug(f'NOK - {url}')
            logger.debug(e)
            errs += 1

    return errs == 0


def check_cf(cf_names):
    """
    Check that names are valid CF standard names
    Args:
        cf_names: list of names to test
    Returns:
        True / False
    """
    ok = True
    for cf_name in cf_names:
        try:
            pti.get_cf_standard_name(cf_name)
            logger.debug(f'OK - {cf_name} is a CF standard name.')
        except IndexError as e:
            logger.info(f'Non standard name found {cf_name}: {e}')
            ok = False
    return ok


def full_check(doc):
    """
    Main checking scripts for in depth checking of XML file.
     - checking URLs
     - checking lat-lon within geographic_extent/rectangle
    Args:
        doc:  ElementTree containing the full XML document
    Returns:
       True / False
    """

    valid = True

    # Get elements with urls and check for OK response
    url_elements = doc.xpath('.//*[contains(text(),"http")]')
    urls = [elem.text for elem in url_elements]
    if len(urls) > 0:
        logger.debug('Checking element(s) containing URL ...')
        urls_ok = check_urls(urls)
        if urls_ok:
            logger.info('OK - URLs')
        else:
            logger.info('NOK - URLs -> check debug log')
        valid = valid and urls_ok
    else:
        logger.debug('No element containing URL.')

    # If there is an element geographic_extent/rectangle, check that lat/lon are valid
    rectangle = doc.findall('./{*}geographic_extent/{*}rectangle')
    if len(rectangle) > 0:
        logger.debug('Checking element geographic_extent/rectangle ...')
        rect_ok = check_rectangle(rectangle)
        if rect_ok:
            logger.info('OK - geographic_extent/rectangle')
        else:
            logger.info('NOK - geographic_extent/rectangle -> check debug log')
        valid = valid and rect_ok
    else:
        logger.debug('No geographic_extent/rectangle element.')

    # Check that cf name provided exist in reference Standard Name Table
    cf_elements = doc.findall('./{*}keywords[@vocabulary="Climate and Forecast Standard Names"]')
    if len(cf_elements) == 1:
        logger.debug('Checking elements keyword from vocabulary CF ...')
        cf_list = [elem.text for elem in cf_elements[0]]
        if len(cf_list) > 1:
            logger.info(f'NOK - CF names -> only one CF name should be provided - {cf_list}')
            valid = False
        # Check CF names even if more than one provided
        cf_ok = check_cf(cf_list)
        if cf_ok:
            logger.info('OK - CF names')
        else:
            logger.info('NOK - CF names -> check debug log')
        valid = valid and cf_ok
    elif len(cf_elements) > 1:
        valid = False
        logger.debug('NOK - More than one element with keywords[@vocabulary="Climate and '
                     'Forecast Standard Names"]')
    else:
        logger.debug('No CF standard names element.')

    return valid
