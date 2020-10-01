"""
Utility methods to create a logger.
 License:
     This file is part of the py-mmd-tools repository (https://github.com/metno/py-mmd-tools).
     licensed under the Apache License 2.0 (https://www.apache.org/licenses/LICENSE-2.0)
"""

import logging
import pathlib
import os

def get_logpath(logdirpath):
    """
    Args:
        logdirpath ([str]): [path to a directory where to store logs]
    Returns:
        [bool]: [return True if an existing and writable path to directory is provided] 
    """
    if not pathlib.Path(logdirpath).exists():
        try:
            pathlib.Path(logdirpath).mkdir(parents=True, exist_ok=True)
            return logdirpath
        except IOError:
            raise
    else:
        if os.access(logdirpath, os.W_OK):
            return logdirpath
        else:
            raise IOError


def setup_log(name, logdirpath, logtype='stream'):
    ''' logtype = [file, stream]'''
    logger = logging.getLogger(name)  # > set up a new name for a new logger
    logger.setLevel(logging.DEBUG)  # here is the missing line
    log_format = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    if logtype=='file':
        # filehandler
        logdirpath = get_logpath(logdirpath)
        filename = pathlib.Path(logdirpath, f"{name}.log")
        fh = logging.FileHandler(filename, mode='w', encoding='utf-8')
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(log_format)
        logger.addHandler(fh)
    if logtype=='stream':
        # streamhandler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(log_format)
        logger.addHandler(ch)
    return logger