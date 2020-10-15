"""
Tool for creating metadata (MMD format) for data from ODA database.

License:
     This file is part of the py-mmd-tools repository (https://github.com/metno/py-mmd-tools).
     py-mmd-tools is licensed under GPL-3.0 (https://github.com/metno/py-mmd-tools/blob/master/LICENSE)
"""

import json
import yaml
import copy
import jinja2
import requests
import pathlib
import errno
import os
from py_mmd_tools.xml_util import xsd_check
import logging

logger = logging.getLogger(__name__)


def retrieve_from_url(point, user_id='', user_pwd='', timeout_secs=10):
    """
    Request from an URL
    Args:
        point (str): URL to request to
        user_id (str): optional, user name, default=''
        user_pwd (str): optional, user password, default=''
        timeout_secs (int): optional, timeout in seconds, default=10
    Returns:
        request object or None if the request fails.
    """

    try:
        r = requests.get(point, auth=(user_id, user_pwd), timeout=timeout_secs)
        logger.debug('Data retrieved OK.')
    except requests.exceptions.RequestException as e:
        logger.error(e)
        return None
    return r


def retrieve_frost_stations(url, user_id):
    stations_req = retrieve_from_url(url, user_id)
    try:
        stations_list = stations_req.json()['data']
    except (AttributeError, KeyError, TypeError):
        logger.error('Unable to get stations list from request.')
        return []
    return stations_list


def process_station(station_id, station_name, outdir, default_file, mmd_template, frost_url, validate=False,
                    mmd_schema=None):
    """
    Process metadata from one station:
     - request metadata information from all available datasets from station
     - create MMD file for each dataset
    Args:
        station_id (str): station identifier
        station_name (str): station name
        outdir (str): directory where created MMD files will be saved
        default_file (str): YAML file containing the default metadata (generic metadata used for all datasets)
        mmd_template (str): XML template file
        frost_url (str): url to query
        validate (bool): Validate created MMD file against schema? default=False
        mmd_schema (str): XSD file containing the schema to validate against. default=None
    Returns:
        True if function succeeded, False otherwise
    """

    # Station URL
    st_url = 'https://' + frost_url + '/api/v1/availableoda?stationid=' + station_id
    logger.debug('Retrieving FROST data for station %s (id: %s).' % (station_name, station_id))

    # Request metadata (ODA tags) for all datasets of station
    st_req = retrieve_from_url(st_url)
    if st_req is None:
        logger.error('Unable to retrieve station data.')
        return False

    # Filter out stations with no metadata information
    try:
        st_data = st_req.json()
    except json.decoder.JSONDecodeError:
        logger.info('No metadata available for station %s (id %s).' % (station_name, station_id))
        logger.debug(st_req.text)
        return False

    logger.debug('%s datasets for station %s (id %s).' % (len(st_data), station_name, station_id))

    # Read static metadata elements (identical for all datasets)
    with open(default_file, 'r') as file:
        default = yaml.load(file.read(), Loader=yaml.SafeLoader)

    # Working individually on each ODA dataset
    for dataset in st_data:
        logger.info('Working on dataset %s' % dataset['Metadata_identifier'])
        logger.debug(dataset)

        # Add station elements
        # todo: Temporary? Is it ok to use station data not coming from ODA tag?
        dataset['station_name'] = station_name
        dataset['station_id'] = station_id

        # Modify elements to fit MMD template format
        # Merge dataset elements with default elements
        out_elements = prepare_elements(dataset, default)

        # Perform MMD transformation
        outfile = pathlib.Path(outdir, 'oda_' + str(dataset['Metadata_identifier']) + '.xml')
        to_mmd(out_elements, outfile, mmd_template, validate, mmd_schema)

    return True


def prepare_elements(dataset_elements, default_elements):
    """
    Prepare a dictionary to fit MMD schema:
     - merge dataset specific elements and default elements (default overwritten if available in dataset)
     - rename elements
     - modify to fit controlled vocabularies
     - verify that elements are 'OK' (fit controlled vocabularies, required are present, ...)
    Args:
        dataset_elements (dict): dictionary containing all elements specific to one dataset
        default_elements (dict): dictionary containing all default elements
    Returns:
        dictionary if function succeeded or None if it failed
   """

    logger.debug("Dataset metadata elements before merging: %s" % dataset_elements)

    # Rename elements keys to lowercase
    dataset_elements = _lowercase(dataset_elements)

    # Remove redundant elements
    dataset_elements.pop('collection', None)

    # Remove lat/lon elements if missing
    if dataset_elements['geographic_extent']['latitude_max'] == 0. and \
            dataset_elements['geographic_extent']['latitude_min'] == 0. and \
            dataset_elements['geographic_extent']['longitude_max'] == 0. and \
            dataset_elements['geographic_extent']['longitude_min'] == 0.:
        dataset_elements.pop('geographic_extent', None)

    # Extract CF keyword names
    # The list should contain only one element
    # todo: throw error if more than one CF name
    for keys in dataset_elements['keyword']:
        if keys['Keyword_type'] == "CF name":
            dataset_elements['keywords_cf'] = keys['Keywords'][0]
        else:
            logger.warning(
                'This type of keyword is not available yet (%s). It will not be included in the output MMD.' % keys[
                    'Keyword_type'])

    # Check that dataset elements contains all the required elements
    required_keys = ['keywords_cf', 'metadata_identifier', 'last_metadata_update', 'temporal_extent']
    for req in required_keys:
        if req not in dataset_elements:
            logger.warning('Required parameter missing (%s), creation of MMD file aborted.' % req)
            return None
    if 'start_date' not in dataset_elements['temporal_extent']:
        logger.warning('Required parameter missing (\'temporal_extent\'][\'start_date\']), creation of MMD file '
                       'aborted.')
        return None

    # Merge default and dataset specific elements
    # (default is overwritten if it's also defined at dataset level)
    elements_out = copy.deepcopy(default_elements)
    _merge_dicts(elements_out, dataset_elements)

    # Rename elements to follow mmd vocabulary for data production status
    choices = {'open': 'In Work', 'future': 'Planned', 'closed': 'Complete'}
    elements_out['dataset_production_status'] = choices.get(elements_out['production_status'], None)
    if elements_out['dataset_production_status'] is None:
        logger.warning(
            'The value for key %s (%s) is not a valid choice. Correct choices are: open/future/closed. This element '
            'is required, so the creation of MMD file is aborted.' % (
                'production_status', elements_out['production_status']))
        return None

    # Remove operational status if empty
    if elements_out['operational_status'] == '':
        elements_out.pop('operational_status')
    else:
        elements_out['operational_status'] = elements_out['operational_status'].title()

    # Remove end date for ongoing data
    elements_out['temporal_extent'].pop('end_date', None)

    # Create dataset specific title and abstract if possible
    try:
        elements_out['title_full'] = elements_out['keywords_cf'] + ' observations from weather station ' + \
                                     elements_out['station_name'] + ' (station ID ' + elements_out['station_id'] + ').'
        elements_out['abstract_full'] = 'Timeseries of ' + elements_out[
            'keywords_cf'] + ' observations from the Norwegian weather station ' + elements_out[
                                            'station_name'] + ' (station ID ' + elements_out[
                                            'station_id'] + '). The observations have been through the data ' \
                                                            'collection system of the Norwegian Meteorological ' \
                                                            'institute which includes a number of automated and ' \
                                                            'manual quality control routines. The number of available '\
                                                            'quality control routines is element dependent. '
    except KeyError:
        elements_out['title_full'] = elements_out['title']
        elements_out['abstract_full'] = elements_out['abstract']

    logger.debug("Metadata elements after merging: %s" % dataset_elements)

    return elements_out


def to_mmd(input_data, output_file, template_file, xsd_validation=False, xsd_schema=None):
    """
    Transform Json file or dictionary to MMD using a template.
    Args:
        input_data (str or dict): filepath to input json file or dictionary
        output_file (str): filepath to output MMD file
        template_file (str): filepath to a xml template file
        xsd_validation (bool): if true, performs validation on the created xml file - requires an xsd schema
                               default=False
        xsd_schema (str): filepath to xsd schema file
                          default=None
    Returns:
        True if function succeeded, False otherwise
    """
    # Input data can be
    # a Jason file
    if isinstance(input_data, str) and pathlib.Path(input_data).is_file():
        with open(input_data, 'r') as file:
            in_doc = json.load(file)
    # or a dictionary
    elif isinstance(input_data, dict):
        in_doc = input_data
    else:
        raise TypeError("Unknown input data %s. Expecting a Jason file or a dictionary." % input_data)

    # Rendering of input in template
    if not pathlib.Path(template_file).is_file():
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), template_file)
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(pathlib.Path(template_file).parent))
    template = env.get_template(pathlib.Path(template_file).name)
    out_doc = template.render(data=in_doc)

    # Creation of output XML file
    pathlib.Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    if pathlib.Path(output_file).is_file:
        logger.warning('Overwriting previous version of output MMD file.')
    pathlib.Path(output_file).write_text(out_doc)
    logger.info("MMD file written to %s " % output_file)

    # Optional validation of output XML file
    if xsd_validation:
        if xsd_schema is None:
            raise TypeError
        if not pathlib.Path(xsd_schema).is_file():
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), xsd_schema)
        else:
            if not xsd_check(output_file, xsd_schema=xsd_schema):
                return False

    return True


def _lowercase(dictin):
    """
    Make all keys from a dictionary lowercase.
    Args:
        dictin (dict): dictionary
    Returns:
        modified dictionary dictin
    Ok for nested dictionaries, but will not work for dictionaries within lists.

    >>> _lowercase({'Toto': 1, 'tata': 'Tata', 'List': [{'MyKey': 'Hello'}]})
    {'toto': 1, 'tata': 'Tata', 'list': [{'MyKey': 'Hello'}]}

    """
    if isinstance(dictin, dict):
        return {k.lower(): _lowercase(v) for k, v in dictin.items()}
    else:
        return dictin


def _merge_dicts(d1, d2):
    """
    Merge dictionaries d1 and d2 with values from d1 overwritten by d2 if exists in both dictionaries.
    Merging includes nested dictionaries.
    Raises error if one key contains a dictionary in one dictionary but not in the other.
    Args:
        d1 (dict): default dictionary
        d2(dict): other dictionary
    Returns:
        True if function succeeded, False otherwise
        Dictionary d1 will now contain the merged dictionary

    >>> d1 = {'A': 1, 'B': 2}
    >>> d2 = {'A': 3, 'C':4}
    >>> _merge_dicts(d1, d2)
    True
    >>> print(d1)
    {'A': 3, 'B': 2, 'C': 4}

    """
    out = d1
    for k in d2:
        if k in out:
            if isinstance(out[k], dict) and isinstance(d2[k], dict):
                _merge_dicts(out[k], d2[k])
            elif (isinstance(out[k], dict) and not isinstance(d2[k], dict)) or (
                    not isinstance(out[k], dict) and isinstance(d2[k], dict)):
                raise TypeError
            else:
                out[k] = d2[k]
        else:
            out[k] = d2[k]
    return True
