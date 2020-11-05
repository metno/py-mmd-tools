import argparse
import os
import pathlib
import sys
import parmap
from lxml.etree import XMLSyntaxError
from xml_utils import xml_translate

"""
Script to run the xmlc onversion tools

 License:
     This file is part of the S-ENDA-Prototype repository (https://github.com/metno/py-mmd-tools).
     S-ENDA-Prototype is licensed under GPL-3.0 (https://github.com/metno/py-mmd-tools/blob/master/LICENSE)

usage: xmlconverter.py [-h] -i INPUT_DIR [-o OUTPUT_DIR] -t INPUT_XSLT
                       [-r RECOVER_CONVERSION] [-p PARALLEL_CONVERSION]
example: python3 xmlconverter.py -i metadata/nbs_mmdv2/ -t mmd2iso.xsl -p True -r True -o metadata/nbs_iso
"""


def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ("yes", "true", "t", "y", "1"):
        return True
    elif v.lower() in ("no", "false", "f", "n", "0"):
        return False
    else:
        raise argparse.ArgumentTypeError("Boolean value expected.")
    
def filelist(directory):
    print('os.walk("%s")' % directory)
    xml_files = []
    for subdir, dirs, files in os.walk(directory):
        for file in files:
            # print('File: %s' %file)
            file_path = subdir + os.sep + file
            if file_path.endswith(".xml"):
                xml_files.append(file_path)
    return xml_files

def translate_and_write(xml_file, xslt, outdir="/tmp"):
    pathlib.Path(outdir).mkdir(parents=True, exist_ok=True)
    if not os.path.isfile(xslt):
        raise Exception("XSLT file is missing: %s" % xslt)
    outputfile = pathlib.PurePosixPath(outdir).joinpath(
        pathlib.PurePosixPath(xml_file).name
    )
    xml_translate(
        xml_file=xml_file,
        outputfile=outputfile,
        xslt=xslt,
    )


def main(metadata, xslt, outdir, recover=False, parallel=False):
    if not recover:
        xmlfiles = filelist(metadata)
    else:
        xmlfiles = recover_task(sourcedir=metadata, outdir=outdir, parallel=parallel)
    print(f"Sprocessing {len(xmlfiles)} files")
    if parallel is True:
        print(f'parallel: {parallel}')
        parmap.map(
            translate_and_write,
            xmlfiles,
            xslt=xslt,
            outdir=outdir,
            pm_pbar=False,
        )
    else:
        for i in xmlfiles:
            try:
                translate_and_write(xml_file=i, xslt=xslt, outdir=outdir)
            except XMLSyntaxError as e:
                print(f"failed on: {i} - {e.message}")


def check_record(record, tobedone):
    """[Returns a filepath string is the file name is present in the input list]
    Args:
        record ([str]): [filepath]
        tobedone ([list]): [list of filenames]
    Returns:
        [str]: [filepath]
    """
    if pathlib.Path(record).stem in tobedone:
        return record


def recover_task(sourcedir, outdir, parallel=False):
    """[Return a list of filenames which are present in the sourcedir tree but not in outdir.]
    Args:
        sourcedir ([str]): [filepath to directory]
        outdir ([str]): [filepath to directory]
        parallel ([bool]): [True to performe the operation using multicore parallel processing]
    Returns:
        [list]: [list of strings]
    """
    total = filelist(sourcedir)
    already_done = filelist(outdir)
    total_stem = [pathlib.Path(i).stem for i in total]
    already_done_stem = [pathlib.Path(i).stem for i in already_done]
    tobedone_stem = list(set(total_stem) - set(already_done_stem))
    if parallel:
        print(f'parallel: {parallel}')
        tobedone = parmap.map(check_record, total, tobedone_stem, pm_pbar=False)
    else:
        tobedone = [check_record(i, tobedone_stem) for i in total]
    tobedone_files = [i for i in tobedone if i is not None]
    return tobedone_files


def parse_arguments():
    parser = argparse.ArgumentParser(description="Convert xml files using XSL Tranformation")
    parser.add_argument(
        "-i", "--input-dir", help="directory with input XML", required=True
    )
    parser.add_argument("-o", "--output-dir", help="outpout directory with ISO")
    parser.add_argument(
        "-t", "--input-xslt", help="input xslt translation file", required=True
    )
    parser.add_argument(
        "-r",
        "--recover-conversion",
        type=str2bool,
        nargs="?",
        const=False,
        help="recover a previously interrupted conversion",
        default=False,
        required=False,
    )
    parser.add_argument(
        "-p",
        "--parallel-conversion",
        type=str2bool,
        nargs="?",
        const=False,
        help="recover a previously interrupted conversion",
        default=False,
        required=False,
    )
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = parse_arguments()
    main(
        metadata=args.input_dir,
        xslt=args.input_xslt,
        outdir=args.output_dir,
        recover=args.recover_conversion,
        parallel=args.parallel_conversion,
    )
