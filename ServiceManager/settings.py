import os
import sys
import configparser
import win32serviceutil

VER = '1.0.0'
B_DATE = '10 November 2020'

if getattr(sys, 'frozen', False):
    # BASE_PATH = os.path.dirname(sys.executable)
    # noinspection PyProtectedMember
    # noinspection PyUnresolvedReferences
    BASE_PATH = sys._MEIPASS
else:
    BASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)))


# Assets & Layouts
gui_dir = os.path.join(BASE_PATH, 'GUI')
icon_path = os.path.join(gui_dir, 'assets', 'icon.svg')
about_logo_path = os.path.join(gui_dir, 'assets', 'isis-logo.png')
main_window_ui = os.path.join(gui_dir, 'layouts', 'MainWindow.ui')
about_ui = os.path.join(gui_dir, 'layouts', 'about.ui')
db_settings_ui = os.path.join(gui_dir, 'layouts', 'DBSettings.ui')
general_settings_ui = os.path.join(gui_dir, 'layouts', 'GeneralSettings.ui')
ca_settings_ui = os.path.join(gui_dir, 'layouts', 'CASettings.ui')
service_path_dlg_ui = os.path.join(gui_dir, 'layouts', 'ServicePathDialog.ui')


# Directory for storing the manager app settings and persistent data
MANAGER_SETTINGS_DIR = os.path.join(os.getenv('LOCALAPPDATA'), 'HLM Service Manager', '')
MANAGER_SETTINGS_FILE = os.path.join(MANAGER_SETTINGS_DIR, 'settings.ini')
SERVICE_SETTINGS_FILE_NAME = os.path.join('settings.ini')

MANAGER_SETTINGS_TEMPLATE = {
    'Service': ['Directory']
}

SERVICE_SETTINGS_TEMPLATE = {
    'ChannelAccess': ['EPICS_CA_ADDR_LIST', 'ConnectionTimeout', 'PvStaleAfter', 'PV_PREFIX', 'PV_DOMAIN'],
    'PVImport': ['LoopTimer'],
    'PVConfig': ['FILE'],
    'HeRecoveryDB': ['Host', 'Name', 'DBObjectName', 'DBObjectType'],
    'Service': ['Name', 'DisplayName', 'Description'],
    'Logging': ['DirectoryPath']
}


def setup_settings_file(path: str, template: dict, parser: configparser.ConfigParser):
    """
    Creates the settings file and its directory, if it doesn't exist, and writes the given config template with
    blank values to it.

    Args:
        path (str): The full path to the file.
        template (dict): The template containing sections (keys, str) and their options (values, list of str).
        parser (ConfigParser): The ConfigParser object.
    """
    # Create file and directory if not exists and write config template to it with blank values
    settings_dir = os.path.dirname(path)
    if not os.path.exists(settings_dir):  # If settings directory does not exist either, create it too
        os.makedirs(settings_dir)

    for section, options in template.items():
        parser.add_section(section)
        for option in options:
            parser.set(section, option, '')
    with open(path, 'w') as settings_file:
        parser.write(settings_file)


def setup_user_config(path: str, template, schema):
    """
    Creates the user PV-Records XML config file and its schema, if they don't exist.

    Args:
        path (str): The full path to the file.
        template: The XML template of the config.
        schema: The XSD schema which will be used to validate the structure of the config.
    """
    # todo
    pass


class Settings:
    def __init__(self):
        self.Manager = ManagerSettings(MANAGER_SETTINGS_FILE)
        self.Service = None

    def init_service_settings(self, service_path):
        self.Service = ServiceSettings(service_path)


class ManagerSettings:
    def __init__(self, settings_path):
        self.config_parser = configparser.ConfigParser()
        self.config_parser.optionxform = lambda option_: option_  # preserve case for letters
        self.settings_path = settings_path

        if not os.path.exists(settings_path):
            setup_settings_file(path=settings_path, template=MANAGER_SETTINGS_TEMPLATE, parser=self.config_parser)

        self.config_parser.read(self.settings_path)

    def update(self):
        with open(self.settings_path, 'w') as settings_file:
            self.config_parser.write(settings_file)

    def get_service_path(self):
        return self.config_parser['Service']['Directory']

    def set_service_path(self, new_path):
        self.config_parser.set('Service', 'Directory', new_path)
        self.update()

    @staticmethod
    def get_logs_dir_path():
        log_dir = os.path.join(MANAGER_SETTINGS_DIR, 'logs')
        return log_dir

    def get_error_log_path(self):
        log_dir = self.get_logs_dir_path()
        log_file = os.path.join(log_dir, 'HLM_ErrorLog.log')
        return log_file


class ServiceSettings:
    def __init__(self, service_path):
        self.config_parser = configparser.ConfigParser()
        self.config_parser.optionxform = lambda option_: option_  # preserve case for letters
        self.service_path = service_path
        self.settings_path = os.path.join(service_path, SERVICE_SETTINGS_FILE_NAME)

        if not os.path.exists(self.settings_path):
            setup_settings_file(path=self.settings_path, template=SERVICE_SETTINGS_TEMPLATE, parser=self.config_parser)

        self.config_parser.read(self.settings_path)

        # Instantiate inner classes
        self.HeliumDB = self.HeliumDB(self)
        self.Info = self.Info(self)
        self.CA = self.CA(self)
        self.Logging = self.Logging(self)
        self.PVConfig = self.PVConfig(self)

    def update(self):
        with open(self.settings_path, 'w') as settings_file:
            self.config_parser.write(settings_file)

    class PVConfig:
        def __init__(self, outer):
            self.outer = outer
            self.ROOT = 'records'
            self.OBJ = 'object_id'
            self.MEAS = 'measurements'
            self.LOG_PERIOD = 'logging_period'

        def get_path(self):
            config_file = self.get_config_file_name()
            return os.path.join(self.outer.service_path, config_file)

        def get_config_file_name(self):
            return self.outer.config_parser['PVConfig']['FILE']

    class Logging:
        def __init__(self, outer):
            self.outer = outer
            service_dir = self.outer.service_path
            logs_dir = os.path.join(service_dir, 'logs')
            self._debug_log_path = os.path.join(logs_dir, 'debug', 'debug.log')

        def get_debug_log_path(self):
            return self._debug_log_path

    class HeliumDB:
        def __init__(self, outer):
            self.outer = outer

        def get_name(self):
            return self.outer.config_parser['HeRecoveryDB']['Name']

        def get_host(self):
            return self.outer.config_parser['HeRecoveryDB']['Host']

        def get_user(self):
            service_name = self.outer.Info.get_name()
            return win32serviceutil.GetServiceCustomOption(serviceName=service_name, option='DB_HE_USER')

        def get_pass(self):
            service_name = self.outer.Info.get_name()
            return win32serviceutil.GetServiceCustomOption(serviceName=service_name, option='DB_HE_PASS')

        def set_name(self, new_name):
            self.outer.config_parser.set('HeRecoveryDB', 'Name', new_name)
            self.outer.update()

        def set_host(self, new_host):
            self.outer.config_parser.set('HeRecoveryDB', 'Host', new_host)
            self.outer.update()

        def set_user(self, new_user):
            service_name = self.outer.Service.get_name()
            win32serviceutil.SetServiceCustomOption(
                serviceName=service_name, option='DB_HE_USER', value=new_user
            )

        def set_pass(self, new_pass):
            service_name = self.outer.Service.get_name()
            win32serviceutil.SetServiceCustomOption(
                serviceName=service_name, option='DB_HE_PASS', value=new_pass
            )

    class Info:
        def __init__(self, outer):
            self.outer = outer

        def get_name(self):
            return self.outer.config_parser['Service']['Name']

    class CA(object):
        def __init__(self, outer):
            self.outer = outer

        def get_addr_list(self, as_list: bool):
            addr_list = self.outer.config_parser['ChannelAccess']['EPICS_CA_ADDR_LIST']
            if as_list:
                addr_list = addr_list.split(' ')
            return addr_list

        def set_addr_list(self, new_list):
            if isinstance(new_list, list):
                new_list = ' '.join(new_list)
            self.outer.config_parser.set('ChannelAccess', 'EPICS_CA_ADDR_LIST', new_list)
            self.outer.update()

        def get_conn_timeout(self):
            return self.outer.config_parser['ChannelAccess']['ConnectionTimeout']

        def set_conn_timeout(self, new_timeout: int):
            self.outer.config_parser.set('ChannelAccess', 'ConnectionTimeout', new_timeout)
            self.outer.update()

        def get_pv_stale_after(self):
            return self.outer.config_parser['ChannelAccess']['PvStaleAfter']

        def set_pv_stale_after(self, new_threshold: int):
            self.outer.config_parser.set('ChannelAccess', 'PvStaleAfter', new_threshold)
            self.outer.update()

        def get_pv_prefix(self):
            return self.outer.config_parser['ChannelAccess']['PV_PREFIX']

        def set_pv_prefix(self, new_prefix: str):
            self.outer.config_parser.set('ChannelAccess', 'PV_PREFIX', new_prefix)
            self.outer.update()
            
        def get_pv_domain(self):
            return self.outer.config_parser['ChannelAccess']['PV_DOMAIN']

        def set_pv_domain(self, new_domain: str):
            self.outer.config_parser.set('ChannelAccess', 'PV_DOMAIN', new_domain)
            self.outer.update()


Settings = Settings()


# Helium DB Tables
class Tables:
    MEASUREMENT = 'gam_measurement'
    OBJECT = 'gam_object'
    OBJECT_TYPE = 'gam_objecttype'
    OBJECT_CLASS = 'gam_objectclass'
    OBJECT_RELATION = 'gam_objectrelation'
    FUNCTION = 'gam_function'
