import confuse
from confuse.exceptions import NotFoundError
import logging

def get_logpath(config_name='mmdtool'):
    try:
        config = confuse.Configuration(config_name, __name__)
        logfilepath = config["paths"]["logs"].get()
    except NotFoundError:
        logfilepath = "./logs/"
    if not pathlib.Path(logfilepath).exists():
        pathlib.Path(logfilepath).mkdir(parents=True, exist_ok=True)
    return logfilepath


def setup_log(name, logtype='stream'):
    ''' logtype = [file, stream]'''
    logger = logging.getLogger(name)  # > set up a new name for a new logger
    logger.setLevel(logging.DEBUG)  # here is the missing line
    log_format = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    if logtype=='file':
        # filehandler
        logfilepath = get_logpath()
        filename = pathlib.Path(logfilepath, f"{name}.log")
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