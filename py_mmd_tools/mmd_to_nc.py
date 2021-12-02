"""
Tool for parsing an XML metadata file, following the MET Norway Metadata specification (MMD),
 and updating an NetCDF file, following the Attribute Convention for Data Discovery (ACDD).

License:

This file is part of the py-mmd-tools repository
<https://github.com/metno/py-mmd-tools>.

py-mmd-tools is licensed under the Apache License 2.0
<https://github.com/metno/py-mmd-tools/blob/master/LICENSE>
"""

import netCDF4 as nc
import lxml.etree as ET


class Mmd_to_nc(object):

    def __init__(self, mmd_product, nc_file):
        """Class for updating a NetCDF file that is compliant with the CF-conventions and ACDD
        from an MMD XML file.
        Args:
            mmd_product (str): Input MMD xml file.
            nc_file (pathlib): Nc file to update.
        """
        super(Mmd_to_nc, self).__init__()
        self.nc = nc_file
        self.mmd = mmd_product
        return

    def update_nc(self):
        """
        Update a netcdf file global attributes.
        """

        tree = ET.parse(self.mmd)

        # Open netcdf file for reading and appending
        with nc.Dataset(self.nc, 'a') as f:

            acdd = {}
            ns = {'xml': 'http://www.w3.org/XML/1998/namespace',
                  'mmd': 'http://www.met.no/schema/mmd'}

            # ACDD - Highly recommended attributes

            acdd['title'] = tree.find('mmd:title[@xml:lang="en"]', namespaces=ns).text
            acdd['summary'] = tree.find('mmd:abstract[@xml:lang="en"]', namespaces=ns).text
            acdd['Conventions'] = ','.join(['ACDD-1.3', f.Conventions])
            keywords = tree.findall('mmd:keywords', namespaces=ns)
            list_keywords = []
            list_vocabularies = []
            for k in keywords:
                list_keywords.append(k.find('mmd:keyword', namespaces=ns).text)
                list_vocabularies.append(k.get('vocabulary'))
            acdd['keywords'] = ','.join(list_keywords)
            acdd['keywords_vocabulary'] = ','.join(list_vocabularies)

            # ACDD - Recommended attributes

            # Not in mmd:
            # Comment / acknowledgement / History / standard_name_vocabulary / publisher_email /
            # publisher_url

            id = tree.find('mmd:metadata_identifier', namespaces=ns).text
            if ':' in id:
                acdd['id'] = id.split(':')[1]
                acdd['naming_authority'] = id.split(':')[0]
            else:
                acdd['id'] = id

            if tree.find('mmd:activity_type', namespaces=ns) is not None:
                activities = tree.findall('mmd:activity_type', namespaces=ns)
                sources = []
                for a in activities:
                    sources.append(a.text)
                acdd['source'] = ','.join(sources)

            if tree.find('mmd:operational_status', namespaces=ns) is not None:
                acdd['processing_level'] = tree.find('mmd:operational_status', namespaces=ns).text

            if tree.find('mmd:use_constraint', namespaces=ns) is not None:
                acdd['license'] = tree.find('mmd:use_constraint/mmd:identifier',
                                            namespaces=ns).text

            if tree.find('mmd:dataset_citation/mmd:publication_date', namespaces=ns) is not None:
                acdd['date_created'] = tree.find('mmd:dataset_citation/mmd:publication_date',
                                                 namespaces=ns).text

            personnel = tree.findall('mmd:personnel', namespaces=ns)
            list_name = []
            list_email = []
            list_institution = []
            for p in personnel:
                list_name.append(p.find('mmd:name', namespaces=ns).text)
                list_email.append(p.find('mmd:email', namespaces=ns).text)
                list_institution.append(p.find('mmd:organisation', namespaces=ns).text)
            acdd['creator_name'] = ','.join(list_name)
            acdd['creator_email'] = ','.join(list_email)
            acdd['creator_institution'] = ','.join(list_institution)

            if tree.find('mmd:data_center/mmd:data_center_name/mmd:long_name',
                         namespaces=ns) is not None:
                acdd['institution'] = tree.find(
                    'mmd:data_center/mmd:data_center_name/mmd:long_name',
                    namespaces=ns).text

            if len(tree.findall('mmd:project', namespaces=ns)) > 0:
                project_list = []
                for p in tree.findall('mmd:project', namespaces=ns):
                    project_list.append(p.find('mmd:long_name', namespaces=ns).text)
                acdd['project'] = ','.join(project_list)

            if tree.find('mmd:dataset_citation/mmd:author', namespaces=ns) is not None:
                acdd['publisher_name'] = tree.find('mmd:dataset_citation/mmd:author',
                                                   namespaces=ns).text

            rectangle = tree.find('mmd:geographic_extent/mmd:rectangle', namespaces=ns)
            acdd['geospatial_lat_max'] = rectangle.find('mmd:north', namespaces=ns).text
            acdd['geospatial_lat_min'] = rectangle.find('mmd:south', namespaces=ns).text
            acdd['geospatial_lon_max'] = rectangle.find('mmd:east', namespaces=ns).text
            acdd['geospatial_lon_min'] = rectangle.find('mmd:west', namespaces=ns).text

            temporal_extent = tree.find('mmd:temporal_extent', namespaces=ns)
            acdd['time_coverage_start'] = temporal_extent.find('mmd:start_date',
                                                               namespaces=ns).text
            if temporal_extent.find('mmd:end_date', namespaces=ns) is not None:
                acdd['time_coverage_end'] = temporal_extent.find('mmd:end_date',
                                                                 namespaces=ns).text

            # Add all global metadata to netcdf at once
            f.setncatts(acdd)

        return
