"""
Tool for parsing metadata following the Attribute Convention for Data
Discovery (ACDD) in NetCDF files to the MET Norway Metadata format
specification (MMD).

Can also be used check to check whether the required MMD elements are
present in input file.

License:

This file is part of the py-mmd-tools repository
<https://github.com/metno/py-mmd-tools>.

py-mmd-tools is licensed under the Apache License 2.0
<https://github.com/metno/py-mmd-tools/blob/master/LICENSE>
"""
import os
import re
import warnings
import yaml
import jinja2
import logging
import wget
import shapely.wkt

from filehash import FileHash
from itertools import zip_longest
from pkg_resources import resource_string
from dateutil.parser import isoparse
from uuid import UUID

from metvocab.mmdgroup import MMDGroup

import pathlib
from netCDF4 import Dataset

from shapely.errors import WKTReadingError


def valid_url(url):
    """ Validate a url pattern (not its existence).
    """
    regex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url) is not None


def normalize_iso8601(s):
    """Convert provided string (s) to a normalized ISO 8601 value:

    YYYY-mm-ddTHH:MM:SS<second fraction><time zone>.

    Parameters:
    -----------
    s: str

    Returns:
    --------
    (<normalized ISO 8601 form of s>, None) upon success, otherwise (None, <error reason>).
    """

    # get initial datetime
    try:
        dt = isoparse(s)
    except Exception as e:
        return None, str(e)

    # format second fraction (drop altogether if zero, otherwise '.<microsecs>' left-padded with
    # zeros)
    sec_frac = '' if dt.microsecond == 0 else '.{:06d}'.format(dt.microsecond)

    # format time zone (use 'Z' for zero UTC offset, otherwise '+hh:mm')
    utc_offset = dt.utcoffset()
    tz_hours = tz_mins = 0
    if utc_offset is not None:
        secs = int(utc_offset.total_seconds())
        tz_hours = secs // 3600
        tz_mins = (secs % 3600) // 60
    tz = 'Z' if (tz_hours == 0 and tz_mins == 0) else '+{:02d}:{:02d}'.format(tz_hours, tz_mins)

    return dt.strftime('%Y-%m-%dT%H:%M:%S{}{}'.format(sec_frac, tz)), None


def normalize_iso8601_0(s):
    """Convert s to a normalized ISO 8601 value (like normalize_iso8601()), but don't flag any
    errors. If s is not valid ISO 8601, s itself is returned.
    This function is used for cases where we 1) assume that s is already valid or 2) rely on
    the validity of s to be checked elsewhere.

    Parameters:
    -----------
    s: str

    Returns:
    --------
    <normalized ISO 8601 form of s> upon success, otherwise the unmodified s.
    """

    ndt, _ = normalize_iso8601(s)
    if ndt is None:
        return s
    return ndt


class Nc_to_mmd(object):

    # Some constants:
    VALID_NAMING_AUTHORITIES = ['no.met']   # add others when needed..
    ACDD_ID = 'id'
    ACDD_NAMING_AUTH = 'naming_authority'
    ACDD_ID_INVALID_CHARS = ['\\', '/', ':', ' ']

    def __init__(self, netcdf_product, output_file=None, check_only=False):
        """Class for creating an MMD XML file based on the discovery
        metadata provided in the global attributes of NetCDF files that
        are compliant with the CF-conventions and ACDD.

        Args:
            output_file (pathlib): Output path for mmd.
            netcdf_product (str): Input NetCDF file (nc file or OPeNDAP
                url).
        """
        if output_file is None and check_only is False:
            raise ValueError('output_filename must be provided if check_only is False')
        super(Nc_to_mmd, self).__init__()
        self.output_file = output_file
        self.netcdf_product = netcdf_product
        self.check_only = check_only
        self.missing_attributes = {
            'errors': [],
            'warnings': []
        }
        self.metadata = {}

        self.platform_group = MMDGroup('mmd', 'https://vocab.met.no/mmd/Platform')
        self.platform_group.init_vocab()

        self.instrument_group = MMDGroup('mmd', 'https://vocab.met.no/mmd/Instrument')
        self.instrument_group.init_vocab()

        if not (self.platform_group.is_initialised and self.instrument_group.is_initialised):
            raise ValueError('Instrument or Platform group were not initialised')

        # Open netcdf file for reading
        with self.read_nc_file(self.netcdf_product) as ncin:
            self.check_attributes_not_empty(ncin)

        return

    def read_nc_file(self, fn):
        """ Open netcdf dataset, appending #fillmismatch if necessary
        """
        try:
            ncin = Dataset(self.netcdf_product)
        except OSError:
            ncin = Dataset(self.netcdf_product+'#fillmismatch')

        return ncin

    def separate_repeated(self, repetition_allowed, acdd_attr, separator=','):
        """ToDo: Add docstring"""
        if repetition_allowed:
            acdd_attr = [ss.strip() for ss in acdd_attr.split(separator)]
        return acdd_attr

    def get_acdd_metadata(self, mmd_element, ncin, mmd_element_name):
        """Recursive function to translate from ACDD to MMD.

        If ACDD does not exist for a given MMD element, the function
        looks for an alternative acdd_ext element instead. It may also
        use a default value as specified in mmd_elements.yaml.
        Repetition is handled by treating the acdd element as a comma
        separated list.

        The accd_ext and default values helps to make sure that this
        passes without errors.
        """
        # TODO: clean up and refactor to get rid of all the ifs...?

        required = mmd_element.pop('minOccurs', '') == '1'

        acdd = mmd_element.pop('acdd', {})
        acdd_ext = mmd_element.pop('acdd_ext', {})
        # This function only accepts one alternative ACDD field for
        # the translation
        if len(acdd.keys()) + len(acdd_ext.keys()) > 1:
            raise ValueError('Multiple ACDD or ACCD extension fields provided.'
                             ' Please use another translation function.')

        default = mmd_element.pop('default', '')
        repetition_allowed = mmd_element.pop('maxOccurs', '') not in ['0', '1']
        mmd_element.pop('comment', '')

        data = None
        if not acdd and not acdd_ext and default:
            data = default
        elif not acdd:
            if acdd_ext and len(mmd_element.items()) == 0:
                separator = acdd_ext.pop('separator', ',')
                acdd_ext_key = list(acdd_ext.keys())[0]
                if acdd_ext_key in ncin.ncattrs():
                    data = self.separate_repeated(
                        repetition_allowed, getattr(ncin, acdd_ext_key), separator
                    )
                elif default:
                    data = default
                elif 'default' in acdd_ext[acdd_ext_key].keys():
                    data = acdd_ext[acdd_ext_key]['default']
                elif required:
                    self.missing_attributes['errors'].append(
                        '%s is a required attribute' % acdd_ext_key
                    )
            elif len(mmd_element.items()) > 0:
                data = {}
                for key, val in mmd_element.items():
                    if val:
                        data[key] = self.get_acdd_metadata(val, ncin, key)
        else:
            acdd_key = list(acdd.keys())[0]
            if acdd_key in ncin.ncattrs():
                separator = acdd.pop('separator', ',')
                data = self.separate_repeated(
                    repetition_allowed, getattr(ncin, acdd_key), separator
                )
            elif required:
                # We may allow some missing elements (in particular for
                # datasets from outside MET) but this is currently not
                # needed. The below code is therefore commented..
                # if default:
                #     data = default
                #     self.missing_attributes['warnings'].append(
                #            'Using default value %s for %s' %(str(default), acdd))
                # else:
                self.missing_attributes['errors'].append('%s is a required attribute' % acdd_key)

        if mmd_element_name != 'metadata_status' and required and data == default:
            self.missing_attributes['warnings'].append(
                'Using default value %s for %s' % (str(default), mmd_element_name)
            )
        return data

    def get_data_centers(self, mmd_element, ncin):
        """Look up ACDD and ACDD extensions to populate MMD elements"""
        acdd_short_name = mmd_element['data_center_name']['short_name'].pop('acdd_ext')
        short_names = []

        acdd_short_name_key = list(acdd_short_name.keys())[0]
        try:
            short_names = self.separate_repeated(True, getattr(ncin, acdd_short_name_key))
        except AttributeError:
            self.missing_attributes['warnings'].append(
                '%s is a recommended attribute' % acdd_short_name_key)

        acdd_long_name = mmd_element['data_center_name']['long_name'].pop('acdd')
        acdd_long_name_key = list(acdd_long_name.keys())[0]
        long_names = []
        try:
            long_names = self.separate_repeated(True, getattr(ncin, acdd_long_name_key))
        except AttributeError:
            self.missing_attributes['errors'].append('%s is a required attribute'
                                                     % acdd_long_name_key)

        acdd_url = mmd_element['data_center_url'].pop('acdd')
        acdd_url_key = list(acdd_url.keys())[0]
        try:
            urls = self.separate_repeated(True, getattr(ncin, acdd_url_key))
        except AttributeError:
            urls = ''

        data = []
        for i in range(len(long_names)):
            if len(urls) <= i:
                url = ''
            else:
                url = urls[i]
            dc = {
                'data_center_name': {'long_name': long_names[i]},
                'data_center_url': url,
            }
            if len(short_names) == len(long_names):
                dc['data_center_name']['short_name'] = short_names[i]
            data.append(dc)
        return data

    def get_metadata_updates(self, mmd_element, ncin):
        """Get time of metadata creation, last metadata update and
        update type.

        OBS: the challenge with this function is that it must translate
        two acdd/accd_ext fields for each update.datetime and
        update.type. This is handled by hardcoding the values. The
        acdd and acdd_ext translation variables in any case needed for
        use in the data management handbook, so therefore we have a
        check here to make sure that the hardcoded values in this
        function agree with the ones in the yaml file.
        """
        acdd_time = mmd_element['update']['datetime'].pop('acdd', '')
        acdd_type = mmd_element['update']['type'].pop('acdd_ext', '')

        DATE_CREATED = 'date_created'
        # Check that DATE_CREATED attribute is present
        if DATE_CREATED not in ncin.ncattrs():
            self.missing_attributes['errors'].append(
                'ACDD attribute %s is required' % DATE_CREATED
            )
            return

        times = []
        types = []
        received_time = ''
        for tt in acdd_time.keys():
            received_time += '%s, ' % tt
        received_type = ''
        for ty in acdd_type.keys():
            received_type += '%s, ' % ty

        if DATE_CREATED not in acdd_time.keys():
            raise AttributeError(
                'ACDD attribute inconsistency in mmd_elements.yaml. Expected %s but received %s.'
                % (DATE_CREATED, received_time)
            )

        if 'date_metadata_modified' not in acdd_time.keys():
            raise AttributeError(
                'ACDD attribute inconsistency in mmd_elements.yaml. Expected %s but received %s.'
                % ('date_metadata_modified', received_type)
            )

        for field_name in acdd_time.keys():
            # Already checked if part of ncin
            if field_name == DATE_CREATED:
                times.append(ncin.date_created)
                types.append(mmd_element['update']['type'].pop('default', 'Created'))
            else:
                if field_name in ncin.ncattrs():
                    times.extend(self.separate_repeated(True, getattr(ncin, field_name)))
                    mtypename = 'date_metadata_modified_type'
                    if mtypename in ncin.ncattrs():
                        modified_type = ncin.date_metadata_modified_type
                    else:
                        # set this to avoid a lot of failing datasets
                        # - this should be a minor issue..
                        modified_type = 'Minor modification'
                        self.missing_attributes['warnings'].append(
                            "Using default value '%s' for %s" % (modified_type, mtypename)
                        )
                    types.extend(self.separate_repeated(True, modified_type))

        data = {}
        data['update'] = []
        for i in range(len(times)):
            tt, msg = normalize_iso8601(times[i])
            if tt is None:
                self.missing_attributes['errors'].append(
                    "Datetime element must be in ISO8601 format: "
                    "YYYY-mm-ddTHH:MM:SS<second fraction><time zone>.")
            else:
                data['update'].append({'datetime': tt, 'type': types[i]})
        return data

    def get_titles(self, mmd_element, ncin):
        """ToDo: Add docstring"""
        return self.get_title_or_abstract('title', mmd_element, ncin)

    def get_abstracts(self, mmd_element, ncin):
        """ToDo: Add docstring"""
        return self.get_title_or_abstract('abstract', mmd_element, ncin)

    def get_title_or_abstract(self, elem_name, mmd_element, ncin):
        """ Title and abstract need to have translations (to
        Norwegian at least). This function handles such
        functionality, which differs somewhat for the needs of
        other fields.
        """
        # The main title or abstract is the acdd element
        acdd = mmd_element[elem_name].pop('acdd')
        # ACDD does not have information on language - mmd_element['land']['acdd_ext']
        # provides the language of the title or abstract
        acdd_ext_lang = mmd_element['lang'].pop('acdd_ext')
        # Extra anguages are not supported in ACDD - acdd_ext provides a list of
        # other languages
        acdd_ext = mmd_element[elem_name].pop('acdd_ext', [])
        data = []
        contents = []
        acdd_key = list(acdd.keys())[0]
        if acdd_key in ncin.ncattrs():
            contents.append(getattr(ncin, acdd_key))
        else:
            self.missing_attributes['errors'].append('%s is a required ACDD attribute'
                                                     % acdd_key)
            return data
        acdd_ext_lang_key = list(acdd_ext_lang.keys())[0]
        if acdd_ext_lang_key in ncin.ncattrs():
            content_lang = [getattr(ncin, acdd_ext_lang_key)]
        else:
            content_lang = [acdd_ext_lang[acdd_ext_lang_key]['default']]
        lang_key = list(acdd_ext.keys())
        for lang_key in acdd_ext:
            if lang_key in ncin.ncattrs():
                contents.append(getattr(ncin, lang_key))
                content_lang.append(lang_key[-2:])
        for i in range(len(contents)):
            data.append({elem_name: contents[i], 'lang': content_lang[i]})
        return data

    def get_temporal_extents(self, mmd_element, ncin):
        """ToDo: Add docstring"""
        acdd_start = mmd_element['start_date'].pop('acdd')
        acdd_end = mmd_element['end_date'].pop('acdd')
        data = []
        start_dates = []
        acdd_start_key = list(acdd_start.keys())[0]
        if acdd_start_key in ncin.ncattrs():
            start_dates = self.separate_repeated(True, getattr(ncin, acdd_start_key))
        else:
            self.missing_attributes['errors'].append(
                '%s is a required ACDD attribute' % acdd_start_key
            )
        acdd_end_key = list(acdd_end.keys())[0]
        end_dates = []
        if acdd_end_key in ncin.ncattrs():
            end_dates = self.separate_repeated(True, getattr(ncin, acdd_end_key))

        def convert_to_normalized_iso8601(dts):
            """ Replaces datetimes in dts with ISO 8601 normalized
            forms if possible, recording cases where normalization is
            not possible.

            Parameters:
            -----------
            dts: list of str

            Returns:
            --------
            A version of dts where each item is 1) replaced by the
            normalized ISO 8601 form if possible, or 2) kept
            unmodified.

            Side effects:
            -------------
            For each item in dts that cannot be converted to
            normalized ISO 8601 form, a reason is recorded in
            self.missing_attributes['errors'].
            """
            ndts = []
            for dt in dts:
                ndt, reason = normalize_iso8601(dt)
                if ndt is None:
                    ndts.append(dt)  # keep original
                    self.missing_attributes['errors'].append(
                        'ACDD start/end datetime %s is not valid ISO8601: %s.' % (dt, reason)
                    )
                else:
                    ndts.append(ndt)  # replace with normalized form
            return ndts

        nstart_dates = convert_to_normalized_iso8601(start_dates)
        nend_dates = convert_to_normalized_iso8601(end_dates)

        for i in range(len(nstart_dates)):
            t_ext = {}
            t_ext['start_date'] = nstart_dates[i]
            if len(nend_dates) > i:
                t_ext['end_date'] = nend_dates[i]
            data.append(t_ext)
        return data

    def get_attribute_name_list(self, mmd_element):
        """ Return dict of ACDD and ACDD_EXT attribute names.
        """
        att_names = mmd_element.pop('acdd', {})
        att_names_acdd_ext = mmd_element.pop('acdd_ext', '')
        if att_names_acdd_ext:
            for key in att_names_acdd_ext.keys():
                att_names[key] = att_names_acdd_ext[key]
        return att_names

    def get_personnel(self, mmd_element, ncin):
        """ToDo: Add docstring"""
        names = []
        roles = []
        emails = []
        organisations = []
        acdd_names = self.get_attribute_name_list(mmd_element['name'])
        acdd_roles = self.get_attribute_name_list(mmd_element['role'])
        acdd_emails = self.get_attribute_name_list(mmd_element['email'])
        acdd_organisations = self.get_attribute_name_list(mmd_element['organisation'])

        for acdd_name in acdd_names.keys():
            # Get names
            if acdd_name in ncin.ncattrs():
                these_names = self.separate_repeated(True, getattr(ncin, acdd_name))
            else:
                these_names = [acdd_names[acdd_name]['default']]
            names.extend(these_names)
            tmp = acdd_name
            acdd_main = tmp.replace('_name', '')
            # Get roles
            acdd_role = [role for role in acdd_roles.keys() if acdd_main in role][0]
            if acdd_role in ncin.ncattrs():
                roles.extend(self.separate_repeated(True, getattr(ncin, acdd_role)))
            else:
                roles.extend([acdd_roles[acdd_role]['default']])
            # Get emails
            acdd_email = [email for email in acdd_emails.keys() if acdd_main in email][0]
            if acdd_email and acdd_email in ncin.ncattrs():
                emails.extend(self.separate_repeated(True, getattr(ncin, acdd_email)))
            else:
                emails.extend([acdd_emails[acdd_email]['default']])
            # Get organisations
            acdd_organisations_list = [
                organisation for organisation in acdd_organisations.keys()
                if acdd_main in organisation]
            these_orgs = []
            for org_elem in acdd_organisations_list:
                if org_elem and org_elem in ncin.ncattrs():
                    these_orgs.extend(self.separate_repeated(True, getattr(ncin, org_elem)))
            if not these_orgs:
                for org in acdd_organisations.keys():
                    if type(acdd_organisations[org]) is dict and \
                            'default' in acdd_organisations[org].keys():
                        these_orgs.append(acdd_organisations[org]['default'])
            if not len(these_orgs) == len(these_names):
                for i in range(len(these_names)):
                    if len(these_orgs) - 1 < i:
                        these_orgs.append(these_orgs[i-1])
            organisations.extend(these_orgs)

        if not len(names) == len(roles) == len(emails) == len(organisations):
            self.missing_attributes['errors'].append('Attributes must have same number of entries')
        clean = 0
        if len(names) > 1 and 'Not available' in names:
            clean = 1
        while clean:
            try:
                ind = names.index('Not available', -1)
            except ValueError:
                clean = 0
            else:
                if len(names) > 1:
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
        """ToDo: Add docstring"""
        ok_formatting = True
        acdd_vocabulary = mmd_element['vocabulary'].pop('acdd')
        vocabularies = []
        acdd_vocabulary_key = list(acdd_vocabulary.keys())[0]
        if acdd_vocabulary_key in ncin.ncattrs():
            vocabularies = self.separate_repeated(True, getattr(ncin, acdd_vocabulary_key))
        else:
            ok_formatting = False
            self.missing_attributes['errors'].append(
                '%s is a required ACDD attribute' % acdd_vocabulary_key
            )
        resources = []
        resource_short_names = []
        for vocabulary in vocabularies:
            voc_elems = vocabulary.split(':')
            if len(voc_elems) != 4:
                # note that the url contains a ":"
                ok_formatting = False
                self.missing_attributes['errors'].append(
                    '%s must be formatted as <short_name>:<long_name>:<url>'
                    % acdd_vocabulary_key)
            else:
                resources.append(voc_elems[0]+':'+voc_elems[2]+':'+voc_elems[3])
                resource_short_names.append(voc_elems[0])

        keywords = []
        acdd_keyword = mmd_element['keyword'].pop('acdd')
        acdd_keyword_key = list(acdd_keyword.keys())[0]
        if acdd_keyword_key in ncin.ncattrs():
            keywords = self.separate_repeated(True, getattr(ncin, acdd_keyword_key))
        else:
            ok_formatting = False
            self.missing_attributes['errors'].append(
                '%s is a required ACDD attribute' % acdd_keyword_key
            )

        keyword_short_names = []
        for keyword in keywords:
            keyword_short_name = keyword.split(':')[0]
            keyword_short_names.append(keyword_short_name)
            if keyword_short_name not in resource_short_names:
                ok_formatting = False
                self.missing_attributes['errors'].append(
                    '%s must be defined in the %s ACDD attribute'
                    % (keyword_short_name, acdd_vocabulary_key)
                )

        data = []
        if ok_formatting:
            for vocabulary in vocabularies:
                prefix = vocabulary.split(':')[0]
                resource = [r.replace(prefix+':', '') for r in resources if prefix in r][0]
                if not valid_url(resource):
                    self.missing_attributes['errors'].append(
                        '%s in %s attribute is not a valid url' % (resource, acdd_vocabulary_key))
                    continue
                keywords_this = [k.replace(prefix+':', '') for k in keywords if prefix in k]
                data.append({
                    'resource': resource,
                    'keyword': keywords_this,
                    'vocabulary': prefix
                })
        return data

    def get_projects(self, mmd_element, ncin):
        """ToDo: Add docstring"""
        acdd = mmd_element['long_name'].pop('acdd')
        projects = []

        acdd_key = list(acdd.keys())[0]
        if acdd_key in ncin.ncattrs():
            projects = self.separate_repeated(True, getattr(ncin, acdd_key))

        acdd_short = mmd_element['short_name'].pop('acdd_ext')
        projects_short = []
        acdd_short_key = list(acdd_short.keys())[0]
        if acdd_short_key in ncin.ncattrs():
            projects_short = self.separate_repeated(True, getattr(ncin, acdd_short_key))
        data = []
        for i in range(len(projects)):
            tmp = {}
            tmp['long_name'] = projects[i]
            # project is not required, so project short name should
            # not be required either
            if len(projects) == len(projects_short):
                tmp['short_name'] = projects_short[i]
            data.append(tmp)
        return data

    def get_platforms(self, mmd_element, ncin):
        """Get dicts with MMD entries for the observation platform and
        its instruments.

        NOTE: This function should be rewritten according to a solution
        to https://github.com/metno/py-mmd-tools/issues/107
        """
        long_names = []
        acdd_long_name = mmd_element['long_name'].pop('acdd')
        acdd_long_name_key = list(acdd_long_name.keys())[0]
        if acdd_long_name_key in ncin.ncattrs():
            long_names = self.separate_repeated(True, getattr(ncin, acdd_long_name_key))

        ilong_names = []
        acdd_instrument_long_name = mmd_element['instrument']['long_name'].pop('acdd')
        acdd_instrument_long_name_key = list(acdd_instrument_long_name.keys())[0]
        if acdd_instrument_long_name_key in ncin.ncattrs():
            ilong_names = self.separate_repeated(
                True, getattr(ncin, acdd_instrument_long_name_key)
            )

        resources = []
        acdd_resource = mmd_element['resource'].pop('acdd')
        acdd_resource_key = list(acdd_resource.keys())[0]
        if acdd_resource_key in ncin.ncattrs():
            resources = self.separate_repeated(True, getattr(ncin, acdd_resource_key))

        iresources = []
        acdd_instrument_resource = mmd_element['instrument']['resource'].pop('acdd')
        acdd_instrument_resource_key = list(acdd_instrument_resource.keys())[0]
        if acdd_instrument_resource_key in ncin.ncattrs():
            iresources = self.separate_repeated(
                True, getattr(ncin, acdd_instrument_resource_key))

        data = []
        for long_name, ilong_name, resource, iresource in zip_longest(
            long_names, ilong_names, resources, iresources, fillvalue=''
        ):
            long_name = long_name.split('>')[-1].strip()
            ilong_name = ilong_name.split('>')[-1].strip()

            # Searches with '' is safe
            platform_data = self.platform_group.search(long_name)
            instrument_data = self.instrument_group.search(ilong_name)

            data_dict = {
                'long_name': long_name,
                'short_name': platform_data.get('Short_Name', ''),
                'resource': platform_data.get('Resource', ''),
            }

            if resource != '':
                data_dict['resource'] = resource

            if data_dict['resource'] == '' or not valid_url(data_dict['resource']):
                self.missing_attributes['warnings'].append(
                    '"%s" in %s attribute is not a valid url' % (data_dict['resource'],
                                                                 acdd_resource_key))
                data_dict.pop('resource')

            instrument_dict = {
                'long_name': instrument_data.get('Long_Name', ''),
                'short_name': instrument_data.get('Short_Name', ''),
                'resource': instrument_data.get('Resource', '')
            }

            if ilong_name != '':
                instrument_dict['long_name'] = ilong_name
            if iresource != '':
                instrument_dict['resource'] = iresource

            if instrument_dict['resource'] == '' or not valid_url(instrument_dict['resource']):
                self.missing_attributes['warnings'].append(
                    '"%s" in %s attribute is not a valid url' % (instrument_dict['resource'],
                                                                 acdd_instrument_resource_key))
                instrument_dict.pop('resource')

            if instrument_dict['long_name'] != '' or instrument_dict['short_name'] != '':
                data_dict['instrument'] = instrument_dict

            data.append(data_dict)

        return data

    def get_dataset_citations(self, mmd_element, ncin):
        """MMD allows several dataset citations. This will lead to
        problems with associating the different elements to each other.
        In practice, most datasets will only have one citation, so will
        handle that eventuality if it arrives.
        """
        acdd_author = mmd_element['author'].pop('acdd')
        authors = []
        acdd_author_key = list(acdd_author.keys())[0]
        if acdd_author_key in ncin.ncattrs():
            authors = getattr(ncin, acdd_author_key)

        publication_dates = []
        acdd_publication_date = mmd_element['publication_date'].pop('acdd')
        acdd_publication_date_key = list(acdd_publication_date.keys())[0]
        if acdd_publication_date_key in ncin.ncattrs():
            publication_dates = self.separate_repeated(
                True, getattr(ncin, acdd_publication_date_key)
            )

        acdd_title = mmd_element['title'].pop('acdd')
        acdd_title_key = list(acdd_title.keys())[0]
        if acdd_title_key in ncin.ncattrs():
            title = getattr(ncin, acdd_title_key)
        acdd_url = mmd_element['url'].pop('acdd')
        urls = []
        acdd_url_key = list(acdd_url.keys())[0]
        if acdd_url_key in ncin.ncattrs():
            urls = self.separate_repeated(True, getattr(ncin, acdd_url_key))
        data = []
        for i in range(len(publication_dates)):
            ndt, reason = normalize_iso8601(publication_dates[i])
            if ndt is None:
                # in case the dates are not actual dates
                self.missing_attributes['errors'].append(
                    'ACDD attribute %s contains an invalid ISO8601 date: %s: %s'
                    % (acdd_publication_date_key, publication_dates[i], reason)
                )
            else:
                data_dict = {
                    'author': authors,
                    'publication_date': ndt,
                    'title': title,
                }
                if len(urls) <= i:
                    ## Issue warning (not necessary, since it is not mandatory)
                    #self.missing_attributes['warnings'].append(
                    #    '%s attribute is missing' % acdd_url_key)
                    url = ''
                else:
                    url = urls[i]
                # Validate the url
                if not valid_url(url):
                    if url != '':
                        # Issue warning
                        self.missing_attributes['warnings'].append(
                            '"%s" in %s attribute is not a valid url' % (url, acdd_url_key))
                else:
                    data_dict['url'] = url

                data.append(data_dict)

        return data

    @staticmethod
    def is_valid_uuid(uuid_to_test, version=4):
        """Check if uuid_to_test is a valid UUID.

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

    def get_metadata_identifier(self, mmd_element, ncin, **kwargs):
        """Look up ACDD element and populate MMD metadata identifier"""
        acdd = mmd_element.pop('acdd')
        valid = False
        ncid = ''
        naming_authority = ''
        # id and naming_authority are required, and both should be in
        # the acdd list
        acdd_key = list(acdd.keys())
        if len(acdd_key) != 2 or self.ACDD_ID not in acdd_key or \
                self.ACDD_NAMING_AUTH not in acdd_key:
            raise AttributeError(
                'ACDD attribute inconsistency in mmd_elements.yaml. Expected %s and %s but '
                'received %s.'
                % (self.ACDD_ID, self.ACDD_NAMING_AUTH, str(acdd_key))
            )
        if self.ACDD_ID not in ncin.ncattrs():
            self.missing_attributes['errors'].append(
                '%s is a required attribute.' % self.ACDD_ID)
        if self.ACDD_NAMING_AUTH not in ncin.ncattrs():
            self.missing_attributes['errors'].append(
                '%s is a required attribute.' % self.ACDD_NAMING_AUTH
            )
        if self.ACDD_ID in ncin.ncattrs():
            ncid = getattr(ncin, self.ACDD_ID)
            valid = Nc_to_mmd.is_valid_uuid(ncid) * (
                not any(xx in ncid for xx in self.ACDD_ID_INVALID_CHARS)
            )
            if not valid:
                ncid = ''
                self.missing_attributes['errors'].append(
                    '%s ACDD attribute is not valid.' % self.ACDD_ID
                )
        if self.ACDD_NAMING_AUTH in ncin.ncattrs():
            naming_authority = getattr(ncin, self.ACDD_NAMING_AUTH)
            if naming_authority not in self.VALID_NAMING_AUTHORITIES:
                naming_authority = ''
                self.missing_attributes['errors'].append(
                    '%s ACDD attribute is not valid.' % self.ACDD_NAMING_AUTH
                )
        return naming_authority + ':' + ncid

    def get_related_dataset(self, mmd_element, ncin):
        """Get id and relation type for a related dataset"""
        acdd_ext_relation_type = mmd_element['relation_type']['acdd_ext']
        relation_types = []
        acdd_ext_relation_type_key = list(acdd_ext_relation_type.keys())[0]
        if acdd_ext_relation_type_key in ncin.ncattrs():
            relation_types = self.separate_repeated(
                True, getattr(ncin, acdd_ext_relation_type_key)
            )
        acdd_ext_id = mmd_element['related_dataset']['acdd_ext']
        ids = []
        acdd_ext_id_key = list(acdd_ext_id.keys())[0]
        if acdd_ext_id_key in ncin.ncattrs():
            ids = self.separate_repeated(True, getattr(ncin, acdd_ext_id_key))
        # TODO: use if-test and raise exception instead:
        assert len(relation_types) == len(ids)
        data = []
        for i in range(len(ids)):
            data.append({
                'id': ids[i],
                'relation_type': relation_types[i],
            })
        return data

    def get_geographic_extent_polygon(self, mmd_element, ncin):
        """ToDo: Add docstring"""
        data = None
        acdd = mmd_element['acdd']
        acdd_key = list(acdd.keys())[0]
        if acdd_key not in ncin.ncattrs():
            return None
        wkt = eval('ncin.%s'%acdd_key)
        try:
            pp = shapely.wkt.loads(wkt)
        except WKTReadingError:
            self.missing_attributes['errors'].append(
                '%s must be formatted as a WKT string' % acdd_key
            )
        else:
            lat = pp.exterior.coords.xy[0]
            lon = pp.exterior.coords.xy[1]
            pos = []
            for i in range(len(lat)):
                pos.append('%.4f %.4f'%(lat[i], lon[i]))
            data = {
                'srsName': ncin.geospatial_bounds_crs,
                'pos': pos
            }
        return data

    def get_geographic_extent_rectangle(self, mmd_element, ncin):
        """Get dataset coverage as a rectangle (north, south, east, west).
        """
        data = {}
        directions = ['north', 'south', 'east', 'west']

        data['srsName'] = mmd_element['srsName']['default']
        for dir in directions:
            acdd = mmd_element[dir]['acdd']
            acdd_key = list(acdd.keys())[0]
            if acdd_key not in ncin.ncattrs():
                self.missing_attributes['errors'].append(
                    '%s is a required attribute' % acdd_key
                )
            else:
                data[dir] = getattr(ncin, acdd_key)
                try:
                    float(data[dir])
                except ValueError:
                    self.missing_attributes['errors'].append(
                        '%s must be convertible to float type.' % acdd_key
                    )

        return data

    def get_related_information(self, mmd_element, ncin):
        """ Get related information stored in the netcdf attribute
        references.
        """
        VALID_TYPES = [
            'Project home page',
            'Users guide',
            'Dataset landing page',
            'Scientific publication',
            'Data paper',
            'Data management plan',
            'Software',
            'Other documentation',
            'Observation facility',
            'Extended metadata',
        ]
        data = []
        repetition_allowed = mmd_element.pop('maxOccurs', '') not in ['0', '1']
        acdd = mmd_element['resource']['acdd']
        separator = acdd.pop('separator', ',')
        acdd_key = list(acdd.keys())[0]
        refs = []
        if acdd_key in ncin.ncattrs():
            refs = self.separate_repeated(repetition_allowed, getattr(ncin, acdd_key), separator)
        for ref in refs:
            ri = ref.split('(')
            if len(ri) != 2:
                self.missing_attributes['errors'].append(
                    "%s must be formed as <uri>(<type>)." % acdd_key
                )
                continue
            uri = ri[0].strip()
            if not valid_url(uri):
                self.missing_attributes['errors'].append(
                    '%s must contain valid uris' % acdd_key
                )
                continue
            type = ri[1][:-1]
            if type not in VALID_TYPES:
                self.missing_attributes['errors'].append(
                    'Reference types must follow a controlled '
                    'vocabulary from MMD (see https://htmlpreview.'
                    'github.io/?https://github.com/metno/mmd/blob/'
                    'master/doc/mmd-specification.html#related-'
                    'information-types).')
                continue
            ri = {'resource': uri, 'type': type}
            ri['description'] = ""  # not easily available in acdd - needs to be discussed
            data.append(ri)
        return data

    def check_attributes_not_empty(self, ncin):
        """ Check that no global attributes are empty.
        """
        for attr in ncin.ncattrs():
            if not ncin.getncattr(attr):
                raise ValueError("%s: Global attribute %s is empty - please correct." % (
                    self.netcdf_product, attr))

    def check_conventions(self, ncin):
        """ Check that the Conventions attribute is present, and
        that it contains all needed information.
        """
        # Check that the Conventions attribute is present
        if 'Conventions' not in ncin.ncattrs():
            self.missing_attributes['errors'].append(
                'Required attribute "Conventions" is missing. This '
                'should be provided as a comma-separated string of '
                'the conventions that are followed by the dataset.')
        else:
            # Check that the conventions attribute contains CF and ACCD
            if 'CF' not in ncin.getncattr('Conventions'):
                self.missing_attributes['errors'].append(
                    'The dataset should follow the CF-standard. Please '
                    'provide the CF standard version in the Conventions '
                    'attribute.')

            if 'ACDD' not in ncin.getncattr('Conventions'):
                self.missing_attributes['errors'].append(
                    'The dataset should follow the ACDD convention. '
                    'Please provide the ACDD convention version in '
                    'the Conventions attribute.')

    def get_license(self, mmd_element, ncin):
        """ Get ACDD license attribute.

        ACDD definition: The license should be provided as a URL to a
        standard or specific license. It may also be specified as
        "Freely Distributed" or "None", or described in free text
        including any restrictions to data access and distribution.

        adc.met.no addition: It is strongly recommended to use
        identifiers and URL's from https://spdx.org/licenses/ and to
        use a form similar to <URL>(<Identifier>) using elements from
        the SPDX source listed above.

        """
        data = None
        old_version = False
        acdd_license = list(mmd_element['resource']['acdd'].keys())[0]
        acdd_license_id = list(mmd_element['identifier']['acdd_ext'].keys())[0]
        license = getattr(ncin, acdd_license).split('(')
        license_url = license[0].strip()
        # validate url
        if not valid_url(license_url):
            # Try deprecated attribute name
            if 'license_resource' in ncin.ncattrs():
                license_url = ncin.license_resource
            if not valid_url(license_url):
                self.missing_attributes['errors'].append(
                    '"%s" is not a valid url' % license_url)
                return data
            else:
                data = {'resource': license_url}
                old_version = True
                self.missing_attributes['warnings'].append(
                    '"license_resource" is a deprecated attribute')
        else:
            data = {'resource': license_url}
        if len(license) > 1:
            data['identifier'] = license[1][0:-1]
        else:
            if acdd_license_id not in ncin.ncattrs():
                self.missing_attributes['warnings'].append(
                    '%s is a recommended attribute' % acdd_license_id
                )
                if old_version:
                    data['identifier'] = ncin.license
            else:
                data['identifier'] = getattr(ncin, acdd_license_id)
        return data

    def to_mmd(self, collection=None, checksum_calculation=False, mmd_yaml=None,
               *args, **kwargs):
        """Method for parsing and mapping NetCDF attributes to MMD.

        Some times the data producers have missed some required elements
        in their netCDF attributes. These are possible to override by
        adding certain optional keyword arguments (see below parameter
        list).

        Parameters
        ----------
        collection : list or str, default ['ADC', 'METNCS']
            Specify the MMD collection for which you are harvesting to.
        checksum_calculation : bool, default False
            True if the file checksum should be calculated.
        mmd_yaml : str, optional
            The yaml file to use for translation from ACDD to MMS.
        time_coverage_start : str, optional
            The start date and time, in iso8601 format, for data
            collection or model coverage.
        time_coverage_end   : str, optional
            The end date and time, in iso8601 format, for data
            collection or model coverage.
        geographic_extent_rectangle : dict, optional
            The geographic extent of the datasets defined as a rectangle
            in lat/lon projection. The extent is defined using the
            following child elements: {
                'geospatial_lat_max': geospatial_lat_max
                    - The northernmost point covered by the dataset.
                'geospatial_lat_min': geospatial_lat_min
                    - The southernmost point covered by the dataset.
                'geospatial_lon_min': geospatial_lon_min
                    - The easternmost point covered by the dataset.
                'geospatial_lon_max': geospatial_lon_max
                    - The westernmost point covered by the dataset.
            }

        This list can be extended but requires some new code...
        """
        if collection is not None and type(collection) not in [list, str]:
            raise ValueError('collection must be of type str or list')

        # kwargs that were not added in the function def:
        time_coverage_start = kwargs.pop('time_coverage_start', '')
        time_coverage_end = kwargs.pop('time_coverage_end', '')
        geographic_extent_rectangle = kwargs.pop('geographic_extent_rectangle', '')

        # Open netcdf file for reading
        ncin = self.read_nc_file(self.netcdf_product)

        self.check_attributes_not_empty(ncin)

        # Get list of MMD elements
        if mmd_yaml is None:
            mmd_yaml = yaml.load(
                resource_string(self.__module__.split('.')[0], 'mmd_elements.yaml'),
                Loader=yaml.FullLoader
            )

        mmd_docs = 'https://htmlpreview.github.io/?https://github.com/metno/mmd/blob/master/' \
                   'doc/mmd-specification.html#collection-keywords'
        default_collections = ['ADC', 'METNCS']
        if collection is None:
            logging.warning('Using default values [%s, %s] for the MMD collection field. '
                            'Please, specify other collection(s) if this is wrong. Valid '
                            'collections are provided in the MMD documentation (%s)'
                            % (default_collections[0], default_collections[1], mmd_docs))
            self.metadata['collection'] = default_collections
        else:
            self.metadata['collection'] = [collection]

        # handle tricky exceptions first
        self.metadata['metadata_identifier'] = self.get_metadata_identifier(
            mmd_yaml.pop('metadata_identifier'), ncin, **kwargs
        )
        self.metadata['data_center'] = self.get_data_centers(mmd_yaml.pop('data_center'), ncin)
        self.metadata['last_metadata_update'] = self.get_metadata_updates(
            mmd_yaml.pop('last_metadata_update'), ncin
        )
        self.metadata['title'] = self.get_titles(mmd_yaml.pop('title'), ncin)
        self.metadata['abstract'] = self.get_abstracts(mmd_yaml.pop('abstract'), ncin)
        if time_coverage_start:
            tt, msg = normalize_iso8601(time_coverage_start)
            if tt is None:
                self.missing_attributes['errors'].append(
                    "time_coverage_start must be in ISO8601 format: "
                    "YYYY-mm-ddTHH:MM:SS<second fraction><time zone>.")
            self.metadata['temporal_extent'] = {'start_date': time_coverage_start}
            if time_coverage_end:
                tt, msg = normalize_iso8601(time_coverage_end)
                if tt is None:
                    self.missing_attributes['errors'].append(
                        "time_coverage_end must be in ISO8601 format: "
                        "YYYY-mm-ddTHH:MM:SS<second fraction><time zone>.")
                self.metadata['temporal_extent']['end_date'] = time_coverage_end
            mmd_yaml.pop('temporal_extent')
        else:
            self.metadata['temporal_extent'] = self.get_temporal_extents(
                mmd_yaml.pop('temporal_extent'), ncin
            )

        self.metadata['personnel'] = self.get_personnel(mmd_yaml.pop('personnel'), ncin)
        self.metadata['keywords'] = self.get_keywords(mmd_yaml.pop('keywords'), ncin)
        self.metadata['project'] = self.get_projects(mmd_yaml.pop('project'), ncin)
        self.metadata['platform'] = self.get_platforms(mmd_yaml.pop('platform'), ncin)
        self.metadata['dataset_citation'] = self.get_dataset_citations(
            mmd_yaml.pop('dataset_citation'), ncin)
        self.metadata['related_dataset'] = self.get_related_dataset(
            mmd_yaml.pop('related_dataset'), ncin)
        self.metadata['related_information'] = self.get_related_information(
            mmd_yaml.pop('related_information'), ncin)
        # Optionally add geographic extent
        self.metadata['geographic_extent'] = {}
        if geographic_extent_rectangle:
            self.metadata['geographic_extent']['rectangle'] = {
                'srsName': 'EPSG:4326',
                'north': geographic_extent_rectangle['geospatial_lat_max'],
                'south': geographic_extent_rectangle['geospatial_lat_min'],
                'west': geographic_extent_rectangle['geospatial_lon_min'],
                'east': geographic_extent_rectangle['geospatial_lon_max'],
            }
            mmd_yaml['geographic_extent'].pop('rectangle')
        else:
            self.metadata['geographic_extent']['rectangle'] = \
                self.get_geographic_extent_rectangle(
                    mmd_yaml['geographic_extent'].pop('rectangle'), ncin)
        # Check for geographic_extent/polygon
        polygon = self.get_geographic_extent_polygon(
            mmd_yaml['geographic_extent'].pop('polygon'), ncin
        )
        if polygon:
            self.metadata['geographic_extent']['polygon'] = polygon
        mmd_yaml.pop('geographic_extent')

        # Get use_constraint data
        self.metadata['use_constraint'] = self.get_license(mmd_yaml.pop('use_constraint'), ncin)

        # Data access should not be read from the netCDF-CF file
        mmd_yaml.pop('data_access')
        # Add OPeNDAP data_access if "netcdf_product" is OPeNDAP url
        rm_file_for_checksum_calculation = False
        if 'dodsC' in self.netcdf_product:
            self.metadata['data_access'] = self.get_data_access_dict(ncin, **kwargs)
            resource = ''
            for access in self.metadata['data_access']:
                if access['type'] == 'HTTP':
                    resource = access['resource']
            logging.info('Downloading NetCDF file to calculate checksum...')
            file_for_checksum_calculation = wget.download(resource)
            rm_file_for_checksum_calculation = True
        else:
            self.metadata['data_access'] = []
            file_for_checksum_calculation = self.netcdf_product

        file_size = pathlib.Path(file_for_checksum_calculation).stat().st_size / (1024 * 1024)

        for key in mmd_yaml:
            self.metadata[key] = self.get_acdd_metadata(mmd_yaml[key], ncin, key)

        # Set storage_information

        file_location = self.netcdf_product

        self.metadata['storage_information'] = {
            'file_name': os.path.basename(self.netcdf_product),
            'file_location': file_location,
            'file_format': 'NetCDF-CF',
            'file_size': '%.2f'%file_size,
            'file_size_unit': 'MB',
        }

        if checksum_calculation:
            hasher = FileHash('md5', chunk_size=1048576)
            fchecksum = hasher.hash_file(file_for_checksum_calculation)

            self.metadata['storage_information']['checksum'] = fchecksum
            self.metadata['storage_information']['checksum_type'] = '%ssum' % \
                                                                    hasher.hash_algorithm

        if rm_file_for_checksum_calculation:
            os.remove(file_for_checksum_calculation)

        self.check_conventions(ncin)

        if len(self.missing_attributes['warnings']) > 0:
            warnings.warn('\n\t'+'\n\t'.join(self.missing_attributes['warnings']))
        if len(self.missing_attributes['errors']) > 0:
            raise AttributeError('\n\t'+'\n\t'.join(self.missing_attributes['errors']))

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
        if add_wms_data_access:  # and 2D dataset...?
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
