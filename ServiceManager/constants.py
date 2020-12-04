import os
import sys

VER = '1.0.0'
B_DATE = '10 November 2020'

if getattr(sys, 'frozen', False):
    # BASE_PATH = os.path.dirname(sys.executable)
    # noinspection PyProtectedMember
    # noinspection PyUnresolvedReferences
    BASE_PATH = sys._MEIPASS
else:
    BASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)))

# region Assets & Layouts
gui_dir = os.path.join(BASE_PATH, 'GUI')
icon_path = os.path.join(gui_dir, 'assets', 'icon.svg')
about_logo_path = os.path.join(gui_dir, 'assets', 'isis-logo.png')
main_window_ui = os.path.join(gui_dir, 'layouts', 'MainWindow.ui')
about_ui = os.path.join(gui_dir, 'layouts', 'about.ui')
db_settings_ui = os.path.join(gui_dir, 'layouts', 'DBSettings.ui')
general_settings_ui = os.path.join(gui_dir, 'layouts', 'GeneralSettings.ui')
ca_settings_ui = os.path.join(gui_dir, 'layouts', 'CASettings.ui')
service_path_dlg_ui = os.path.join(gui_dir, 'layouts', 'ServicePathDialog.ui')
config_entry_ui = os.path.join(gui_dir, 'layouts', 'ConfigEntry.ui')
# endregion


# Directory for storing the manager app settings and persistent data
MANAGER_SETTINGS_DIR = os.path.join(os.getenv('LOCALAPPDATA'), 'HLM Service Manager', '')
MANAGER_SETTINGS_FILE = os.path.join(MANAGER_SETTINGS_DIR, 'settings.ini')
MANAGER_LOGS_DIR = os.path.join(MANAGER_SETTINGS_DIR, 'logs')
MANAGER_LOGS_FILE = os.path.join(MANAGER_LOGS_DIR, 'HLM_ErrorLog.log')
SERVICE_SETTINGS_FILE_NAME = 'settings.ini'


# region Settings Files Templates
MANAGER_SETTINGS_TEMPLATE = {
    'Service': ['Directory'],
    'General': ['AutoPVConnectionCheck'],
    'Defaults': ['MeasurementsUpdateInterval']
}

SERVICE_SETTINGS_TEMPLATE = {
    'ChannelAccess': ['EPICS_CA_ADDR_LIST', 'ConnectionTimeout', 'PvStaleAfter', 'PV_PREFIX', 'PV_DOMAIN'],
    'PVImport': ['LoopTimer'],
    'PVConfig': ['FILE'],
    'HeRecoveryDB': ['Host', 'Name', 'DBObjectName', 'DBObjectType'],
    'Service': ['Name', 'DisplayName', 'Description'],
    'Logging': ['DirectoryPath']
}
# endregion
