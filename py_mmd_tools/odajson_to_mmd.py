"""
Tool for creating metadata (MMD format) for data from ODA database.

License:
     This file is part of the py-mmd-tools repository (https://github.com/metno/py-mmd-tools).
     py-mmd-tools is licensed under GPL-3.0 (https://github.com/metno/py-mmd-tools/blob/master/LICENSE)
"""

import pathlib
import lxml.etree as ET
import sys
import logging
import json
import yaml
import jinja2
import copy
import requests    
import logging
import os

# Initiate logger
logger = logging.getLogger(__name__)


def get_from_frost(point, user_id=None, user_pwd='', timeout_secs=30):
    """ Request from URL. """

    r = requests.get(point, auth=(user_id,user_pwd), timeout=timeout_secs)
    if r.status_code == 200:
        logger.debug('Data retrieved OK.')
    else:
        logger.error('Error while trying to get all elements from end point %s \n Returned status code %s \n Message: %s \n Reason: %s' % 
                (point, r.status_code, r.json()['error']['message'], r.json()['error']['reason']))
    return r


def process_all(default_elements, mmd_template, outdir, mmd_schema, validate, frost_url='frost-staging.met.no'):
    """ Process all datasets available from FROST API. """
    
    # Get list of available stations
    # For now, request frost.met.no instead of frost_url as this service is not available on the staging API
    stations_req = get_from_frost('https://frost.met.no/sources/v0.jsonld', os.getenv('FROST_ID'))
    try:
        stations_list = stations_req.json()['data']  
    except (KeyError, TypeError):
        logger.error('Problem with stations request: %s' % stations_req)
        return False 

    # for test only
    stations_list = stations_list[0:10]

    # Looping over available stations
    for station in stations_list:

        st_id = station['id'][2:]
        st_url = 'https://' + frost_url + '/api/v1/availableoda?stationid=' + st_id
        logger.debug('Retrieving FROST data for station %s (id: %s).' %(station['name'], st_id))

        # Request ODA tags for all datasets of current station
        st_req = get_from_frost(st_url)

        # Filter out stations with no tag
        try:
            st_data = st_req.json()
        except json.decoder.JSONDecodeError:
            logger.info('No metadata available for station %s (id %s).' %(station['name'], st_id))
            logger.debug(st_req.text)
            continue

        logger.debug('%s datasets for station %s (id %s).' %(len(st_data), station['name'], st_id))

        # Working individually on each ODA dataset
        for dataset in st_data:

            logger.debug('Working on dataset %s' % dataset['Metadata_identifier'])

            logger.debug(dataset)

            # Add station elements
            # Temporary? Is it ok to use station data not coming from ODA tag?
            dataset['station_name'] = station['name'] 
            dataset['station_id'] = station['id'] 

            outfile = pathlib.Path(outdir, 'oda_' + str(dataset['Metadata_identifier']) + '.xml')
            process_dataset(dataset, default_elements, mmd_template, mmd_schema, validate, outfile)


def process_file(infile, default_elements, mmd_template, outdir, mmd_schema, validate):
    """ Process one dataset, ie one Json file containing metadata for one dataset. """

    # Read ODA dataset metadata
    with open(infile, 'r') as file:
        dataset_elements = json.load(file)
    
    # Create output file name
    outfile = pathlib.Path(outdir, infile.stem + '.xml')
    
    # Process data
    process_dataset(dataset_elements, default_elements, mmd_template, mmd_schema, validate, outfile)


def process_dataset(dataset, default, template, schema, validate, outfile):
    """ Fully process one dataset: convert to mmd, validate, write to file."""

    # Create mmd
    xml_out = to_mmd(dataset, default, template)
    if xml_out is None:
        return False

    # Validate against schema
    if validate:
        check_mmd(xml_out, schema)

    # Write to file
    write_mmd(xml_out, outfile)

    return True


def to_mmd(dataset_elements, default_elements, mmd_template):
    """ Fill MMD template for one dataset using default elements, station elements and time-series elements."""

    # Transforming time-series metadata keys to lower case
    elements_out = _lowercase(dataset_elements) 

    # Merge default and dataset specific elements 
    # default is overwritten if it's also defined at dataset level
    _merge_dicts(elements_out, dataset_elements)

    # Geographical extent: 
    # provided as dictionary describing latitude and longitude
    # create an element describing geographical extent as rectangle with identical north/south and east/west
    try:
        elements_out['rectangle'] = {
                'north': elements_out['geographic_extent']['latitude'],
                'south': elements_out['geographic_extent']['latitude'],
                'west':  elements_out['geographic_extent']['longitude'],
                'east':  elements_out['geographic_extent']['longitude'],
                }
    # Check if it catches the data with missing lat-lon
    except KeyError:
        elements_out['rectangle'] = {
                'north': elements_out['geographic_extent']['latitude_max'],
                'south': elements_out['geographic_extent']['latitude_min'],
                'west':  elements_out['geographic_extent']['longitude_min'],
                'east':  elements_out['geographic_extent']['longitude_max'],
                }


    del elements_out['geographic_extent']

    # Rename elements to follow mmd vocabulary
    for keys in elements_out['keyword']:
        if keys['Keyword_type'] == "CF name":
            elements_out['keywords_cf'] = keys['Keywords']
        else:
            logging.warning('This type of keyword is not available yet (%s). It will not be included in the output MMD.' % keys['keyword_type'])

    if not 'keywords_cf' in elements_out:
        logging.warning('Required parameter missing (\'keyword\'), creation of MMD file aborted.')
        return None

    # Controlled vocabularies choices
    # -for data production status
    try:
        choices = {'open': 'In Work', 'future': 'Planned','closed': 'Complete'}
        elements_out['data_production_status'] = choices.get(elements_out['production_status'])
    except KeyError:
        raise KeyError('The value for key %s (%s) is not a valid choice. Correct choices are: open/future/closed' %('production_status', elements_out['production_status']))

    # Remove end date for ongoing data
    elements_out['temporal_extent'].pop('end_date', None)

    elements_out['operational_status'] = elements_out['operational_status'].title()

    # Fill template with fully updated dataset elements
    mmd_out = mmd_template.render(data=elements_out)
    
    return mmd_out


def write_mmd(mmd, outfile):
    """ Write MMD-like XML string to file."""

    # Create output directory
    outfile.parent.mkdir(parents=True, exist_ok=True)
   
    if outfile.is_file:
        logger.warning('Overwriting previous version of output MMD file.')

    outfile.write_text(mmd)

    logger.info("MMD file written to %s " % outfile)


def check_mmd(xml, mmd):
    """ Check XML string against MMD schema."""

    # Read mmd-schema
    xmlschema_mmd = ET.XMLSchema(ET.parse(mmd))

    # Validate and log outputs
    if not xmlschema_mmd.validate(ET.fromstring(xml)):
        logger.warn("MMD document not validated.")
        logger.debug(xmlschema_mmd.error_log)
    else:
        logger.info("MMD document validated.")


def _lowercase(obj):
    """ Make all keys from a dictionary lowercase 
    (ok for nested dictionaries, but will not work for dictionaries within lists) """
    if isinstance(obj, dict):
        return {k.lower():_lowercase(v) for k, v in obj.items()}
    else:
        return obj


def _merge_dicts(d1, d2):
    """
    Merge dictionaries d1 and d2 with values from d1 overwritten by d2 if exists in both dictionaries.
    Merging includes nested dictionaries.
    Dictionnary d1 will contain the merged dictionary.
    Raises error if one key contains a dict in one dict but no in the other.
    """
    out = d1
    for k in d2:
        if k in out:
            if isinstance(out[k], dict) and isinstance(d2[k], dict):
                _merge_dicts(out[k], d2[k])
            elif (isinstance(out[k], dict) and not isinstance(d2[k], dict)) or (not isinstance(out[k], dict) and isinstance(d2[k], dict)):
                raise TypeError
            else:
                out[k] = d2[k]
        else:
            out[k] = d2[k]
    return True


def main(input_data, outdir, oda_default, oda_mmd_template, validate, mmd_schema):

    # Read static metadata elements (identical for all ODA datasets)
    with open(oda_default, 'r') as file:
        default_elements = yaml.load(file.read(), Loader=yaml.SafeLoader)

    # Read ODA MMD template
    try:
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(oda_mmd_template.parent)) 
        mmd_template = env.get_template(oda_mmd_template.name)
    except jinja2.exceptions.TemplateNotFound:
        raise FileNotFoundError(oda_mmd_template)

    # Process all available datasets from FROST API
    if str(input_data) == 'FROST':
        logger.info('Processing all data from %s' %input)
        process_all(default_elements, mmd_template, outdir, mmd_schema, validate)

    # Processing a single Json file representing one dataset
    else:
        logger.info('Processing file %s' %input_data)
        process_file(input_data, default_elements, mmd_template, outdir, mmd_schema, validate)




