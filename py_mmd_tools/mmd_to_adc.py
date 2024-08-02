#!/usr/bin/env python3

"""
This script generates a yaml file contatining requiremnents specific to the Arctic Data Centre.
This new yaml file is generated using the more general mmd_elements.yaml file.

License:

This file is part of the py-mmd-tools repository
<https://github.com/metno/py-mmd-tools>.

py-mmd-tools is licensed under the Apache License 2.0
<https://github.com/metno/py-mmd-tools/blob/master/LICENSE>

Each entry in adc_elements.yaml is strucutred as follows:

attribute name:
    description:
    help:
    format:
    limits: # Where applicable, such as for geospatial_lat_min
      min:
      max:
    options: # Where applicable
      - option 1
      - option 2
      - option 3
      - option 4
    requirement_level:
"""

import yaml
from collections import defaultdict


def extract_adc_attributes(data, prefix=''):
    """
    Recursively extract attributes relevant for the Arctic Data Centre (ADC)
    from a nested dictionary or list structure.

    This function searches for 'acdd' and 'acdd_ext' keys in the input data structure
    and extracts attributes that have both 'format' and 'requirement_level' keys.

    Parameters
    ----------
    data : dict or list
        The input data structure to search for ADC attributes.
    prefix : str, optional
        A string prefix to prepend to extracted attribute names, used for
        handling nested structures. Default is an empty string.

    Returns
    -------
    dict
        A dictionary of extracted ADC attributes. The keys are the attribute
        names (prefixed if nested), and the values are dictionaries containing
        the attribute's metadata (description, format, requirement_level, etc.).
    """
    attributes = defaultdict(dict)

    if isinstance(data, dict):
        for key, value in data.items():
            if key in ['acdd', 'acdd_ext']:
                for attr, attr_data in value.items():
                    if 'format' in attr_data and 'requirement_level' in attr_data:
                        full_key = f"{prefix}{attr}" if prefix else attr
                        final_key = full_key.split('.')[-1]
                        attributes[final_key] = attr_data
            else:
                nested_attributes = extract_adc_attributes(value, f"{prefix}{key}.")
                attributes.update(nested_attributes)
    elif isinstance(data, list):
        for item in data:
            nested_attributes = extract_adc_attributes(item, prefix)
            attributes.update(nested_attributes)

    return attributes


# Read the mmd_elements.yaml file
with open('mmd_elements.yaml', 'r') as f:
    mmd_data = yaml.safe_load(f)

# Extract ADC attributes
ADC_attributes = extract_adc_attributes(mmd_data)

# Create the output dictionary
output = {}

for attr, data in ADC_attributes.items():
    output[attr] = {
        "description": data.get("description", ""),
        "help": data.get("comment", ""),
        "format": data.get("format", ""),
        "requirement_level": data.get("requirement_level", "")
    }

    if "options" in data:
        output[attr]["options"] = data["options"]

    if "limits" in data:
        output[attr]["limits"] = data["limits"]

# Write the output to adc_elements.yaml
with open('adc_elements.yaml', 'w') as f:
    yaml.dump(output, f, sort_keys=False, default_flow_style=False)

print("adc_elements.yaml has been created successfully.")
