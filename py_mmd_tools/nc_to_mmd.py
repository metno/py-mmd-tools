"""
Tool for parsing metadata following the Attribute Convention for Data Discovery (ACDD)
in NetCDF files to the MET Norway Metadata format specification (MMD).

Can also be used check to check whether the required MMD elements are present in input file.

License:
     This file is part of the py-mmd-tools repository (https://github.com/metno/py-mmd-tools).
     py-mmd-tools is licensed under the Apache License 2.0 (
     https://github.com/metno/py-mmd-tools/blob/master/LICENSE)
"""
import os
import warnings
import yaml
import jinja2
import wget
import pandas as pd

from filehash import FileHash
from pkg_resources import resource_string
from dateutil.parser import parse
from dateutil.parser._parser import ParserError
from uuid import UUID, uuid4

import pathlib
from netCDF4 import Dataset
import lxml.etree as ET

def get_attr_info(key, convention, normalized):
    max_occurs_key = key.replace(convention, '')+'maxOccurs'
    if max_occurs_key in normalized.keys():
        max_occurs = normalized[max_occurs_key]
    else:
        max_occurs = ''
    repetition_allowed = 'yes' if max_occurs not in ['0', '1'] else 'no'
    min_occurs_key = key.replace(convention, '')+'minOccurs'
    if min_occurs_key in normalized.keys():
        required = int(normalized[min_occurs_key])
    else:
        required = 0
    separator_key = key.replace(convention, '')+'separator'
    if separator_key in normalized.keys():
        separator = normalized[separator_key]
    else:
        separator = ''
    default_key = key.replace(convention, '')+'default'
    if default_key in normalized.keys():
        default = normalized[default_key]
    else:
        default = ''
    return required, repetition_allowed, separator, default

def nc_attrs_from_yaml():
    mmd_yaml = yaml.load(resource_string(globals()['__name__'].split('.')[0], 'mmd_elements.yaml'), Loader=yaml.FullLoader)

    # Flatten dict
    df = pd.json_normalize(mmd_yaml, sep='>')
    normalized = df.to_dict(orient='records')[0]

    attributes = {}
    attributes['message'] = """
    This file is autogenerated from https://github.com/metno/py-mmd-tools/blob/master/py_mmd_tools/mmd_elements.yaml

    Please do not update this file manually. The yaml file (https://github.com/metno/py-mmd-tools/blob/master/py_mmd_tools/mmd_elements.yaml)
    is used as the authoritative source. If any translations from ACDD to MMD should be changed, the changes should be 
    made in that file."""
    attributes['acdd_ext'] = []
    attributes['acdd'] = {}
    attributes['acdd']['required'] = []
    attributes['acdd']['not_required'] = []
    for key, val in normalized.items():
        if key.endswith('acdd'):
            required, repetition_allowed, separator, default = get_attr_info(key, 'acdd', normalized)
            if required:
                attributes['acdd']['required'].append({
                    'mmd_field': key.replace('>acdd', ''),
                    'attribute': val, 
                    'repetition_allowed': repetition_allowed,
                    'separator': separator,
                    'default': default,
                })
            else:
                attributes['acdd']['not_required'].append({
                    'mmd_field': key.replace('>acdd', ''),
                    'attribute': val,
                    'repetition_allowed': repetition_allowed,
                    'separator': separator,
                    'default': default,
                })
        if key.endswith('acdd_ext'):
            required, repetition_allowed, separator, default = get_attr_info(key, 'acdd_ext', normalized)
            attributes['acdd_ext'].append({
                    'mmd_field': key.replace('>acdd_ext', ''),
                    'attribute': val, 
                    'repetition_allowed': repetition_allowed,
                    'separator': separator,
                    'default': default,
                })

    def is_list(value):
        return isinstance(value, list)

    env = jinja2.Environment(
        loader=jinja2.PackageLoader(globals()['__name__'].split('.')[0], 'templates'),
        autoescape=jinja2.select_autoescape(['html', 'xml']),
        trim_blocks=True, lstrip_blocks=True
    )
    env.filters['is_list'] = is_list
    template = env.get_template('nc_attributes_template.adoc')

    out_doc = template.render(data=attributes)
    return out_doc

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

    def get_acdd_metadata(self, mmd_element, ncin, mmd_element_name):
        """ Recursive function to trenslate from ACDD to MMD.

        If ACDD does not exist for a given MMD element, the function looks 
        for an alternative acdd_ext element instead. It may also use a default 
        value as specified in mmd_elements.yaml. Repetition is handled by 
        treating the acdd element as a comma separated list.

        The accd_ext and default values helps to make sure that this passes without errors.
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
                    if required:
                        self.missing_attributes['warnings'].append('Using default value %s for %s' %(str(default), mmd_element_name))
                elif not required:
                    if repetition_allowed:
                        return []
                    else:
                        return None
            else:
                data = {}
                for key, val in mmd_element.items():
                    if val:
                        data[key] = self.get_acdd_metadata(val, ncin, key)
        else:
            if acdd in ncin.ncattrs():
                data = self.separate_repeated(repetition_allowed, eval('ncin.%s' %acdd), separator)
            elif required:
                # We allow some missing elements (in particular for datasets from outside MET)
                data = default
                self.missing_attributes['warnings'].append('Using default value %s for %s' %(str(default), mmd_element_name))
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
        separator = mmd_element['title'].pop('separator')
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
        separator = mmd_element['start_date'].pop('separator')
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

    def get_attribute_name_list(self, mmd_element):
        """ Return list of attribute names either in ACDD or in an extension to ACDD """
        att_names_acdd = mmd_element.pop('acdd')
        if not isinstance(att_names_acdd, list):
            att_names_acdd = [att_names_acdd]
        att_names_acdd_ext = mmd_element.pop('acdd_ext', '')
        if att_names_acdd_ext:
            if not isinstance(att_names_acdd_ext, list):
                att_names_acdd_ext = [att_names_acdd_ext]
            att_names_acdd.extend(att_names_acdd_ext)
        return att_names_acdd

    def get_personnel(self, mmd_element, ncin):
        names = []
        roles = []
        emails = []
        organisations = []
        acdd_names = self.get_attribute_name_list(mmd_element['name'])
        acdd_roles = self.get_attribute_name_list(mmd_element['role'])
        acdd_emails = self.get_attribute_name_list(mmd_element['email'])
        acdd_organisations = self.get_attribute_name_list(mmd_element['organisation'])

        for acdd_name in acdd_names:
            # Get names
            num_names = 0
            if acdd_name in ncin.ncattrs(): 
                these_names = self.separate_repeated(True, eval('ncin.%s' %acdd_name))
            else:
                these_names = [mmd_element['name']['default']]
            names.extend(these_names)
            num_names = len(these_names)
            tmp = acdd_name
            acdd_main = tmp.replace('_name', '')
            # Get roles
            acdd_role = [role for role in acdd_roles if acdd_main in role][0]
            if acdd_role in ncin.ncattrs():
                roles.extend(self.separate_repeated(True, eval('ncin.%s' %acdd_role)))
            else:
                roles.extend([mmd_element['role']['default']])
            # Get emails
            if len(acdd_emails)>1:
                acdd_email = [email for email in acdd_emails if acdd_main in email][0]
            else:
                acdd_email = acdd_emails[0]
            if acdd_email and acdd_email in ncin.ncattrs():
                emails.extend(self.separate_repeated(True, eval('ncin.%s' %acdd_email)))
            else:
                emails.extend([mmd_element['email']['default']])
            # Get organisations
            if len(acdd_organisations)>1:
                acdd_organisation = [organisation for organisation in acdd_organisations if acdd_main in organisation][0]
            else:
                acdd_organisation = acdd_organisations[0]
            if acdd_organisation and acdd_organisation in ncin.ncattrs():
                these_orgs = self.separate_repeated(True, eval('ncin.%s' %acdd_organisation))
            else:
                these_orgs = [mmd_element['organisation']['default']]
            if not len(these_orgs)==len(these_names):
                for i in range(len(these_names)):
                    if len(these_orgs)-1<i:
                        these_orgs.append(these_orgs[i-1])
            organisations.extend(these_orgs)

        if not len(names)==len(roles)==len(emails)==len(organisations):
            self.missing_attributes['errors'].append('Attributes must have same number of entries')
        clean = 0
        if len(names)>1 and 'unknown' in names:
            clean = 1
        while clean:
            try:
                ind = names.index('unknown')
            except ValueError:
                clean = 0
            else:
                if len(names)>1:
                    names.pop(ind)
                    roles.pop(ind)
                    emails.pop(ind)
                    organisations.pop(ind)
                else:
                    clean = 0

        data = []
        for i in range(len(names)):
            data.append({
                'role': roles[i], 
                'name': names[i], 
                'email': emails[i],
                'organisation': organisations[i],
                })
        return data

    def get_keywords(self, mmd_element, ncin):
        acdd_vocabulary = mmd_element['vocabulary'].pop('acdd')
        vocabularies = []
        if acdd_vocabulary in ncin.ncattrs():
            vocabularies = self.separate_repeated(True, eval('ncin.%s' %acdd_vocabulary))
        else:
            self.missing_attributes['errors'].append('%s is a required ACDD attribute' %acdd_vocabulary)

        acdd_resource = mmd_element['resource'].pop('acdd_ext')
        if acdd_resource in ncin.ncattrs():
            resources = self.separate_repeated(True, eval('ncin.%s' %acdd_resource))
        else:
            resources = ['']

        keywords = []
        acdd_keyword = mmd_element['keyword'].pop('acdd')
        if acdd_keyword in ncin.ncattrs():
            keywords = self.separate_repeated(True, eval('ncin.%s' %acdd_keyword))
        else:
            self.missing_attributes['errors'].append('%s is a required ACDD attribute' %acdd_keyword)
        data = []
        resource = ''
        for i in range(len(keywords)):
            if len(resources)<=i:
                resource = resource
            else:
                resource = resources[i]
            if len(vocabularies)<=i:
                vocabulary = vocabularies
            else:
                vocabulary = vocabularies[i]
            data.append({'resource': resource, 'keyword': keywords[i], 'vocabulary': vocabulary})
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
            publication_date = parse(publication_dates[i]).strftime('%Y-%m-%d')
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

    @staticmethod
    def is_valid_uuid(uuid_to_test, version=4):
        """
        Check if uuid_to_test is a valid UUID.
        
         Parameters
        ----------
        uuid_to_test : str
        version : {1, 2, 3, 4}
        
         Returns
        -------
        `True` if uuid_to_test is a valid UUID, otherwise `False`.
        
         Examples
        --------
        >>> is_valid_uuid('c9bf9e57-1685-4c89-bafb-ff5af830be8a')
        True
        >>> is_valid_uuid('c9bf9e58')
        False
        """
        try:
            uuid_obj = UUID(uuid_to_test, version=version)
        except ValueError:
            return False
        return str(uuid_obj) == uuid_to_test

    def get_metadata_identifier(self, mmd_element, ncin, require_uuid=True):
        acdd = mmd_element.pop('acdd')
        valid = False
        invalid_chars = ['\\', '/', ':', ' ']
        if acdd in ncin.ncattrs():
            id = eval('ncin.%s' %acdd)
            valid = Nc_to_mmd.is_valid_uuid(id) * (not any(xx in id for xx in invalid_chars))
            if require_uuid and not valid:
                id = str(uuid4())
                self.missing_attributes['warnings'].append(
                    '%s ACDD attribute is not unique - created metadata_identifier MMD element as uuid.' %acdd)
        else:
            id = str(uuid4())
            self.missing_attributes['warnings'].append(
                    '%s ACDD attribute is missing - created metadata_identifier MMD element as uuid.' %acdd)
        return id

    def get_related_dataset(self, mmd_element, ncin):
        acdd_ext_relation_type = mmd_element['relation_type']['acdd_ext']
        relation_types = []
        if acdd_ext_relation_type in ncin.ncattrs():
            relation_types = self.separate_repeated(True, eval('ncin.%s' %acdd_ext_relation_type))
        acdd_ext_id = mmd_element['id']['acdd_ext']
        ids = []
        if acdd_ext_id in ncin.ncattrs():
            ids = self.separate_repeated(True, eval('ncin.%s' %acdd_ext_id))
        assert len(relation_types) == len(ids)
        data = []
        for i in range(len(ids)):
            data.append({
                    'id': ids[i],
                    'relation_type': relation_types[i],
                })
        return data

    def to_mmd(self, netcdf_local_path='', *args, **kwargs):
        """
        Method for parsing content of NetCDF file, mapping discovery
        metadata to MMD, and writes MMD to disk.
        """
        try:
            ncin = Dataset(self.netcdf_product)
        except OSError:
            ncin = Dataset(self.netcdf_product+'#fillmismatch')

        self.metadata = {}
        mmd_yaml = yaml.load(resource_string(self.__module__.split('.')[0], 'mmd_elements.yaml'), Loader=yaml.FullLoader)

        # handle tricky exceptions first
        self.metadata['metadata_identifier'] = self.get_metadata_identifier(mmd_yaml.pop('metadata_identifier'), ncin, **kwargs)
        self.metadata['data_center'] = self.get_data_centers(mmd_yaml.pop('data_center'), ncin)
        self.metadata['last_metadata_update'] = self.get_metadata_updates(
                mmd_yaml.pop('last_metadata_update'), ncin)
        self.metadata['title'] = self.get_titles(mmd_yaml.pop('title'), ncin)
        self.metadata['abstract'] = self.get_abstracts(mmd_yaml.pop('abstract'), ncin)
        self.metadata['temporal_extent'] = self.get_temporal_extents(mmd_yaml.pop('temporal_extent'), ncin)
        self.metadata['personnel'] = self.get_personnel(mmd_yaml.pop('personnel'), ncin)
        self.metadata['keywords'] = self.get_keywords(mmd_yaml.pop('keywords'), ncin)
        self.metadata['project'] = self.get_projects(mmd_yaml.pop('project'), ncin)
        self.metadata['platform'] = self.get_platforms(mmd_yaml.pop('platform'), ncin)
        self.metadata['dataset_citation'] = self.get_dataset_citations(mmd_yaml.pop('dataset_citation'), ncin)
        self.metadata['related_dataset'] = self.get_related_dataset(mmd_yaml.pop('related_dataset'), ncin)

        # Data access should not be read from the netCDF-CF file
        _ = mmd_yaml.pop('data_access')
        # Add OPeNDAP data_access if "netcdf_product" is OPeNDAP url
        rm_file_for_checksum_calculation = False
        if 'dodsC' in self.netcdf_product:
            self.metadata['data_access'] = self.get_data_access_dict(ncin, **kwargs)
            if netcdf_local_path:
                file_for_checksum_calculation = netcdf_local_path
            else:
                resource = ''
                for access in self.metadata['data_access']:
                    if access['type'] == 'HTTP':
                        resource = access['resource']
                print('Downloading NetCDF file to calculate checksum...')
                file_for_checksum_calculation = wget.download(resource)
                rm_file_for_checksum_calculation = True
        else:
            self.metadata['data_access'] = []
            file_for_checksum_calculation = self.netcdf_product

        file_size = pathlib.Path(file_for_checksum_calculation).stat().st_size / (1024 * 1024)

        for key in mmd_yaml:
            self.metadata[key] = self.get_acdd_metadata(mmd_yaml[key], ncin, key)

        # Set storage_information
        md5hasher = FileHash('md5', chunk_size=1048576)
        fchecksum = md5hasher.hash_file(file_for_checksum_calculation)
        self.metadata['storage_information'] = {
                'file_name': os.path.basename(self.netcdf_product),
                'file_location': self.netcdf_product.replace(os.path.basename(self.netcdf_product),''),
                'file_format': 'NetCDF-CF',
                'file_size': '%.2f'%file_size,
                'file_size_unit': 'MB',
                'checksum': fchecksum,
                'checksum_type': '%ssum'%md5hasher.hash_algorithm,
            }

        if rm_file_for_checksum_calculation:
            os.remove(file_for_checksum_calculation)
        
        if len(self.missing_attributes['errors']) > 0:
            raise AttributeError("\n\t"+"\n\t".join(self.missing_attributes['errors']))
        if len(self.missing_attributes['warnings']) > 0:
            warnings.warn("\n\t"+"\n\t".join(self.missing_attributes['warnings']))

        # Finally, check that the conventions attribute contains CF and ACCD
        assert 'CF' in ncin.getncattr('Conventions') and 'ACDD' in ncin.getncattr('Conventions')

        env = jinja2.Environment(
            loader=jinja2.PackageLoader(self.__module__.split('.')[0], 'templates'),
            autoescape=jinja2.select_autoescape(['html', 'xml']),
            trim_blocks=True, lstrip_blocks=True
        )
        template = env.get_template('mmd_template.xml')

        out_doc = template.render(data=self.metadata)

        # Are all required elements present?
        msg = ''
        req_ok = True
        # If running in check only mode, exit now
        # and return whether the required elements are present
        if self.check_only:
            return req_ok, msg

        with open(self.output_file, 'w') as fh:
            fh.write(out_doc)

    def get_data_access_dict(self, ncin, add_wms_data_access=False, add_http_data_access=True):
        all_netcdf_variables = []
        for var in ncin.variables:
            if 'standard_name' in ncin.variables[var].ncattrs():
                all_netcdf_variables.append(ncin.variables[var].standard_name)
        data_accesses = [{
                'type': 'OPeNDAP',
                'description': 'Open-source Project for a Network Data Access Protocol',
                'resource': self.netcdf_product,
                }]

        access_list = []
        _desc = []
        _res = []
        if add_wms_data_access: # and 2D dataset...?
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
                skip_layers = [
                        'latitude', 
                        'longitude', 
                        'angle', 
                        'time', 
                        'projection_x_coordinate', 
                        'projection_y_coordinate',
                    ]
                for w_layer in all_netcdf_variables:
                    if any(skip_layer in w_layer for skip_layer in skip_layers):
                        continue
                    data_access['wms_layers'].append(w_layer)
                # Need to add get capabilities to the wms resource
                res += '?service=WMS&version=1.3.0&request=GetCapabilities'
            data_access['resource'] = res
            data_accesses.append(data_access)

        return data_accesses
