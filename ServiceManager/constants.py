import os
import sys
# noinspection PyUnresolvedReferences
from shared.const import *

# About
VER = '1.1.4'
B_DATE = '6 Jul 2021'
ISIS_URL = "https://www.isis.stfc.ac.uk/Pages/home.aspx"


if getattr(sys, 'frozen', False):
    # BASE_PATH = os.path.dirname(sys.executable)
    # noinspection PyProtectedMember
    # noinspection PyUnresolvedReferences
    BASE_PATH = sys._MEIPASS
else:
    BASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)))

# region Assets & Layouts
GUI_DIR_PATH = os.path.join(BASE_PATH, 'GUI')
ASSETS_PATH = os.path.join(GUI_DIR_PATH, 'assets')
icon_path = os.path.join(ASSETS_PATH, 'icon.svg')
about_logo_path = os.path.join(ASSETS_PATH, 'isis-logo.png')
loading_animation = os.path.join(ASSETS_PATH, 'loading.gif')
main_window_ui = os.path.join(GUI_DIR_PATH, 'layouts', 'MainWindow.ui')
about_ui = os.path.join(GUI_DIR_PATH, 'layouts', 'about.ui')
db_settings_ui = os.path.join(GUI_DIR_PATH, 'layouts', 'DBSettings.ui')
general_settings_ui = os.path.join(GUI_DIR_PATH, 'layouts', 'GeneralSettings.ui')
ca_settings_ui = os.path.join(GUI_DIR_PATH, 'layouts', 'CASettings.ui')
service_path_dlg_ui = os.path.join(GUI_DIR_PATH, 'layouts', 'ServicePathDialog.ui')
config_entry_ui = os.path.join(GUI_DIR_PATH, 'layouts', 'ConfigEntry.ui')
# endregion


# Directory for storing the manager app settings and persistent data
MANAGER_SETTINGS_DIR = os.path.join(os.getenv('LOCALAPPDATA'), 'HLM Service Manager', '')
MANAGER_SETTINGS_FILE = os.path.join(MANAGER_SETTINGS_DIR, 'settings.ini')
MANAGER_LOGS_DIR = os.path.join(MANAGER_SETTINGS_DIR, 'logs')
MANAGER_LOGS_FILE = os.path.join(MANAGER_LOGS_DIR, 'HLM_Manager.log')
MANAGER_ERR_LOGS_DIR = os.path.join(MANAGER_LOGS_DIR, 'error')
MANAGER_ERR_LOGS_FILE = os.path.join(MANAGER_ERR_LOGS_DIR, 'HLM_Manager_Error.log')
SERVICE_SETTINGS_FILE_NAME = 'settings.ini'


# region Settings Files Templates
MANAGER_SETTINGS_TEMPLATE = {
    'Service': {
        'Directory': ''
    },
    'General': {
        'AutoPVConnectionCheck': 'True',
        'AutoLoadExistingConfig': 'False'
    },
    'Defaults': {
        'MeasurementsUpdateInterval': '60'
    }
}

SERVICE_SETTINGS_TEMPLATE = {
    'ChannelAccess': {
        'EPICS_CA_ADDR_LIST': '',
        'ConnectionTimeout': '2',
        'PvStaleAfter': '7200',
        'AddStalePvs': 'False',
        'PV_PREFIX': '',
        'PV_DOMAIN': ''
    },
    'PVImport': {
        'LoopTimer': '5'
    },
    'HeRecoveryDB': {
        'Host': '',
        'Name': ''
    }
}
# endregion
