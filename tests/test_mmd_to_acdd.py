"""
License:

This file is part of the py-mmd-tools repository
<https://github.com/metno/py-mmd-tools>.

py-mmd-tools is licensed under the Apache License 2.0
<https://github.com/metno/py-mmd-tools/blob/master/LICENSE>
"""

import pytest
from py_mmd_tools.mmd_to_acdd import extract_acdd_attributes


@pytest.mark.py_mmd_tools
def test_extract_acdd_attributes_single_level_dict():
    """ Test that data is extracted as expected.
    """
    data = {
        'metadata_identifier': {
            'maxOccurs': '1',
            'minOccurs': '1',
            'acdd': {
                'id': {
                    'maxOccurs': '1',
                    'minOccurs': '1',
                    'comment': 'Required, and should be UUID. No repetition allowed.',
                    'description': (
                        'An identifier for the dataset, provided by and unique within its'
                        ' naming authority. '
                        'The combination of the "naming authority" and the "id" should be'
                        ' globally unique, but the '
                        'id can be globally unique by itself also. A uuid is recommended.'
                    ),
                    'format': 'text',
                    'requirement_level': 'Required if not hosted by MET'
                },
                'naming_authority': {
                    'maxOccurs': '1',
                    'minOccurs': '1',
                    'comment': 'Required. We recommend using reverse-DNS naming.'
                    ' No repetition allowed.',
                    'description': (
                        'The organisation that provides the initial id (see above)'
                        ' for the dataset. The naming authority should be uniquely '
                        'specified by this attribute. We recommend using reverse-DNS '
                        'naming for the naming authority.'
                    ),
                    'format': 'text',
                    'requirement_level': 'Required if not hosted by MET'
                }
            }
        },
        'alternate_identifier': {
            'maxOccurs': 'unbounded',
            'minOccurs': '0',
            'alternate_identifier': {
                'acdd_ext': {
                    'alternate_identifier': {
                        'comment': 'Alternative identifier for the dataset (but not DOI).'
                        ' Comma separated list.',
                        'separator': ',',
                        'description': (
                            'Alternative identifier for the dataset described by the metadata'
                            ' document in the form '
                            '<url> (<type>). This is used when datasets have multiple identifiers,'
                            ' e.g., depending on the framework through which the data is shared.'
                        )
                    }
                }
            },
            'alternate_identifier_type': None
        },
        'not_mmd.Conventions': {
            'maxOccurs': 'unbounded',
            'minOccurs': '0',
            'acdd': {
                'Conventions': {
                    'maxOccurs': '1',
                    'minOccurs': '1',
                    'comment': 'Required',
                    'description': (
                        'Required. A comma-separated string with names of the conventions '
                        'that are followed by the '
                        'dataset, e.g., "CF-1.10, ACDD-1.3".'
                    ),
                    'format': 'text',
                    'requirement_level': 'Required'
                }
            }
        },
        'not_mmd.history': {
            'maxOccurs': 'unbounded',
            'minOccurs': '0',
            'acdd': {
                'history': {
                    'maxOccurs': '1',
                    'minOccurs': '1',
                    'comment': 'Required',
                    'description': (
                        'Provides an audit trail for modifications to the original data. '
                        'This attribute is also in the NetCDF Users Guide '
                        '("This is a character array with a line for each invocation of a '
                        'program that has modified the dataset. '
                        'Well-behaved generic netCDF applications should '
                        'append a line containing date, time of day, user name, '
                        'program name and command arguments"). '
                        'To include a more complete description you can append a reference '
                        'to an ISO Lineage entity; '
                        'see NOAA EDM ISO Lineage guidance.'
                    ),
                    'format': 'text',
                    'requirement_level': 'Required'
                }
            }
        },
        'not_mmd.featureType': {
            'maxOccurs': 'unbounded',
            'minOccurs': '0',
            'acdd_ext': {
                'featureType': {
                    'maxOccurs': '1',
                    'minOccurs': '0',
                    'comment': (
                        'This is part of the CF conventions and is required when '
                        'submitting data according to the discrete sampling geometries '
                        'section of the CF conventions.'
                    ),
                    'description': (
                        'Specifies the type of discrete sampling geometry to which the '
                        'data in the scope of this attribute belongs, and implies that '
                        'all data variables in the scope of this attribute contain '
                        'collections of features of that type. All of the data variables '
                        'contained in a single file must be of the single feature type '
                        'indicated by the global featureType attribute. The value assigned '
                        'to the featureType attribute is case-insensitive; it must be one '
                        'of the string values listed in the left column of Table 9.1 in '
                        'https://cfconventions.org/Data/cf-conventions/cf-conventions-1.10/'
                        'cf-conventions.html#_features_and_feature_types[chapter 9, '
                        'Discrete Sampling Geometries, of the CF convention]. Note that a '
                        'dataset with the timeSeries feature type will be plottable with '
                        'the Bokeh tool available via its landing page at https://data.met.no, '
                        'e.g., https://bokeh.metsis-api.met.no/TS-Plot?url=https://thredds.met.no/'
                        'thredds/dodsC/met.no/observations/surface/80740/173/'
                        'reipa_surface_air_pressure.nc.'
                    ),
                    'format': 'text',
                    'options': [
                        'point', 'timeSeries', 'trajectory', 'profile',
                        'timeSeriesProfile', 'trajectoryProfile'
                    ],
                    'requirement_level': 'Recommended'
                }
            }
        }
    }

    expected_output = {
        'id': {
            'maxOccurs': '1',
            'minOccurs': '1',
            'comment': 'Required, and should be UUID. No repetition allowed.',
            'description': (
                'An identifier for the dataset, provided by and unique within '
                'its naming authority. The combination of the "naming authority" '
                'and the "id" should be globally unique, but the id can be globally '
                'unique by itself also. A uuid is recommended.'
            ),
            'format': 'text',
            'requirement_level': 'Required if not hosted by MET'
        },
        'naming_authority': {
            'maxOccurs': '1',
            'minOccurs': '1',
            'comment': 'Required. We recommend using reverse-DNS naming. No repetition allowed.',
            'description': (
                'The organisation that provides the initial id (see above) for the dataset. '
                'The naming authority should be uniquely specified by this attribute. '
                'We recommend using reverse-DNS naming for the naming authority.'
            ),
            'format': 'text',
            'requirement_level': 'Required if not hosted by MET'
        },
        'Conventions': {
            'maxOccurs': '1',
            'minOccurs': '1',
            'comment': 'Required',
            'description': (
                'Required. A comma-separated string with names of the conventions '
                'that are followed by the dataset, e.g., "CF-1.10, ACDD-1.3".'
            ),
            'format': 'text',
            'requirement_level': 'Required'
        },
        'history': {
            'maxOccurs': '1',
            'minOccurs': '1',
            'comment': 'Required',
            'description': (
                'Provides an audit trail for modifications to the original data. '
                'This attribute is also in the NetCDF Users Guide ("This is a '
                'character array with a line for each invocation of a program that '
                'has modified the dataset. Well-behaved generic netCDF applications '
                'should append a line containing date, time of day, user name, '
                'program name and command arguments"). To include a more complete '
                'description you can append a reference to an ISO Lineage entity; '
                'see NOAA EDM ISO Lineage guidance.'
            ),
            'format': 'text',
            'requirement_level': 'Required'
        }
    }

    result = extract_acdd_attributes(data)
    assert result == expected_output


@pytest.mark.py_mmd_tools
def test_extract_acdd_attributes_non_dict_or_list():
    """ Test that the dictionary doesn't change if a non list or dict type is given.
    """
    invalid_data = 42  # Using an integer this time
    expected_output = {}
    result = extract_acdd_attributes(invalid_data)
    assert result == expected_output


@pytest.mark.py_mmd_tools
def test_extract_acdd_attributes_empty():
    """Test how the function handles an empty dictionary or list."""
    empty_data = {}
    expected_output = {}
    result = extract_acdd_attributes(empty_data)
    assert result == expected_output


@pytest.mark.py_mmd_tools
def test_extract_acdd_attributes_missing_format():
    """Test how the function handles missing 'format' and 'requirement_level'."""
    data_missing_format = {
        'metadata_identifier': {
            'acdd': {
                'id': {
                    'comment': 'Required, and should be UUID. No repetition allowed.',
                    'description': 'An identifier for the dataset.',
                }
            }
        }
    }
    expected_output = {}
    result = extract_acdd_attributes(data_missing_format)
    assert result == expected_output


@pytest.mark.py_mmd_tools
def test_extract_acdd_attributes_missing_attribute():
    """Test that missing attributes (e.g., 'acdd') don't cause issues."""
    data_missing_acdd = {
        'metadata_identifier': {
            'maxOccurs': '1',
            'minOccurs': '1',
        }
    }
    expected_output = {}
    result = extract_acdd_attributes(data_missing_acdd)
    assert result == expected_output
