This folder conatin executable python scripts. Please import from `py_mmd_tools`, and keep this code as simple as possible. Remember unit tests.
---


# Usage via command line

```bash
python mmd2iso-csw.py [-h] -i INPUT_MMD -o OUTPUT_ISO -t INPUT_XSLT [--xsd-mmd XSD_MMD] [--mmd-validation [MMD_VALIDATION]]
```

The following arguments are required: 

* -i/--input-mmd 
* -o/--output-iso 
* -t/--input-xslt


# Usage in a python session

```python
main(mmd_file='path_to_mmd_xml_file', 
        outputfile='path_to_output_file, 
        mmd2isocsw='path_to_xslt_translation_file_mmd_to_iso-csw',
        mmd_xsd_schema='path_to_mmd_xsd_validation_schema',
        mmd_validation='True')
```

## Using the [`confuse`](https://pypi.org/project/confuse)  library
In this context `confuse` can be used to facilitate test and debug - `confuse` is used internally to guess the value for:
* module logs output folder (generates a log file foreach method being used) 
* guess the  path to the `xslt` transfromation file
* guess the  path to the `xsd` validation file

Assuming you have a configuration `config.yaml` file looking like:

```yaml
paths:
  mmd_xsd: "mmd.xsd"
  iso_xsd: "iso.xsd"
  mmd2isocsw: "mmd-to-iso.xsl"
  example_mmd: "sentinel-1-mmd.xml"
  logs: "./logs/"
```

Stored in the `confuse` default directory, which is (on linux):

`$HOME/.config/mmdtool/`

(Note: the project name `mmdtool` is the app name given in the call to fetch configuration options using the `confuse.Configuration` class)

### Example usage:

```python
import confuse             
config = confuse.Configuration('mmdtool', __name__) 
mmd_file = config['paths']['example_mmd'].get()\
mmd2isocsw = config['paths']['mmd2isocsw'].get()
outputfile = 'out.xml' 
```
