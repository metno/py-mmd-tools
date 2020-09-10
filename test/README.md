To handle the path to the needed file and to avoid to copy files across repositories the configuration library confuse is used.
The "confuse" library is used to pass the path string for static files consumed in the test.

From the confuse documentation:

On Linux systems, by default, confuse reads a configuration file from:
$HOME/.config/appname/config.yaml # in this code 'mdtool' is used as 'appname'
The confuse configuration file uses yaml syntax, an example is provided below:
paths:
    reference_mmd: 'path/to/reference_mmd.xml'
    reference_iso: 'path/to/reference_iso.xml'
    mmd2isocsw: 'path/to/mmd-to-iso.xsl'
    mmd_xsd: 'path/to/mmd.xsd'
    logs: './logs/'
Consult the confuse documentation for more details. --

If you do not want (or can not) use the 'confuse' library:

replace the values of:
reference_mmd
reference_iso
mmd2iso_xslt
 with the path strings to the files provided by your testing environment - e.g.: 
reference_mmd='path/to/reference_mmd.xml'
reference_iso='path/to/reference_iso.xml'
mmd2isocsw='path/to/mmd-to-iso.xsl'           

comment/remove the following lines:
import confuse
config = confuse.Configuration('mmdtool', __name__)
example file used in this test are from the mmd_repository, for convenience can be also found grouped as gist https://gist.github.com/934db4d3cf4e7a52985a3e231e0d36cf)

To run the test, run the following command from the test directory.

python3 -m unittest test_mmd_to_iso.py
make sure your environment has access to a configuration file (or replace the path as described above) and that the module is importable
