import logging
import pathlib
import os

def get_logpath(logdirpath):
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
        return logger
    if logtype=='stream':
        # streamhandler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(log_format)
        logger.addHandler(ch)
        return logger