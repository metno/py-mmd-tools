#!/usr/bin/env python3

"""
Script to generate a yaml file containing ACDD requirements specific to the Arctic Data Centre.
This new acdd_elements.yaml file is generated using the more general mmd_elements.yaml file.

License:

This file is part of the py-mmd-tools repository
<https://github.com/metno/py-mmd-tools>.

py-mmd-tools is licensed under the Apache License 2.0
<https://github.com/metno/py-mmd-tools/blob/master/LICENSE>

Each entry in adc_elements.yaml is structured as follows:

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

Example:
    python -m py_mmd_tools.script.mmd2acdd
"""

import os
import yaml
from py_mmd_tools import mmd_to_acdd

if __name__ == "__main__":
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Path to the mmd_elements.yaml file
    mmd_elements_path = os.path.join(script_dir, "../mmd_elements.yaml")

    # Read the mmd_elements.yaml file
    with open(mmd_elements_path, 'r') as f:
        mmd_data = yaml.safe_load(f)

    # Extract ACDD attributes
    acdd_attributes = mmd_to_acdd.extract_acdd_attributes(mmd_data)

    # Create the output dictionary
    output = {}

    for attr, data in acdd_attributes.items():
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

    # Path to the acdd_elements.yaml file
    acdd_elements_path = os.path.join(script_dir, "../acdd_elements.yaml")

    # Write the output to acdd_elements.yaml
    with open(acdd_elements_path, 'w') as f:
        yaml.dump(output, f, sort_keys=False, default_flow_style=False)

    print("acdd_elements.yaml has been created successfully in the py_mmd_tools directory.")
