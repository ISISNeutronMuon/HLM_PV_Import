"""
For logging the script when running as a service, write stdout output to a file.
"""
import sys
import logging
import logging.handlers
import os.path


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

    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.join(os.path.dirname(os.path.abspath(__file__)))
    log_dir = os.path.join(base_path, 'logs', 'debug')
    log_file = os.path.join(log_dir, 'debug.log')

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
