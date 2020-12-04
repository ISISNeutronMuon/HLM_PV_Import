"""
For logging the service manager, write stdout output to a file.
"""
import sys
import logging
import logging.handlers
import os
from ServiceManager.constants import MANAGER_LOGS_FILE, MANAGER_LOGS_DIR


class StreamToLogger:
    """
    Fake file-like stream object that redirects writes to a logger instance.
    """

    def __init__(self, logger_):
        self.logger = logger_
        self.log_level = logger_.getEffectiveLevel()

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.log_level, line.rstrip())

    def flush(self):
        pass


def get_logger():
    formatter = logging.Formatter('%(asctime)s %(process)d:%(thread)d %(name)s %(levelname)-8s %(message)s')

    if not os.path.exists(MANAGER_LOGS_FILE):
        if not os.path.exists(MANAGER_LOGS_DIR):  # If settings directory does not exist either, create it too
            os.makedirs(MANAGER_LOGS_DIR)
        with open(MANAGER_LOGS_FILE, 'w') as f:
            pass

    logger_ = logging.getLogger()
    logger_.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.NOTSET)
    handler.setFormatter(formatter)
    logger_.addHandler(handler)

    handler = logging.handlers.RotatingFileHandler(MANAGER_LOGS_FILE, maxBytes=10*1024**2, backupCount=10)
    handler.setLevel(logging.NOTSET)
    handler.setFormatter(formatter)
    logger_.addHandler(handler)

    return logger_


def log_exception(type_, value, traceback):
    """ Log unhandled exceptions """
    logging.error("Unhandled exception occurred", exc_info=(type_, value, traceback))


logger = get_logger()

sys.stdout = StreamToLogger(logger)
