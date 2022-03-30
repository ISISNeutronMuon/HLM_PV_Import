import sys
import os
import logging.config
from service_manager.constants import MANAGER_LOGS_FILE, MANAGER_ERR_LOGS_FILE

# Setup log file
for logfile in [MANAGER_LOGS_FILE, MANAGER_ERR_LOGS_FILE]:
    if not os.path.exists(logfile):
        if not os.path.exists(os.path.dirname(logfile)):
            os.makedirs(os.path.dirname(logfile))
        open(logfile, 'a').close()


LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{asctime} {process:d}:{thread:d} {levelname} {module} \t {message}',
            'style': '{',
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
            'formatter': 'verbose'
        },
        'manager_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': MANAGER_LOGS_FILE,
            'maxBytes': 10*1024**2,
            'backupCount': 15,
            'formatter': 'verbose',
            'delay': True
        },
        'manager_err_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': MANAGER_ERR_LOGS_FILE,
            'maxBytes': 10 * 1024 ** 2,
            'backupCount': 15,
            'formatter': 'verbose',
            'delay': True
        }
    },
    'loggers': {
        'manager_log': {
            'handlers': ['console', 'manager_file'],
            'level': 'INFO'
        },
        'exc_manager_log': {
            'handlers': ['manager_err_file'],
            'level': 'ERROR'
        }
    }
}
logging.config.dictConfig(LOGGING_CONFIG)

# Create logger
manager_logger = logging.getLogger('manager_log')
exc_manager_logger = logging.getLogger('exc_manager_log')


def log_exception(type_, value, traceback):
    """ Log exception traceback """
    exc_manager_logger.error("Exception occurred", exc_info=(type_, value, traceback))
