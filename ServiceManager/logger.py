"""
For logging the service manager, write stdout output to a file.
"""
import sys
import logging
import logging.handlers
import os
from ServiceManager.settings import Settings


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

    log_dir = Settings.Manager.get_logs_dir_path()
    log_file = Settings.Manager.get_error_log_path()

    if not os.path.exists(log_file):
        if not os.path.exists(log_dir):  # If settings directory does not exist either, create it too
            os.makedirs(log_dir)
        with open(log_file, 'w') as f:
            pass

    logger_ = logging.getLogger()
    logger_.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.NOTSET)
    handler.setFormatter(formatter)
    logger_.addHandler(handler)

    handler = logging.handlers.RotatingFileHandler(log_file, maxBytes=10*1024**2, backupCount=10)
    handler.setLevel(logging.NOTSET)
    handler.setFormatter(formatter)
    logger_.addHandler(handler)

    return logger_


def log_exception(type_, value, traceback):
    """ Log unhandled exceptions """
    logging.error("Unhandled exception occurred", exc_info=(type_, value, traceback))


logger = get_logger()

sys.stdout = StreamToLogger(logger)
