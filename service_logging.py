import sys
import logging
import logging.handlers
import os.path

app_path = os.path.dirname(sys.executable)
log_dir_path = os.path.join(app_path, 'logs', 'debug')
log_file = os.path.join(log_dir_path, 'debug.log')
logger = logging.getLogger()
logger.setLevel(logging.INFO)
log_format = logging.Formatter('%(asctime)s %(process)d:%(thread)d %(name)s %(levelname)-8s %(message)s')
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.NOTSET)
handler.setFormatter(log_format)
logger.addHandler(handler)
handler = logging.handlers.RotatingFileHandler(log_file, maxBytes=1024**2, backupCount=5)
handler.setLevel(logging.NOTSET)
handler.setFormatter(log_format)
logger.addHandler(handler)
del handler, log_format


# hook to log unhandled exceptions
def except_hook(type_, value, traceback):
    logging.error("Unhandled exception occurred", exc_info=(type_, value, traceback))
    # Don't need another copy of traceback on stderr
    if old_excepthook != sys.__excepthook__:
        old_excepthook(type_, value, traceback)


old_excepthook = sys.excepthook
sys.excepthook = except_hook

del log_file, os
