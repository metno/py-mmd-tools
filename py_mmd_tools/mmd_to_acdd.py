#!/usr/bin/env python3

"""
Tool for extracting ACDD requirements specific to the Arctic Data Centre.
Elements are extracted from the more general mmd_elements.yaml file.

License:

This file is part of the py-mmd-tools repository
<https://github.com/metno/py-mmd-tools>.

py-mmd-tools is licensed under the Apache License 2.0
<https://github.com/metno/py-mmd-tools/blob/master/LICENSE>
"""

from collections import defaultdict


def extract_acdd_attributes(data, prefix=''):
    """
    Recursively extract ACDD attributes
    from a nested dictionary or list structure.

    This function searches for 'acdd' keys in the input data structure
    and extracts attributes that have both 'format' and 'requirement_level' keys.

    Parameters
    ----------
    data : dict or list
        The input data structure to search for ACDD attributes.
    prefix : str, optional
        A string prefix to prepend to extracted attribute names, used for
        handling nested structures. Default is an empty string.

    Returns
    -------
    dict
        A dictionary of extracted ACDD attributes. The keys are the attribute
        names (prefixed if nested), and the values are dictionaries containing
        the attribute's metadata (description, format, requirement_level, etc.).
    """
    attributes = defaultdict(dict)

    if isinstance(data, dict):
        for key, value in data.items():
            if key == 'acdd':
                for attr, attr_data in value.items():
                    if 'format' in attr_data and 'requirement_level' in attr_data:
                        full_key = f"{prefix}{attr}" if prefix else attr
                        final_key = full_key.split('.')[-1]
                        attributes[final_key] = attr_data
            else:
                nested_attributes = extract_acdd_attributes(value, f"{prefix}{key}.")
                attributes.update(nested_attributes)
    elif isinstance(data, list):
        for item in data:
            nested_attributes = extract_acdd_attributes(item, prefix)
            attributes.update(nested_attributes)

    return attributes
