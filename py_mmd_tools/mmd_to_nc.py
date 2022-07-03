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
            nc_file (str): Nc file to update.
        """

        # NC file
        self.nc = nc_file
        # MMD file content and namespaces
        tree = ET.parse(mmd_product)
        self.tree = tree
        self.namespaces = tree.getroot().nsmap
        self.namespaces.update({'xml': 'http://www.w3.org/XML/1998/namespace'})
        # Translation file between MMD and ACDD
        self.mmd_yaml = yaml.load(
            resource_string(py_mmd_tools.__name__, 'mmd_elements.yaml'), Loader=yaml.FullLoader
        )
        # Dictionary that will contain all ACDD attributes
        self.acdd_metadata = None
        return

    @staticmethod
    def get_acdd(mmd_field):
        """
        Get corresponding ACDD element name from an MMD name.

        Parameters
        ----------
        mmd_field : dict
            MMD element to translate into ACDD.

        Returns
        -------
        acdd_attrs : list
            List of ACDD attributes that can be used for this MMD
            field.
        comments : list
            One comment for each ACDD attribute. If there is no
            comment for an ACDD attribute, the corresponding list
            item is None.

        """

        acdd_fields = []
        comments = []
        sep = []

        # Check that there is an ACDD translation available
        if 'acdd' in mmd_field:
            for key in mmd_field['acdd'].keys():
                acdd_fields.append(key)
                if 'comment' in mmd_field['acdd'][key].keys():
                    comments.append(mmd_field['acdd'][key]['comment'])
                else:
                    comments.append(None)
                if 'separator' in mmd_field['acdd'][key].keys():
                    sep.append(mmd_field['acdd'][key]['separator'])
                else:
                    sep.append(None)
        else:
            acdd_fields = None
            comments = None
            sep = None

        return acdd_fields, comments, sep

    def process_element(self, xml_element, translations):
        """
        Translate an MMD element to ACDD and append it to the global ACDD dictionary.

        Input
        ====
        xml_element: XML element
        translations: dict
            Contains the MMD to ACDD translations
        """

        # Name of the XML element without namespace
        tag = ET.QName(xml_element).localname

        # Check if name exists in translation dictionary,
        # and that if it exists, it contains information
        if tag in translations and not translations[tag] is None:

            # Corresponding ACDD element name
            acdd_name, comments, sep = Mmd_to_nc.get_acdd(translations[tag])

            # Some MMD elements that are listed in mmd_yaml do not have an ACDD
            # translation, so must check that an ACDD translation has been found
            if acdd_name is not None:
                if len(acdd_name) > 1:
                    raise ValueError('Multiple ACDD or ACCD extension fields provided.'
                            ' Please use another translation function.')
                ## Update the dictionary containing the ACDD elements
                #if type(acdd_name) is dict:
                #    # there are separate comments for the attributes
                #    # which are not needes
                #    acdd_name = list(acdd_name.keys())
                self.update_acdd({acdd_name[0]: xml_element.text}, {acdd_name[0]: sep})

    def update_acdd(self, new_dict, sep=None):
        """
        Update the ACDD dictionary, ie dictionary that holds all the ACDD translations.
        Append the information from new_dict to the ACDD dictionary.

        Input
        ====

        new_dict: dictionary containing a new ACDD translation
        sep: dictionary containing the separator character. Optional. Default is None. If sep is
            defined, it must contain the same keys as new_dict.

        """
        # If self.acdd_metadata is empty, fill it with new_dict
        if self.acdd_metadata is None:
            self.acdd_metadata = new_dict

        # Main case
        else:

            # Loop on new_dict keys
            for key in new_dict:

                # If a key is already present in acdd_metadata,
                # then the content of new_dict[key] must be appended to the already existing
                # content of self.acdd_metadata[key], using the separator from the sep dictionary
                if key in self.acdd_metadata:
                    self.acdd_metadata[key] = sep[key].join([self.acdd_metadata[key],
                                                             new_dict[key]])

                # Otherwise, add a new key to acdd_metadata
                else:
                    self.acdd_metadata[key] = new_dict[key]

    def process_metadata_identifier(self, element):
        """ The metadata_identifier in MMD is translated to two
        fields in ACDD, the 'id' and the 'naming_authority'.
        """
        # Name of the XML element without namespace
        tag = ET.QName(element).localname
        if not tag=='metadata_identifier':
            raise OptionError('Wrong input')
        # Corresponding ACDD element name
        acdd_name, comments, sep = Mmd_to_nc.get_acdd(self.mmd_yaml['metadata_identifier'])
        assert 'id' in acdd_name
        assert 'naming_authority' in acdd_name
        [naming_authority, id] = element.text.split(':')
        self.update_acdd({
            'id': id,
            'naming_authority': naming_authority
        })

    def process_last_metadata_update(self, element):
        """ Special case for MMD element "last_metadata_update".
        This element has two ACDD translations: date_created and
        date_metadata_modified. As the appropriate translation in
        this case is 'date_metadata_modified' only, it has do be done
        via a special case.

        Note: It might be possible to not use a special case for this
        element if the order of acdd translations in mmd_elements.yaml
        was changed.

        Input
        ====
        element: 'last_metadata_update' XML element from MMD. Example:
            <mmd:last_metadata_update>
                <mmd:update>
                    <mmd:datetime>2022-02-18T13:09:44.299926+00:00</mmd:datetime>
                    <mmd:type>Created</mmd:type>
                </mmd:update>
            </mmd:last_metadata_update>

        """

        self.update_acdd({
                'date_metadata_modified': element.find('mmd:update/mmd:datetime',
                    namespaces=self.namespaces).text
            }, {
                'date_metadata_modified': self.mmd_yaml['last_metadata_update']['update']
                         ['datetime']['acdd']['date_metadata_modified']['separator']
            })

    def process_personnel(self, element, separator=','):
        """
        Special case for MMD element "personnel". Since its child elements are related one to
        another, they must to be processed simultaneously.

        Input
        ====
        element: 'personnel' XML element from MMD. Example:
            <mmd:personnel>
              <mmd:role>Principal Investigator</mmd:role>
              <mmd:name>Pepe</mmd:name>
              <mmd:email>pepe@met.no</mmd:email>
            </mmd:personnel>

        separator : str
            Defaults to ',', which is common for all the personnel
            elements.

        """
        assert separator == \
                self.mmd_yaml['personnel']['role']['acdd']['creator_role']['separator']

        out = {}
        sep = {}

        # Personnel child elements from MMD can be translated to creator or contributor in ACDD
        # For example, personnel/role in MMD can be translated to either creator_role or
        # contributor_role in ACDD
        # Only some MMD personnel child elements have an ACDD translation in mmd_elements.yaml,
        # and they are not the same for creator and contributor type,
        # and some are optional while others are required,
        # so build appropriate lists of fields to translate
        if element.find('mmd:role', namespaces=self.namespaces).text == 'Technical contact':
            prefix = 'creator'
            acdd_translation_and_mmd_required_fields = ['role', 'name', 'email']
            acdd_translation_and_mmd_optional_fields = ['organisation']
        else:
            prefix = 'contributor'
            acdd_translation_and_mmd_required_fields = ['role', 'name']
            acdd_translation_and_mmd_optional_fields = []

        # Process the mandatory fields
        for mmd_field in acdd_translation_and_mmd_required_fields:
            nc_field = '_'.join([prefix, mmd_field])
            out[nc_field] = element.find(f'mmd:{mmd_field}', namespaces=self.namespaces).text
            #sep[nc_field] = self.mmd_yaml['personnel'][mmd_field]['acdd']['separator']
            sep[nc_field] = separator

        # Process the optional field, so first check if they are defined in the MMD file
        for mmd_field in acdd_translation_and_mmd_optional_fields:
            field = element.find(f'mmd:{mmd_field}', namespaces=self.namespaces)
            if field is not None:
                nc_field = '_'.join([prefix, mmd_field])
                out[nc_field] = field.text
                #sep[nc_field] = self.mmd_yaml['personnel'][mmd_field]['acdd']['separator']
                sep[nc_field] = separator

        # Update the dictionary containing the ACDD elements
        self.update_acdd(out, sep)

    def process_keywords(self, element):
        """
        Special case for MMD element "keywords". Since its child elements are related to one
        another, they must be processed simultaneously.

        Input
        ====
        element: 'keywords' XML element from MMD. Example:
            <mmd:keywords vocabulary="NORTHEMES">
              <mmd:keyword>Weather and climate</mmd:keyword>
              <mmd:resource>
                https://register.geonorge.no/subregister/metadata-kodelister/kartverket/nasjonal-temainndeling
              </mmd:resource>
              <mmd:separator></mmd:separator>
            </mmd:keywords>

        Corresponding example of ACDD translation:
            keywords = "NORTHEMES:Weather and climate"
            keywords_vocabulary = "NORTHEMES:https://register.geonorge.no/subregister
                                        /metadata-kodelister/kartverket/nasjonal-temainndeling"
        """

        out = {}
        sep = {}

        # Get vocabulary attribute from MMD element
        # It will be used as a prefix for ACDD translations
        prefix = element.attrib['vocabulary']

        # ACDD keywords element
        # Syntax: "prefix:keyword"
        out['keywords'] = ':'.join([prefix, element.find('mmd:keyword',
                                                         namespaces=self.namespaces).text])
        for key in self.mmd_yaml['keywords']['keyword']['acdd'].keys():
            sep['keywords'] = self.mmd_yaml['keywords']['keyword']['acdd'][key]['separator']

        # ACDD keywords_vocabulary element
        # Syntax: "prefix:uri"
        # URI is only optional in MMD, so check if it is defined before translation
        found = element.find('mmd:resource', namespaces=self.namespaces)
        if found is not None:
            out['keywords_vocabulary'] = ':'.join([prefix, found.text])
            for key in self.mmd_yaml['keywords']['vocabulary']['acdd'].keys():
                sep['keywords_vocabulary'] = \
                        self.mmd_yaml['keywords']['vocabulary']['acdd'][key]['separator']

        # Update ACDD dictionary
        self.update_acdd(out, sep)

    def process_citation(self, element):
        """
        Special case for MMD element "dataset_citation",
        as only some of its child elements need to be translated to acdd.
        Only translate fields that have not already been translated to acdd before.
        List of ACDD elements that have a translation from child elements of dataset_citation
        element (in mmd_elements.yaml):
        - creator_name -> already translated from personnel / PI (required in mmd)
        - date_created -> in acdd relates to the data, not the metadata, so already in nc file
        - title -> already translated from title (required in mmd)
        - publisher_name -> needs to be translated here (from publisher child element)
        - metadata_link -> needs to be translated here (from url child element)
        - references -> needs to be translated here (from other child element)

        Input
        ====
        element: 'dataset_citaton' XML element from MMD. Example:
            <mmd:dataset_citation>
                <mmd:author>Jane Doe</mmd:author>
                <mmd:publication_date>2022-02-18T13:09:44.201246+00:00</mmd:publication_date>
                <mmd:title>My dataset</mmd:title>
                <mmd:publisher>John Doe</mmd:publisher>
            </mmd:dataset_citation>
        """
        for child in ['publisher', 'url', 'other']:
            found = element.find(f'mmd:{child}', namespaces=self.namespaces)
            if found is not None:
                self.update_acdd({
                    list(self.mmd_yaml['dataset_citation'][child]['acdd'].keys())[0]: found.text
                })

    def process_title_and_abstract(self, element):
        """
        Special case for MMD elements "title" and "abstract". Both elements have repetitions
        allowed in MMD, with different language each time. For ACDD, only the English language
        title and abstracts are extracted.

        Input
        ====
        element: 'title' or 'abstract' XML element from MMD. Example:
          <mmd:title xml:lang="en">This is my dataset.</mmd:title>
        """

        # Local name of element ('title' or 'abstract'),
        # ie MMD element name without namespace
        tag = ET.QName(element).localname

        # Get ACDD name corresponding to MMD element name
        acdd_name, comments, sep = self.get_acdd(self.mmd_yaml[tag][tag])

        # Keep only title and abstract with attribute 'en' (english language)
        if element.attrib["{%s}" % self.namespaces['xml'] + 'lang'] == 'en':
            self.update_acdd({acdd_name[0]: element.text})

    def update_nc(self):
        """
        Update a netcdf file global attributes.
        """

        # Loop on elements from mmd_yaml
        for mmd_element in self.mmd_yaml:

            # Find corresponding XML element in the MMD file
            elements = self.tree.findall('mmd:' + mmd_element, self.namespaces)

            # Not all elements on mmd_yaml are required MMD elements,
            # So, if element is not found in the MMD file, continue
            if len(elements) == 0:
                print(f'{mmd_element} not found in input MMD file')
                continue

            # Loop the elements found in the MMD file (some MMD
            # elements have repetition allowed)
            for element in elements:

                # Special case for metadata_identifier
                if mmd_element == 'metadata_identifier':
                    self.process_metadata_identifier(element)

                # Special case for MMD elements "title" and "abstract"
                elif mmd_element in ['title', 'abstract']:
                    self.process_title_and_abstract(element)

                # Special case for keywords element
                elif mmd_element == 'keywords':
                    self.process_keywords(element)

                # Special case for MMD element "last_metadata_update"
                elif mmd_element == 'last_metadata_update':
                    self.process_last_metadata_update(element)

                # Special case for MMD element 'personnel' and its child elements
                elif mmd_element == 'personnel':
                    self.process_personnel(element)

                # If XML element found has no child elements, process it directly
                elif len(list(element)) == 0:
                    self.process_element(element, self.mmd_yaml)

                # Special case for MMD element "dataset_citation"
                # Processed last as its translation depends on other MMD elements processed
                # previously
                elif mmd_element == 'dataset_citation':
                    self.process_citation(element)

                # Last case: the XML element has child elements
                else:

                    # Name of the parent element without namespace
                    parent_name = ET.QName(element).localname
                    # Extract of mmd_yaml for this element and its children
                    mmd_yaml_extract = self.mmd_yaml[parent_name]

                    # Loop on child elements
                    for child_element in list(element):

                        # If child element has children elements also
                        if len(list(child_element)) > 0:

                            # Extract of mmd_yaml_extract for this child element and its children
                            child_name = ET.QName(child_element).localname
                            mmd_yaml_extract_extract = mmd_yaml_extract[child_name]

                            for grandchild_element in list(child_element):
                                self.process_element(grandchild_element, mmd_yaml_extract_extract)

                        # If child element has no children elements
                        else:
                            self.process_element(child_element, mmd_yaml_extract)

        # Open netcdf file for reading and appending
        with nc.Dataset(self.nc, 'a') as f:

            # Append global attribute Conventions
            self.acdd_metadata['Conventions'] = f.Conventions + ', ' + self.ACDD

            # Check that there is no conflict between ACDD global attributes created from MMD
            # and global attributes already set in netcdf file. Only new global attributes are
            # allowed, except for Conventions.
            for key in self.acdd_metadata:
                if key in f.ncattrs() and key != 'Conventions':
                    raise Exception("%s is already a global attribute" % key)

            # Add all global metadata to netcdf at once
            f.setncatts(self.acdd_metadata)

        return
