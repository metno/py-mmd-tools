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
import os
import xmltodict
import py_mmd_tools
from pkg_resources import resource_string


class Mmd_to_nc(object):

    def __init__(self, mmd_product, nc_file):
        """Class for updating a NetCDF file that is compliant with the CF-conventions and ACDD
        from an MMD XML file.
        Args:
            mmd_product (str): Input MMD xml file.
            nc_file (pathlib): Nc file to update.
        """
        super(Mmd_to_nc, self).__init__()

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
        return

    @staticmethod
    def get_acdd(t):
        """
        Get acdd or acdd_ext value from a dictionary.
        """
        if 'acdd' in t:
            out = t['acdd']
        elif 'acdd_ext' in t:
            out = t['acdd_ext']
        else:
            out = None
        try:
            sep = t['separator']
        except KeyError:
            sep = None
        return out, sep

    @staticmethod
    def process_elem(elem, elem_info, tag):
        out = {}
        sep = None
        if not elem_info[tag] is None:
            acdd_name, sep = Mmd_to_nc.get_acdd(elem_info[tag])
            if acdd_name is not None:
                if isinstance(acdd_name, list):
                    if tag == 'metadata_identifier':
                        out['id'] = elem.text.split(':')[1]
                        out['naming_authority'] = elem.text.split(':')[0]
                    else:
                        ### Default = take the first possible name?
                        ##acdd_name = acdd_name[0]
                        ##out[acdd_name] = elem.text
                        print('Special case not implemented')
                        print(f'{elem.tag} - {elem.text}')
                else:
                    out[acdd_name] = elem.text
        return out, sep

    @staticmethod
    def update_acdd(dict1, dict2, sep=None):
        # First time = 'initialize' the dictionary
        if len(dict1) == 0:
            return dict2
        # If dict2 is empty, no update
        elif dict2 is None:
            return dict1
        # Main case
        else:
            # Check if key already present in dict1
            for key in dict2:
                if key in dict1:
                    # If so, it must be a list, so we append it
                    try:
                        dict1[key] = sep[key].join([dict1[key], dict2[key]])
                    except TypeError:
                        dict1[key] = sep.join([dict1[key], dict2[key]])
                else:
                    dict1[key] = dict2[key]
        return dict1

    def get_last_metadata_update(self, element):
        """
        todo: Hard coded, but I see no way around that
        """
        # todo: not sure why date_created in acdd is linked to last_metadata_update
        # see  https://wiki.esipfed.org/Attribute_Convention_for_Data_Discovery_1-3
        # The date on which this version of the data was created. (Modification of values implies a
        # new version, hence this would be assigned the date of the most recent values modification.)
        # Metadata changes are not considered when assigning the date_created. The ISO 8601:2004
        # extended date format is recommended, as described in the Attribute Content Guidance section.
        out = {
            'date_metadata_modified': element.find('mmd:update/mmd:datetime', namespaces=self.namespaces).text,
            'date_metadata_modified_type': element.find('mmd:update/mmd:type', namespaces=self.namespaces).text
        }

        sep = {
            'date_metadata_modified': self.mmd_yaml['last_metadata_update']['update']['datetime']['separator'],
            'date_metadata_modified_type': self.mmd_yaml['last_metadata_update']['update']['type']['separator']
        }

        return out, sep

    def get_personnel(self, element):
        """
        todo: Hard coded, but I see no way around that
        """

        out = {}
        sep = {}
        for mmd_field in ['role', 'name', 'email', 'organisation']:
            nc_field = 'contributor_' + mmd_field
            out[nc_field] = element.find(f'mmd:{mmd_field}', namespaces=self.namespaces).text
            sep[nc_field] = self.mmd_yaml['personnel'][mmd_field]['separator']
        return out, sep

    def get_keyword(self, element):
        """
        todo: Hard coded, but I see no way around that
        """

        # todo: add Vocabulary in mmd?
        prefix = element.attrib['vocabulary']
        out = {
            'keywords': ':'.join([prefix, element.find('mmd:keyword', namespaces=self.namespaces).text]),
            'keywords_vocabulary': ':'.join([prefix, element.find('mmd:resource', namespaces=self.namespaces).text])
        }

        sep = {
            'keywords': self.mmd_yaml['keywords']['keyword']['separator'],
            'keywords_vocabulary': self.mmd_yaml['keywords']['vocabulary']['separator']
        }

        return out, sep

    def get_title_abstract(self, element, tag):
        """
        todo: Hard coded, but I see no way around that
        """

        out = {}
        acdd_name, sep = self.get_acdd(self.mmd_yaml[tag][tag])
        # Check element language
        for att in element.attrib:
            if element.attrib[att] == 'no':
                acdd_name = acdd_name + '_no'
            elif element.attrib[att] == 'en':
                out[acdd_name + '_lang'] = 'en'
            else:
                print(f'Case not implemented for language {element.attrib[att]}')
                return None
        out[acdd_name] = element.text
        return out

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
                    match = self.get_title_abstract(elem, tag)
                    acdd = self.update_acdd(acdd, match)

                elif mmd_element == 'keywords':
                    match, sep = self.get_keyword(elem)
                    acdd = self.update_acdd(acdd, match, sep)

                elif mmd_element == 'last_metadata_update':
                    match, sep = self.get_last_metadata_update(elem)
                    acdd = self.update_acdd(acdd, match, sep)

                elif mmd_element == 'personnel':
                    match, sep = self.get_personnel(elem)
                    acdd = self.update_acdd(acdd, match, sep)

                # dataset_citation = repeat of mmd fields already processed elsewhere
                elif mmd_element == 'dataset_citation':
                    continue

                # No subselements
                elif len(list(elem)) == 0:
                    match, sep = self.process_elem(elem, self.mmd_yaml, tag)
                    acdd = self.update_acdd(acdd, match, sep)

                # Subselements processed independently
                else:

                    for subelem in list(elem):

                        subtag = ET.QName(subelem).localname

                        if len(list(subelem)) > 0:
                            for subsubelem in list(subelem):
                                subsubtag = ET.QName(subsubelem).localname
                                if len(list(subsubelem)) > 0:
                                    print('Case not implemented')
                                    print(f"tag {tag} / subtag {tag} / subsubtag {subsubtag}")
                                    continue
                                else:
                                    match, sep = self.process_elem(subsubelem, self.mmd_yaml[tag][subtag], subsubtag)
                                    acdd = self.update_acdd(acdd, match, sep)
                        else:
                            match, sep = self.process_elem(subelem, self.mmd_yaml[tag], subtag)
                            acdd = self.update_acdd(acdd, match, sep)

        # Open netcdf file for reading and appending
        with nc.Dataset(self.nc, 'a') as f:

            # Add all global metadata to netcdf at once
            f.setncatts(acdd)

        return
