# For Jenkins

import configparser
import os

from service_manager.utilities import setup_settings_file
from service_manager.constants import SERVICE_SETTINGS_TEMPLATE

if __name__ == '__main__':
    settings_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '', 'settings.ini')
    if not os.path.exists(settings_path):
        setup_settings_file(path=settings_path,
                            template=SERVICE_SETTINGS_TEMPLATE, parser=configparser.ConfigParser())
