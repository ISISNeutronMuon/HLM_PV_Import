import sys
import os
import logging.config
from ServiceManager.constants import MANAGER_LOGS_FILE


# Setup log file
if not os.path.exists(MANAGER_LOGS_FILE):
    if not os.path.exists(os.path.dirname(MANAGER_LOGS_FILE)):
        os.makedirs(os.path.dirname(MANAGER_LOGS_FILE))
    open(MANAGER_LOGS_FILE, 'a').close()


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
        }
    },
    'loggers': {
        'manager_log': {
            'handlers': ['console', 'manager_file'],
            'level': 'INFO'
        }
    }
}
logging.config.dictConfig(LOGGING_CONFIG)

# Create logger
manager_logger = logging.getLogger('manager_log')
