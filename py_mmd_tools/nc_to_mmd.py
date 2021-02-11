"""
Tool for parsing metadata following the Attribute Convention for Data Discovery (ACDD)
in NetCDF files to the MET Norway Metadata format specification (MMD).

Can also be used check to check whether the required MMD elements are present in input file.

License:
     This file is part of the py-mmd-tools repository (https://github.com/metno/py-mmd-tools).
     py-mmd-tools is licensed under the Apache License 2.0 (
     https://github.com/metno/py-mmd-tools/blob/master/LICENSE)
"""

import warnings
import yaml
import jinja2

from pkg_resources import resource_string
from dateutil.parser import parse
from dateutil.parser._parser import ParserError

import pathlib
from netCDF4 import Dataset
import lxml.etree as ET

class Nc_to_mmd(object):

    def __init__(self, netcdf_product, output_file=None, check_only=False):
        """
        Class for creating an MMD XML file based on the discovery metadata provided in the global attributes of NetCDF
        files that are compliant with the CF-conventions and ACDD.

        Args:
            output_file (pathlib): Output path for mmd.
            netcdf_product (str: nc file or OPeNDAP url): input NetCDF file.

        """
        super(Nc_to_mmd, self).__init__()
        self.output_file = output_file
        self.netcdf_product = netcdf_product
        self.check_only = check_only
        self.missing_attributes = {
                    'errors': [],
                    'warnings': []
                }

    def separate_repeated(self, repetition_allowed, acdd_attr, separator=','):
        if repetition_allowed:
            acdd_attr = [ss.strip() for ss in acdd_attr.split(separator)]
        return acdd_attr

    def get_acdd_metadata(self, mmd_element, ncin):
        """ Recursive function to trenslate from ACDD to MMD.

        If ACDD does not exist for a given MMD element, the function looks 
        for an alternative acdd_ext element instead. It may also use a default 
        value as specified in mmd_elements.yaml. Repetition is handled by 
        treating the acdd element as a comma separated list.
        """
        # TODO: clean up and refactor to get rid of all the ifs...?

        required = mmd_element.pop('minOccurs','') == '1'
        acdd = mmd_element.pop('acdd', '')
        acdd_ext = mmd_element.pop('acdd_ext', '')
        default = mmd_element.pop('default', '')
        repetition_allowed = mmd_element.pop('maxOccurs', '') not in ['', '0', '1']
        separator = mmd_element.pop('separator',',')
        
        data = []
        if not acdd:
            if len(mmd_element.items()) == 0:
                if acdd_ext and acdd_ext in ncin.ncattrs():
                    data = self.separate_repeated(repetition_allowed, 
                            eval('ncin.%s' %acdd_ext), separator)
                elif default:
                    data = default
                elif not required:
                    if repetition_allowed:
                        return []
                    else:
                        return None
            else:
                data = {}
                for key, val in mmd_element.items():
                    if val:
                        data[key] = self.get_acdd_metadata(val, ncin)
        else:
            if acdd in ncin.ncattrs():
                data = self.separate_repeated(repetition_allowed, eval('ncin.%s' %acdd), separator)
            elif required:
                if default:
                    # We allow some missing elements (in particular for datasets from outside MET)
                    data = default
                    self.missing_attributes['warnings'].append('%s is a required ACDD attribute' %acdd)
                else:
                    self.missing_attributes['errors'].append('%s is a required ACDD attribute' %acdd)
                    return 
            else:
                return

        return data

    def get_data_centers(self, mmd_element, ncin):
        acdd_short_name = mmd_element['data_center_name']['short_name'].pop('acdd')
        short_names = self.separate_repeated(True, eval('ncin.%s' %acdd_short_name))
        acdd_long_name = mmd_element['data_center_name']['long_name'].pop('acdd')
        long_names = self.separate_repeated(True, eval('ncin.%s' %acdd_long_name))
        acdd_url = mmd_element['data_center_url'].pop('acdd')
        try:
            urls = self.separate_repeated(True, eval('ncin.%s' %acdd_url))
        except AttributeError:
            urls = ''
        data = []
        for i in range(len(short_names)):
            if len(urls)<=i:
                url = ''
            else:
                url = urls[i]
            data.append({
                'data_center_name': {
                    'short_name': short_names[i],
                    'long_name': long_names[i],
                    },
                'data_center_url': url,
                })
        return data

    def get_metadata_updates(self, mmd_element, ncin):
        acdd_time = mmd_element['update']['datetime'].pop('acdd', '')
        times = []
        for field_name in acdd_time:
            if field_name in ncin.ncattrs():
                times = self.separate_repeated(True, eval('ncin.%s' %field_name))
                break
        if not times:
            self.missing_attributes['errors'].append('ACDD attribute %s or %s is required' %(acdd_time[0], acdd_time[1]))
            return

        acdd_type = mmd_element['update']['type'].pop('acdd', '')
        # acdd is not added to the type field in mmd_elements.yaml..
        #if acdd_type:
        #    types = self.separate_repeated(True, eval('ncin.%s' %acdd_type))
        #else:
        types =  [mmd_element['update']['type'].pop('default', '') for i in range(len(times))]
        data = {}
        data['update'] = []
        for i in range(len(times)):
            data['update'].append({'datetime': times[i], 'type': types[i]}) 
        return data

    def get_titles(self, mmd_element, ncin):
        acdd = mmd_element['title'].pop('acdd')
        separator = mmd_element.pop('separator')
        data = []
        titles = self.separate_repeated(True, eval('ncin.%s' %acdd), separator)
        for title in titles:
            data.append({'title': title, 'lang': mmd_element['lang']['default']})
        return data

    def get_abstracts(self, mmd_element, ncin):
        acdd = mmd_element['abstract'].pop('acdd')
        separator = mmd_element.pop('separator')
        data = []
        if acdd in ncin.ncattrs():
            abstracts = self.separate_repeated(True, eval('ncin.%s' %acdd), separator)
        else:
            self.missing_attributes['errors'].append('%s is a required ACDD attribute' %acdd)
            return
        for abstract in abstracts:
            data.append({'abstract': abstract, 'lang': mmd_element['lang']['default']})
        return data

    def get_temporal_extents(self, mmd_element, ncin):
        separator = mmd_element.pop('separator')
        acdd_start = mmd_element['start_date'].pop('acdd')
        acdd_end = mmd_element['end_date'].pop('acdd')
        if acdd_start in ncin.ncattrs():
            start_dates = [eval('ncin.%s' %acdd_start)]
        else:
            start_dates = [mmd_element['start_date'].pop('default')]
        if acdd_end in ncin.ncattrs():
            end_dates = [eval('ncin.%s' %acdd_end)]
        else:
            end_dates = []
        
        try:
            _ = parse(start_dates[0])
        except ParserError:
            start_dates = self.separate_repeated(True, start_dates[0], separator)
        if end_dates:
            try:
                _ = parse(end_dates[0])
            except ParserError:
                end_dates = self.separate_repeated(True, end_dates[0], separator)

        data = []
        for i in range(len(start_dates)):
            t_ext = {}
            t_ext['start_date'] = start_dates[i]
            if len(end_dates)>i:
                t_ext['end_date'] = end_dates[i]
            data.append(t_ext)
        return data

    def get_personnel(self, mmd_element, ncin):
        """ This function expects one value for the acdd fields, i.e., creator*. 
        Later, we should also add, e.g., publisher_*, and loop the acdd fields.
        """
        acdd_role = mmd_element['role'].pop('acdd')
        if acdd_role in ncin.ncattrs():
            roles = self.separate_repeated(True, eval('ncin.%s' %acdd_role))
        else:
            roles = [mmd_element['role'].pop('default')]

        acdd_name = mmd_element['name'].pop('acdd')
        if acdd_name in ncin.ncattrs():
            names = self.separate_repeated(True, eval('ncin.%s' %acdd_name))
        else:
            names = [mmd_element['name'].pop('default')]

        acdd_email = mmd_element['email'].pop('acdd')
        if acdd_email in ncin.ncattrs():
            emails = self.separate_repeated(True, eval('ncin.%s' %acdd_email))
        else:
            emails = [mmd_element['email'].pop('default')]

        acdd_organisation = mmd_element['organisation'].pop('acdd')
        if acdd_organisation in ncin.ncattrs():
            organisations = self.separate_repeated(True, eval('ncin.%s' %acdd_organisation))
        else:
            organisations = [mmd_element['organisation'].pop('default')]

        data = []
        for i in range(len(roles)):
            role = roles[i]
            if len(names)<=i:
                name = name
            else:
                name = names[i]
            if len(emails)<=i:
                email = email
            else:
                email = emails[i]
            if len(organisations)<=i:
                organisation = organisation
            else:
                organisation = organisations[i]
            data.append({
                'role': role, 
                'name': name, 
                'email': email,
                'organisation': organisation,
                })
        return data

    def get_keywords(self, mmd_element, ncin):
        acdd_resource = mmd_element['resource'].pop('acdd')
        if acdd_resource in ncin.ncattrs():
            resources = self.separate_repeated(True, eval('ncin.%s' %acdd_resource))
        else:
            resources = []

        acdd_keyword = mmd_element['keyword'].pop('acdd')
        if acdd_keyword in ncin.ncattrs():
            keywords = self.separate_repeated(True, eval('ncin.%s' %acdd_keyword))
        else:
            self.missing_attributes['errors'].append('%s is a required ACDD attribute' %acdd_keyword)
            return
        data = []
        resource = ''
        for i in range(len(keywords)):
            keyword = keywords[i]
            if len(resources)<=i:
                resource = resource
            else:
                resource = resources[i]
            data.append({'resource': resource, 'keyword': keyword})
        return data

    def get_projects(self, mmd_element, ncin):
        acdd = mmd_element['long_name'].pop('acdd')
        projects = []
        if acdd in ncin.ncattrs():
            projects = self.separate_repeated(True, eval('ncin.%s' %acdd))
        acdd_short = mmd_element['short_name'].pop('acdd')
        projects_short = []
        if acdd_short in ncin.ncattrs():
            projects_short = self.separate_repeated(True, eval('ncin.%s' %acdd_short))
        data = []
        for i in range(len(projects)):
            data.append({
                'long_name': projects[i],
                'short_name': projects_short[i]
                })
        return data

    def get_platforms(self, mmd_element, ncin):
        short_names = []
        acdd_short_name = mmd_element['short_name'].pop('acdd')
        if acdd_short_name in ncin.ncattrs():
            short_names = self.separate_repeated(True, eval('ncin.%s' %acdd_short_name))

        long_names = []
        acdd_long_name = mmd_element['long_name'].pop('acdd')
        if acdd_long_name in ncin.ncattrs():
            long_names = self.separate_repeated(True, eval('ncin.%s' %acdd_long_name))

        resources = []
        acdd_resource = mmd_element['resource'].pop('acdd')
        if acdd_resource in ncin.ncattrs():
            resources = self.separate_repeated(True, eval('ncin.%s' %acdd_resource))

        ishort_names = []
        acdd_instrument_short_name = mmd_element['instrument']['short_name'].pop('acdd')
        if acdd_instrument_short_name in ncin.ncattrs():
            ishort_names = self.separate_repeated(True, eval('ncin.%s' %acdd_instrument_short_name))

        ilong_names = []
        acdd_instrument_long_name = mmd_element['instrument']['long_name'].pop('acdd')
        if acdd_instrument_long_name in ncin.ncattrs():
            ilong_names = self.separate_repeated(True, eval('ncin.%s' %acdd_instrument_long_name))

        iresources = []
        acdd_instrument_resource = mmd_element['instrument']['resource'].pop('acdd')
        if acdd_instrument_resource in ncin.ncattrs():
            iresources = self.separate_repeated(True, eval('ncin.%s' %acdd_instrument_resource))

        data = []
        for i in range(len(long_names)):
            short_name = short_names[i]
            long_name = long_names[i]
            if len(resources)<=i:
                resource = ''
            else:
                resource = resources[i]
            if len(ishort_names)<=i:
                ishort_name = ''
            else:
                ishort_name = ishort_names[i]
            if len(ilong_names)<=i:
                ilong_name = ''
            else:
                ilong_name = ilong_names[i]
            if len(iresources)<=i:
                iresource = ''
            else:
                iresource = iresources[i]
            data.append({
                'short_name': short_name,
                'long_name': long_name,
                'resource': resource,
                'instrument': {
                    'short_name': ishort_name, 
                    'long_name': ilong_name, 
                    'resource': iresource,
                    }
                })
        return data

    def get_dataset_citations(self, mmd_element, ncin):
        """ MMD allows several dataset citations. This will lead to problems with 
        associating the diffetent elements to each other. In practice, most 
        datasets will only have one citation, so will handle that eventuality if 
        it arrives.
        """
        acdd_author = mmd_element['author'].pop('acdd')
        if acdd_author in ncin.ncattrs():
            authors = eval('ncin.%s' %acdd_author)

        publication_dates = []
        acdd_publication_date = mmd_element['publication_date'].pop('acdd')
        if acdd_publication_date in ncin.ncattrs():
            publication_dates = self.separate_repeated(True, eval('ncin.%s' %acdd_publication_date))
        acdd_title = mmd_element['title'].pop('acdd')
        if acdd_title in ncin.ncattrs():
            titles = self.separate_repeated(True, eval('ncin.%s' %acdd_title))
        acdd_url = mmd_element['url'].pop('acdd')
        urls = []
        if acdd_url in ncin.ncattrs():
            urls = self.separate_repeated(True, eval('ncin.%s' %acdd_url))
        acdd_other = mmd_element['other'].pop('acdd')
        others = []
        if acdd_other in ncin.ncattrs():
            others = self.separate_repeated(True, eval('ncin.%s' %acdd_other))
        data = []
        for i in range(len(publication_dates)):
            publication_date = publication_dates[i]
            title = titles[i]
            if len(urls)<=i:
                url = ''
            else:
                url = urls[i]
            if len(others)<=i:
                other = ''
            else:
                other = others[i]
            data.append({
                'author': authors,
                'publication_date': publication_date,
                'title': title,
                'url': url,
                'other': other,
                })
        return data

    def to_mmd(self):
        """
        Method for parsing content of NetCDF file, mapping discovery
        metadata to MMD, and writes MMD to disk.
        """

        #template_file = resource_string(self.__module__.split('.')[0], 'mmd_template.xml')

        # Why
        cf_mmd_lut = self.generate_cf_acdd_mmd_lut()

        # Some mandatory MMD does not have equivalent in ACDD
        # Make one to one mapping
        cf_mmd_lut.update(self.generate_cf_mmd_lut_missing_acdd())
        mmd_required_elements = self.required_mmd_elements()

        try:
            ncin = Dataset(self.netcdf_product)
        except OSError:
            ncin = Dataset(self.netcdf_product+'#fillmismatch')

        data = {}
        mmd_yaml = yaml.load(resource_string(self.__module__.split('.')[0], 'mmd_elements.yaml'), Loader=yaml.FullLoader)

        # handle tricky exceptions first
        data['data_center'] = self.get_data_centers(mmd_yaml.pop('data_center'), ncin)
        data['last_metadata_update'] = self.get_metadata_updates(
                                            mmd_yaml.pop('last_metadata_update'), ncin)
        data['title'] = self.get_titles(mmd_yaml.pop('title'), ncin)
        data['abstract'] = self.get_abstracts(mmd_yaml.pop('abstract'), ncin)
        data['temporal_extent'] = self.get_temporal_extents(mmd_yaml.pop('temporal_extent'), ncin)
        data['personnel'] = self.get_personnel(mmd_yaml.pop('personnel'), ncin)
        data['keywords'] = self.get_keywords(mmd_yaml.pop('keywords'), ncin)
        data['project'] = self.get_projects(mmd_yaml.pop('project'), ncin)
        data['platform'] = self.get_platforms(mmd_yaml.pop('platform'), ncin)
        data['dataset_citation'] = self.get_dataset_citations(mmd_yaml.pop('dataset_citation'), ncin)

        # Data access should not be read from the netCDF-CF file
        _ = mmd_yaml.pop('data_access')
        # Add OPeNDAP data_access if "netcdf_product" is OPeNDAP url
        if 'dodsC' in self.netcdf_product:
            data['data_access'] = self.get_data_access_dict(ncin)
        else:
            data['data_access'] = []

        for key in mmd_yaml:
            data[key] = self.get_acdd_metadata(mmd_yaml[key], ncin)
        
        for key in data:
            if data[key] == [{}]:
                data[key] = {}
      
        if len(self.missing_attributes['errors']) > 0:
            raise AttributeError("\n\t"+"\n\t".join(self.missing_attributes['errors']))

        env = jinja2.Environment(
            loader=jinja2.PackageLoader(self.__module__.split('.')[0], 'templates'),
            autoescape=jinja2.select_autoescape(['html', 'xml']),
            trim_blocks=True, lstrip_blocks=True
        )
        template = env.get_template('mmd_template.xml')

        out_doc = template.render(data=data)

        # Are all required elements present?
        msg = ''
        req_ok = True
        # If running in check only mode, exit now
        # and return whether the required elements are present
        if self.check_only:
            return req_ok, msg

        with open(self.output_file, 'w') as fh:
            fh.write(out_doc)

    def get_data_access_dict(self, ncin, add_wms_data_access=True, add_http_data_access=True):
        all_netcdf_variables = [var for var in ncin.variables]
        data_accesses = [{
                'type': 'OPeNDAP',
                'description': 'Open-source Project for a Network Data Access Protocol',
                'resource': self.netcdf_product,
                }]

        access_list = []
        _desc = []
        _res = []
        if add_wms_data_access:
            access_list.append('OGC WMS')
            _desc.append('OGC Web Mapping Service, URI to GetCapabilities Document.')
            _res.append(self.netcdf_product.replace('dodsC', 'wms'))
        if add_http_data_access:
            access_list.append('HTTP')
            _desc.append('Direct download of file')
            _res.append(self.netcdf_product.replace('dodsC', 'fileServer'))

        for prot_type, desc, res in zip(access_list, _desc, _res):
            data_access = {
                'type': prot_type,
                'description': desc,
                }
            if 'OGC WMS' in prot_type:
                data_access['wms_layers'] = []
                # Don't add variables containing these names to the wms layers
                skip_layers = ['latitude', 'longitude', 'angle']
                for w_layer in all_netcdf_variables:
                    if any(skip_layer in w_layer for skip_layer in skip_layers):
                        continue
                    data_access['wms_layers'].append(w_layer)
                # Need to add get capabilities to the wms resource
                res += '?service=WMS&version=1.3.0&request=GetCapabilities'
            data_access['resource'] = res

        data_accesses.append(data_access)

        return data_accesses




        # # Add empty/commented required  MMD elements that are not found in NetCDF file
        # for k, v in mmd_required_elements.items():

        #     # check if required element is part of output MMD (ie. of NetCDF file)
        #     if not len(root.findall(ET.QName(ns_map['mmd'], k))) > 0:
        #         #print('Did not find required element: {}.'.format(k))
        #         req_ok = False
        #         msg += (f"Missing element {k}\n")
        #         if not v:
        #             root.append(ET.Comment('<mmd:{}></mmd:{}>'.format(k, k)))
        #         else:
        #             root.append(ET.Comment('<mmd:{}>{}</mmd:{}>'.format(k, v, k)))

        #     da_element = ET.SubElement(root, ET.QName(ns_map['mmd'], 'data_access'))
        #     type_sub_element = ET.SubElement(da_element, ET.QName(ns_map['mmd'], 'type'))
        #     description_sub_element = ET.SubElement(da_element, ET.QName(ns_map['mmd'], 'description'))
        #     resource_sub_element = ET.SubElement(da_element, ET.QName(ns_map['mmd'], 'resource'))
        #     type_sub_element.text = "OPeNDAP"
        #     description_sub_element.text = "Open-source Project for a Network Data Access Protocol"
        #     resource_sub_element.text = self.netcdf_product

        #     _desc = ['Open-source Project for a Network Data Access Protocol.',
        #              'OGC Web Mapping Service, URI to GetCapabilities Document.']
        #     _res = [self.netcdf_product.replace('dodsC', 'fileServer'),
        #             self.netcdf_product.replace('dodsC', 'wms')]
        #     access_list = []
        #     _desc = []
        #     _res = []
        #     add_wms_data_access = True
        #     if add_wms_data_access:
        #         access_list.append('OGC WMS')
        #         _desc.append('OGC Web Mapping Service, URI to GetCapabilities Document.')
        #         _res.append(self.netcdf_product.replace('dodsC', 'wms'))
        #     add_http_data_access = True
        #     if add_http_data_access:
        #         access_list.append('HTTP')
        #         _desc.append('Open-source Project for a Network Data Access Protocol.')
        #         _res.append(self.netcdf_product.replace('dodsC', 'fileServer'))
        #     for prot_type, desc, res in zip(access_list, _desc, _res):
        #         dacc = ET.SubElement(root, ET.QName(ns_map['mmd'], 'data_access'))
        #         dacc_type = ET.SubElement(dacc, ET.QName(ns_map['mmd'], 'type'))
        #         dacc_type.text = prot_type
        #         dacc_desc = ET.SubElement(dacc, ET.QName(ns_map['mmd'], 'description'))
        #         dacc_desc.text = str(desc)
        #         dacc_res = ET.SubElement(dacc, ET.QName(ns_map['mmd'], 'resource'))
        #         if 'OGC WMS' in prot_type:
        #             wms_layers = ET.SubElement(dacc, ET.QName(ns_map['mmd'], 'wms_layers'))
        #             # Don't add variables containing these names to the wms layers
        #             skip_layers = ['latitude', 'longitude', 'angle']
        #             for w_layer in all_netcdf_variables:
        #                 if any(skip_layer in w_layer for skip_layer in skip_layers):
        #                     continue
        #                 wms_layer = ET.SubElement(wms_layers, ET.QName(ns_map['mmd'], 'wms_layer'))
        #                 wms_layer.text = w_layer
        #             # Need to add get capabilities to the wms resource
        #             res += '?service=WMS&version=1.3.0&request=GetCapabilities'
        #         dacc_res.text = res

        ## Add OGC WMS data_access as comment (Should be implemented above)
        #out_doc+= str('<!--\n<mmd:data_access>\n\t<mmd:type>OGC WMS</mmd:type>\n\t<mmd:description>OGC Web '
        #                           'Mapping Service, URI to GetCapabilities Document.</mmd:description>\n\t'
        #                           '<mmd:resource></mmd:resource>\n\t<mmd:wms_layers>\n\t\t<mmd:wms_layer>'
        #                           '</mmd:wms_layer>\n\t</mmd:wms_layers>\n</mmd:data_access>\n-->')

        #et = ET.ElementTree(ET.fromstring(out_doc))
        #if self.output_file:
        #    et.write(str(self.output_file), pretty_print=True)

    def required_mmd_elements(self):
        """ Create dict with required MMD elements"""

        mmd_required_elements = {
                'metadata_identifier': None,
                'metadata_status': None,
                'collection': None,
                'title': None,
                'abstract': None,
                'last_metadata_update': None,
                'dataset_production_status': None,
                'operational_status': None,
                'iso_topic_category': None,
                'keywords': '\n\t\t<mmd:keyword></mmd:keyword>\n\t',
                'temporal_extent': '\n\t\t<mmd:start_date></mmd:start_date>\n\t',
                'geographic_extent': str('\n\t\t<mmd:rectangle srsName=""> \n\t\t\t<mmd:north></mmd:north> \n\t\t\t'
                                         '<mmd:south></mmd:south> \n\t\t\t<mmd:east></mmd:east> \n\t\t\t<mmd:west>'
                                         '</mmd:west> \n\t\t</mmd:rectangle>\n\t')
            }
        return mmd_required_elements

    def generate_cf_mmd_lut_missing_acdd(self):
        """ Translation dict between ACDD and MMD (dict={ACDD: MDD})

        Create lookup table for mandatory MMD elements missing in the ACDD
        but that still is present as global attributes in the netCDF file"""

        cf_mmd = {'metadata_status': 'metadata_status',
                  'collection': 'collection',
                  'dataset_production_status': 'dataset_production_status',
                  'iso_topic_category': 'iso_topic_category',
                  'platform': 'platform,short_name',
                  'platform_long_name': 'platform,long_name',
                  'platform_resource': 'platform,resource',
                  'instrument': 'platform,instrument,short_name',
                  'instrument_long_name': 'platform,instrument,long_name',
                  'instrument_resource': 'platform,instrument,resource',
                  'ancillary_timeliness': 'platform,ancillary,timeliness',
                  'title_lang': 'attrib_lang',
                  'summary_lang': 'attrib_lang',
                  'license': 'use_constraint,identifier',
                  'license_resource': 'use_constraint,resource',
                  'publisher_country': 'personnel,country',
                  'creator_role': 'personnel,role',
                  'date_metadata_modified': 'last_metadata_update,update,datetime',
                  'date_metadata_modified_type': 'last_metadata_update,update,type',
                  'date_metadata_modified_note': 'last_metadata_update,update,note'}

        return cf_mmd

    def generate_cf_acdd_mmd_lut(self):
        """ Create the Look Up Table for CF/ACDD and MMD on the form:
        {CF/ACDD-element: MMD-element} """

        cf_acdd_mmd_lut = {
                'title': 'title',
                'summary': 'abstract',
                'keywords': 'keywords,keyword',
                'keywords_vocabulary': 'attrib_vocabulary',
                'Conventions': None,
                'id': 'metadata_identifier',
                'naming_authority': 'reference',
                'history': None,
                'source': 'activity_type',
                'processing_level': 'operational_status',
                'comment': None,
                'acknowledgement': 'reference',
                'license': 'use_constraint',
                'standard_name_vocabulary': None,
                'date_created': None,
                'creator_name': 'personnel,name',
                'creator_email': 'personnel,email',
                'creator_url': None,
                'project': 'project,long_name',
                'publisher_name': 'personnel,name',
                'publisher_email': 'personnel,email',
                'publisher_url': None,
                'geospatial_bounds': None,
                'geospatial_bounds_crs': 'attrib_srsName',
                'geospatial_bounds_vertical_crs': None,
                'geospatial_lat_min': 'geographic_extent,rectangle,south',
                'geospatial_lat_max': 'geographic_extent,rectangle,north',
                'geospatial_lon_min': 'geographic_extent,rectangle,west',
                'geospatial_lon_max': 'geographic_extent,rectangle,east',
                'geospatial_vertical_min': None,
                'geospatial_vertical_max': None,
                'geospatial_vertical_positive': None,
                'time_coverage_start': 'temporal_extent,start_date',
                'time_coverage_end': 'temporal_extent,end_date',
                'time_coverage_duration': None,
                'time_coverage_resolution': None,
                'creator_type': None,
                'publisher_type': None,
                'publisher_institution': 'personnel,organisation',
                'contributor_name': 'data_center,contact,name',
                'contributor_role': 'data_center,contact,role',
                'institution': 'data_center,data_center_name,long_name',
                'creator_institution': 'dataset_citation,dataset_publisher',
                'metadata_link': 'dataset_citation,online_resource',
                'references': 'dataset_citation,other_citation_details',
                'product_version': 'dataset_citation,version',
                'geospatial_lat_units': None,
                'geospatial_lat_resolution': None,
                'geospatial_lon_units': None,
                'geospatial_lon_resolution': None,
                'geospatial_vertical_units': None,
                'geospatial_vertical_resolution': None,
                'date_modified': None,
                'date_issued': None,
                'date_metadata_modified': 'last_metadata_update',
                'platform': None,
                'platform_vocabulary': None,
                'instrument': 'instrument,long_name',
                'instrument_vocabulary': None,
                'cdm_data_type': None}
        return cf_acdd_mmd_lut
