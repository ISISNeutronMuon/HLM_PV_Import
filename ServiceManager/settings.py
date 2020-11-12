import os
import configparser
import win32serviceutil

VER = '1.0.0'
B_DATE = '10 November 2020'


# Assets & Layouts
gui_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'GUI')
icon_path = os.path.join(gui_dir, 'assets', 'icon.svg')
about_logo_path = os.path.join(gui_dir, 'assets', 'isis-logo.png')
about_ui = os.path.join(gui_dir, 'layouts', 'about.ui')
db_settings_ui = os.path.join(gui_dir, 'layouts', 'DBSettings.ui')
general_settings_ui = os.path.join(gui_dir, 'layouts', 'GeneralSettings.ui')
service_path_dlg_ui = os.path.join(gui_dir, 'layouts', 'ServicePathDialog.ui')


# Directory for storing the manager app settings and persistent data
MANAGER_SETTINGS_DIR = os.path.join(os.getenv('LOCALAPPDATA'), 'HLM Service Manager', '')
MANAGER_SETTINGS_FILE = os.path.join(MANAGER_SETTINGS_DIR, 'settings.ini')

MANAGER_SETTINGS_TEMPLATE = {
    'Service': ['Directory']
}

SERVICE_SETTINGS_TEMPLATE = {
    'ChannelAccess': ['EPICS_CA_ADDR_LIST', 'ConnectionTimeout'],
    'PVImport': ['LoopTimer', 'PvStaleAfter', 'PV_PREFIX', 'PV_DOMAIN'],
    'UserConfig': ['DIRECTORY', 'FILE', 'SCHEMA'],
    'HeRecoveryDB': ['Host', 'Name', 'DBObjectName', 'DBObjectType'],
    'Service': ['Name', 'DisplayName', 'Description'],
    'Logging': ['DirectoryPath']
}


class Settings:
    def __init__(self):
        self.Manager = None
        self.Service = None

    def init_manager_settings(self):
        self.Manager = ManagerSettings(MANAGER_SETTINGS_FILE)

    def init_service_settings(self):
        self.Service = ServiceSettings()


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


class ServiceSettings:
    def __init__(self, settings_path):
        self.config_parser = configparser.ConfigParser()
        self.config_parser.optionxform = lambda option_: option_  # preserve case for letters
        self.settings_path = settings_path

        if not os.path.exists(settings_path):
            setup_settings_file(path=settings_path, template=SERVICE_SETTINGS_TEMPLATE, parser=self.config_parser)

        self.config_parser.read(self.settings_path)

        # Instantiate inner classes
        self.HeliumDB = self.HeliumDB(self)
        self.Info = self.Info(self)
        self.CA = self.CA(self)

    def update(self):
        with open(self.settings_path, 'w') as settings_file:
            self.config_parser.write(settings_file)

    class HeliumDB:
        def __init__(self, outer):
            self.outer = outer

        def get_name(self):
            return self.outer.config_parser['HeRecoveryDB']['Name']

        def get_host(self):
            return self.outer.config_parser['HeRecoveryDB']['Host']

        def get_user(self):
            service_name = self.outer.Service.get_name()
            return win32serviceutil.GetServiceCustomOption(serviceName=service_name, option='DB_HE_USER')

        def get_pass(self):
            service_name = self.outer.Service.get_name()
            return win32serviceutil.GetServiceCustomOption(serviceName=service_name, option='DB_HE_PASS')

        def set_name(self, new_name):
            self.outer.config_parser.set('HeRecoveryDB', 'Name', new_name)
            self.outer.update_service()

        def set_host(self, new_host):
            self.outer.config_parser.set('HeRecoveryDB', 'Host', new_host)
            self.outer.update_service()

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

    class CA:
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
            self.outer.update_service()


def setup_settings_file(path: str, template: dict, parser: configparser.ConfigParser):
    """
    Creates the settings file and its directory, if it doesn't exist, and writes the given config template with
    blank values to it.

    Args:
        path (str): The full path of the file.
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
    parser.update()


Settings = Settings()


manager_settings = ManagerSettings(MANAGER_SETTINGS_FILE)

SERVICE_DIR = 'C:\\Users\\bgd37885\\PycharmProjects\\HLM_PV_Import'
SERVICE_SETTINGS_FILE = os.path.join(SERVICE_DIR, 'settings.ini')

service_settings = ServiceSettings(SERVICE_SETTINGS_FILE)
