This folder conatin executable python scripts. Please import from `py_mmd_tools`, and keep this code as simple as possible. Remember unit tests.
---

# checkMMD

## Usage via command line

```bash
python checkMMD.py [-h] -i INPUT -x XSD_MMD -l LOG_DIR 
```

The following arguments are required: 
* -i/--input XML file or directory containing XML files
* -x/--mmd-xsd MMD schema 

# mmd2iso

## Usage via command line

```bash
python mmd2iso-csw.py [-h] -i INPUT_MMD -o OUTPUT_ISO -t INPUT_XSLT [--xsd-mmd XSD_MMD] [--mmd-validation [MMD_VALIDATION]]
```

The following arguments are required: 

* -i/--input-mmd 
* -o/--output-iso 
* -t/--input-xslt


## Usage in a python session

```python
main(mmd_file='path_to_mmd_xml_file', 
        outputfile='path_to_output_file, 
        mmd2isocsw='path_to_xslt_translation_file_mmd_to_iso-csw',
        mmd_xsd_schema='path_to_mmd_xsd_validation_schema',
        mmd_validation='True')
```
