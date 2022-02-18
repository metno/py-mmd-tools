#!/usr/bin/env python3
"""
Tool for parsing an XML metadata file, following the MET Norway Metadata specification (MMD),
 and updating an NetCDF file, following the Attribute Convention for Data Discovery (ACDD).

License:

This file is part of the py-mmd-tools repository
<https://github.com/metno/py-mmd-tools>.

py-mmd-tools is licensed under the Apache License 2.0
<https://github.com/metno/py-mmd-tools/blob/master/LICENSE>
"""

import yaml
import netCDF4 as nc
import lxml.etree as ET
import py_mmd_tools
from pkg_resources import resource_string


class Mmd_to_nc(object):
    # ACDD version
    ACDD = 'ACDD-1.3'

    def __init__(self, mmd_product, nc_file):
        """Class for updating a NetCDF file that is compliant with the CF-conventions and ACDD
        from an MMD XML file.
        Args:
            mmd_product (str): Input MMD xml file.
            nc_file (pathlib): Nc file to update.
        """

        # NC file
        self.nc = nc_file

        # MMD file content / namespaces
        tree = ET.parse(mmd_product)
        self.tree = tree
        self.namespaces = tree.getroot().nsmap

        # Get translation file between MMD and ACDD
        self.mmd_yaml = yaml.load(
            resource_string(py_mmd_tools.__name__, 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        self.acdd_metadata = None
        return

    @staticmethod
    def get_acdd(mmd_field, ind=0):
        """
        Get acdd or acdd_ext value from an MMD name.
        
        Input
        ====
        mmd_field: dict
            MMD element to translate into ACDD 
        ind : int (default 0)
            Index of list element to use if the value of an ACDD attribute is a list
        """
        if 'acdd' in mmd_field:
            if type(mmd_field['acdd']) is list:
                out = mmd_field['acdd'][
                    ind]  # always take the first - this  must be tested to ensure that we get what we want
            else:
                out = mmd_field['acdd']
        else:
            out = None
        try:
            sep = mmd_field['separator']
        except KeyError:
            sep = None
        return out, sep

    @staticmethod
    def process_elem(elem, elem_info, tag):
        out = None
        sep = None
        if not elem_info[tag] is None:
            acdd_name, sep = Mmd_to_nc.get_acdd(elem_info[tag])
            if acdd_name is not None:
                out = {acdd_name: elem.text}
        return out, sep

    def update_acdd(self, dict2, sep=None):
        # First time = 'initialize' the dictionary
        if self.acdd_metadata is None:
            self.acdd_metadata = dict2
        # Main case
        else:
            # Check if key already present in dict1
            for key in dict2:
                if key in self.acdd_metadata:
                    # If so, it must be a list, so we append it
                    if type(sep) is dict:
                        self.acdd_metadata[key] = sep[key].join(
                            [self.acdd_metadata[key], dict2[key]])
                    else:
                        self.acdd_metadata[key] = sep.join([self.acdd_metadata[key], dict2[key]])
                else:
                    self.acdd_metadata[key] = dict2[key]

    def get_last_metadata_update(self, element):
        """
        """
        out = {
            'date_metadata_modified': element.find('mmd:update/mmd:datetime',
                                                   namespaces=self.namespaces).text,
            'date_metadata_modified_type': element.find('mmd:update/mmd:type',
                                                        namespaces=self.namespaces).text
        }

        sep = {
            'date_metadata_modified': self.mmd_yaml['last_metadata_update']['update']['datetime']
            ['separator'],
            'date_metadata_modified_type': self.mmd_yaml['last_metadata_update']['update']['type']
            ['separator']
        }

        return out, sep

    def get_personnel(self, element):
        """
        """

        out = {}
        sep = {}
        if element.find('mmd:role', namespaces=self.namespaces).text == 'Technical contact':
            prefix = 'creator'
        else:
            prefix = 'contributor'

        for mmd_field in ['role', 'name', 'email', 'organisation']:
            nc_field = '_'.join([prefix, mmd_field])
            out[nc_field] = element.find(f'mmd:{mmd_field}', namespaces=self.namespaces).text
            sep[nc_field] = self.mmd_yaml['personnel'][mmd_field]['separator']
        return out, sep

    def get_keyword(self, element):
        """
        """

        out = {}
        sep = {}
        prefix = element.attrib['vocabulary']
        out['keywords'] = ':'.join([prefix, element.find('mmd:keyword',
                                                         namespaces=self.namespaces).text])
        sep['keywords'] = self.mmd_yaml['keywords']['keyword']['separator']
        try:
            out['keywords_vocabulary'] = ':'.join([prefix, element.find(
                'mmd:resource', namespaces=self.namespaces).text])
            sep['keywords_vocabulary'] = self.mmd_yaml['keywords']['vocabulary']['separator']
        except AttributeError:
            print('No resource for keyword')

        return out, sep

    def get_title_and_abstract(self, element, tag):
        """
        """

        acdd_name, sep = self.get_acdd(self.mmd_yaml[tag][tag])
        # Keep only title and abstract with attribute 'en' (english language)
        for att in element.attrib:
            if element.attrib[att] == 'en':
                return {acdd_name: element.text}

    def update_nc(self):
        """
        Update a netcdf file global attributes.
        """

        acdd = {}

        # Loop on expected MMD elements
        # ie from mmd_elements.yaml = kind-off mapping between acdd and mmd
        for mmd_element in self.mmd_yaml:

            elements = self.tree.findall('mmd:' + mmd_element, self.namespaces)

            if len(elements) == 0:
                print(f'{mmd_element} not found in input MMD file')
                continue

            # Loop on  MMD elements found
            for elem in elements:

                tag = ET.QName(elem).localname

                if mmd_element in ['title', 'abstract']:
                    match = self.get_title_and_abstract(elem, tag)
                    if match is not None:
                        self.update_acdd(match)

                elif mmd_element == 'keywords':
                    match, sep = self.get_keyword(elem)
                    self.update_acdd(match, sep)

                elif mmd_element == 'last_metadata_update':
                    match, sep = self.get_last_metadata_update(elem)
                    self.update_acdd(match, sep)

                elif mmd_element == 'personnel':
                    match, sep = self.get_personnel(elem)
                    self.update_acdd(match, sep)

                # No subselements
                elif len(list(elem)) == 0:
                    match, sep = self.process_elem(elem, self.mmd_yaml, tag)
                    if match is not None:
                        self.update_acdd(match, sep)

                # dataset_citation = repeat of mmd fields already processed elsewhere
                # -----
                # Only pickup fields that have not already been translated to acdd before
                # is mmd ordered?
                # - creator_name -> if there is an entry with role = technical contact in mmd, it's already done,
                # otherwise, needs to be translated
                # - date_created -> in acdd relates to the data, not the metadata, so already in nc file
                # - title is compulsory in mmd -> so must have been already translated
                # - publisher_name -> needs to be translated here
                # - metadata_link -> needs to be translated here
                # - references -> attribute is defined in the CF conventions, so already in nc file

                elif mmd_element == 'dataset_citation':
                    continue

                # Subselements processed independently
                else:

                    for subelem in list(elem):

                        subtag = ET.QName(subelem).localname

                        if len(list(subelem)) > 0:
                            for subsubelem in list(subelem):
                                subsubtag = ET.QName(subsubelem).localname
                                match, sep = self.process_elem(subsubelem,
                                                               self.mmd_yaml[tag][subtag],
                                                               subsubtag)
                                if match is not None:
                                    self.update_acdd(match, sep)
                        else:
                            match, sep = self.process_elem(subelem, self.mmd_yaml[tag], subtag)
                            if match is not None:
                                self.update_acdd(match, sep)

        # Open netcdf file for reading and appending
        with nc.Dataset(self.nc, 'a') as f:

            # Conventions
            self.acdd_metadata['Conventions'] = f.Conventions + ', ' + self.ACDD

            # Add all global metadata to netcdf at once
            for key in self.acdd_metadata.keys():
                if key in f.ncattrs() and key != 'Conventions':  # optionally add more attrs
                    raise Exception("%s is already a global attribute" % key)
            f.setncatts(self.acdd_metadata)

        return
