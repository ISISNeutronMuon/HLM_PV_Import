import os
import sys
import logging.config
from HLM_PV_Import.settings import LoggingFiles


def setup_log_file(log_path):
    if not os.path.exists(log_path):
        if not os.path.exists(os.path.dirname(log_path)):
            os.makedirs(os.path.dirname(log_path))
        open(log_path, 'a').close()


LOG_FILES = {
    'error': LoggingFiles.ERR_LOG,
    'db': LoggingFiles.DB_LOG,
    'pvs': LoggingFiles.PVS_LOG,
    'service': LoggingFiles.SRV_LOG
}

for file_path in LOG_FILES.values():
    setup_log_file(file_path)

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
        'err_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': LOG_FILES['error'],
            'when': 'midnight',
            'interval': 1,
            'formatter': 'verbose',
            'delay': True
        },
        'db_file': {
            'level': 'INFO',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': LOG_FILES['db'],
            'when': 'midnight',
            'interval': 1,
            'formatter': 'verbose',
            'delay': True
        },
        'pvs_file': {
            'level': 'INFO',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': LOG_FILES['pvs'],
            'when': 'midnight',
            'interval': 1,
            'formatter': 'verbose',
            'delay': True
        },
        'service_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_FILES['service'],
            'maxBytes': 10*1024**2,
            'backupCount': 15,
            'formatter': 'verbose',
            'delay': True
        }
    },
    'loggers': {
        'log': {
            'handlers': ['console', 'err_file', 'service_file'],
            'level': 'DEBUG'
        },
        'db': {
            'handlers': ['db_file', 'err_file'],
            'level': 'DEBUG',
            'propagate': False
        },
        'pv': {
            'handlers': ['pvs_file', 'err_file'],
            'level': 'DEBUG',
            'propagate': False
        },
        'exc': {
            'handlers': ['err_file'],
            'level': 'ERROR',
            'propagate': False
        }
    }
}
logging.config.dictConfig(LOGGING_CONFIG)

# Create loggers
logger = logging.getLogger('log')
db_logger = logging.getLogger('db')
pv_logger = logging.getLogger('pv')
exc_logger = logging.getLogger('exc')


def log_exception(type_, value, traceback):
    """ Log unhandled exceptions """
    exc_logger.error("Exception occurred", exc_info=(type_, value, traceback))
