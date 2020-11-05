import sys
import logging
import logging.handlers
import os.path

formatter = logging.Formatter('%(asctime)s %(process)d:%(thread)d %(name)s %(levelname)-8s %(message)s')

app_path = os.path.dirname(sys.executable)
log_dir = os.path.join(app_path, 'logs', 'debug')
log_file = os.path.join(log_dir, 'debug.log')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.NOTSET)
handler.setFormatter(formatter)
logger.addHandler(handler)

handler = logging.handlers.RotatingFileHandler(log_file, maxBytes=10*1024**2, backupCount=10)
handler.setLevel(logging.NOTSET)
handler.setFormatter(formatter)
logger.addHandler(handler)

del handler, formatter


# hook to log unhandled exceptions
def except_hook(type_, value, traceback):
    logging.error("Unhandled exception occurred", exc_info=(type_, value, traceback))
    # Don't need another copy of traceback on stderr
    if old_excepthook != sys.__excepthook__:
        old_excepthook(type_, value, traceback)


old_excepthook = sys.excepthook
sys.excepthook = except_hook

del log_file, os


class StreamToLogger(object):
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


sys.stdout = StreamToLogger(logger)
