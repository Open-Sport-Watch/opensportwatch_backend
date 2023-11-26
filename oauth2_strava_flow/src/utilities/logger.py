import time, os, sys
import logging
import logging.handlers

def log_setup(file_path):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # create formatter
    formatter = logging.Formatter('[%(asctime)s,%(msecs)03d] [%(name)s] [%(levelname)s] %(message)s','%Y-%m-%d %H:%M:%S')
    formatter.converter = time.gmtime  # if you want UTC time

    # add stout
    log_handler_stdout = logging.StreamHandler(sys.stdout)
    log_handler_stdout.setFormatter(formatter)
    logger.addHandler(log_handler_stdout)

    # add file
    log_handler_file = logging.handlers.WatchedFileHandler(file_path)
    log_handler_file.setFormatter(formatter)
    logger.addHandler(log_handler_file)

    # manage external logging
    logging.getLogger('timeloop').propagate = False

def info (msg,app=''):
    if app:
        logging.getLogger(f'{app}').info(msg)
    else:
        logging.info(msg)

def warn (msg,app=''):
    if app:
        logging.getLogger(f'{app}').warning(msg)
    else:
        logging.warning(msg)

def error (msg,app=''):
    if app:
        logging.getLogger(f'{app}').error(msg)
    else:
        logging.error(msg)