import json
import os
import configparser
import win32serviceutil
from ServiceManager.constants import MANAGER_SETTINGS_FILE, MANAGER_SETTINGS_TEMPLATE, SERVICE_SETTINGS_FILE_NAME, \
    SERVICE_SETTINGS_TEMPLATE
from ServiceManager.db_utilities import DBUtils


def pv_name_without_prefix_and_domain(name):
    """
    Given a PV name, remove the prefix and domain and return only the PV name.

    Args:
        name(str): the full PV name
    Returns:
        name(str): the PV name without prefix and domain
    """
    name = name.replace(f'{Settings.Service.CA.get_pv_prefix()}:', '') \
               .replace(f'{Settings.Service.CA.get_pv_domain()}:', '')
    return name


def get_full_pv_name(name):
    """
    Adds the prefix and domain to the PV if it doesn't have them.

    Args:
        name (str): The PV name.

    Returns:
        (str) The full PV name.
    """
    if not name:
        return None
    name = pv_name_without_prefix_and_domain(name)
    name = f'{Settings.Service.CA.get_pv_prefix()}:{Settings.Service.CA.get_pv_domain()}:{name}'
    return name


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


class _Settings:
    def __init__(self):
        self.Manager = ManagerSettings(MANAGER_SETTINGS_FILE)
        self.Service = None

    def init_service_settings(self, service_path):
        self.Service = ServiceSettings(service_path)
        DBUtils.make_connection(host=Settings.Service.HeliumDB.get_host(),
                                database=Settings.Service.HeliumDB.get_name(),
                                user=Settings.Service.HeliumDB.get_user(),
                                password=Settings.Service.HeliumDB.get_pass())


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
    def __init__(self, service_path):
        self.config_parser = configparser.ConfigParser()
        self.config_parser.optionxform = lambda option_: option_  # preserve case for letters
        self.service_path = service_path
        self.settings_path = os.path.join(service_path, SERVICE_SETTINGS_FILE_NAME)
        self.pv_config_path = os.path.join(service_path, )

        if not os.path.exists(self.settings_path):
            setup_settings_file(path=self.settings_path, template=SERVICE_SETTINGS_TEMPLATE, parser=self.config_parser)

        self.config_parser.read(self.settings_path)

        # Instantiate inner classes
        self.HeliumDB = _HeliumDB(self.config_parser, self.update)
        self.Info = _Info(self.config_parser)
        self.CA = _CA(self.config_parser, self.update)
        self.Logging = _Logging(self.service_path)
        self.PVConfig = _PVConfig(self.service_path, self.config_parser)

    def update(self):
        with open(self.settings_path, 'w') as settings_file:
            self.config_parser.write(settings_file)


# region Service Settings Subclasses
class _PVConfig:
    def __init__(self, service_path, config_parser):
        self.service_path = service_path
        self.config_parser = config_parser
        self.ROOT = 'records'
        self.OBJ = 'object_id'
        self.MEAS = 'measurements'
        self.LOG_PERIOD = 'logging_period'

        # If PV config not found, create it
        config_path = self.get_path()
        if not os.path.exists(config_path):
            self.setup_file()

    def get_path(self):
        config_file = self.get_config_file_name()
        return os.path.join(self.service_path, config_file)

    def get_config_file_name(self):
        return self.config_parser['PVConfig']['FILE']

    def setup_file(self):
        """ Creates the user PV-Records config file if it doesn't exist. """
        path = self.get_path()
        settings_dir = os.path.dirname(path)
        if not os.path.exists(settings_dir):  # If settings directory does not exist either, create it too
            os.makedirs(settings_dir)

        data = {self.ROOT: []}
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def get_entries(self):
        """
        Get all user configuration entries as a dictionary.

        Returns:
            (list): The PV configurations list.
        """
        config_file = self.get_path()
        with open(config_file) as f:
            data = json.load(f)
            data = data[Settings.Service.PVConfig.ROOT]

            if not data:
                print('PV configuration file is empty.')
            return data

    def add_entry(self, new_entry: dict):
        """
        Add a new record config entry to PV Config.

        Args:
            new_entry  (dict): The record config.
        """
        file_path = self.get_path()
        data = self.get_entries()
        data.append(new_entry)
        data = {self.ROOT: data}

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        print(f'Added new PV configuration entry: {new_entry}')


class _Logging:
    def __init__(self, service_path):
        self.service_path = service_path
        logs_dir = os.path.join(service_path, 'logs')
        self._debug_log_path = os.path.join(logs_dir, 'debug', 'debug.log')

    def get_debug_log_path(self):
        return self._debug_log_path


class _HeliumDB:
    def __init__(self, config_parser, update):
        self.config_parser = config_parser
        self.update = update

    def get_name(self):
        return self.config_parser['HeRecoveryDB']['Name']

    def get_host(self):
        return self.config_parser['HeRecoveryDB']['Host']

    @staticmethod
    def get_user():
        service_name = Settings.Service.Info.get_name()
        return win32serviceutil.GetServiceCustomOption(serviceName=service_name, option='DB_HE_USER')

    @staticmethod
    def get_pass():
        service_name = Settings.Service.Info.get_name()
        return win32serviceutil.GetServiceCustomOption(serviceName=service_name, option='DB_HE_PASS')

    def set_name(self, new_name):
        self.config_parser.set('HeRecoveryDB', 'Name', new_name)
        self.update()

    def set_host(self, new_host):
        self.config_parser.set('HeRecoveryDB', 'Host', new_host)
        self.update()

    @staticmethod
    def set_user(new_user):
        service_name = Settings.Service.Info.get_name()
        win32serviceutil.SetServiceCustomOption(
            serviceName=service_name, option='DB_HE_USER', value=new_user
        )

    @staticmethod
    def set_pass(new_pass):
        service_name = Settings.Service.Info.get_name()
        win32serviceutil.SetServiceCustomOption(
            serviceName=service_name, option='DB_HE_PASS', value=new_pass
        )


class _Info:
    def __init__(self, config_parser):
        self.config_parser = config_parser

    def get_name(self):
        return self.config_parser['Service']['Name']


class _CA:
    def __init__(self, config_parser, update):
        self.config_parser = config_parser
        self.update = update
        # Setup the channel access address list in order to connect to PVs
        os.environ['EPICS_CA_ADDR_LIST'] = self.get_addr_list()

    def get_addr_list(self, as_list: bool = False):
        addr_list = self.config_parser['ChannelAccess']['EPICS_CA_ADDR_LIST']
        if as_list:
            addr_list = addr_list.split(' ')
        return addr_list

    def set_addr_list(self, new_list):
        if isinstance(new_list, list):
            new_list = ' '.join(new_list)
        self.config_parser.set('ChannelAccess', 'EPICS_CA_ADDR_LIST', new_list)
        self.update()

    def get_conn_timeout(self):
        return self.config_parser['ChannelAccess']['ConnectionTimeout']

    def set_conn_timeout(self, new_timeout: int):
        self.config_parser.set('ChannelAccess', 'ConnectionTimeout', new_timeout)
        self.update()

    def get_pv_stale_after(self):
        return self.config_parser['ChannelAccess']['PvStaleAfter']

    def set_pv_stale_after(self, new_threshold: int):
        self.config_parser.set('ChannelAccess', 'PvStaleAfter', new_threshold)
        self.update()

    def get_pv_prefix(self):
        return self.config_parser['ChannelAccess']['PV_PREFIX']

    def set_pv_prefix(self, new_prefix: str):
        self.config_parser.set('ChannelAccess', 'PV_PREFIX', new_prefix)
        self.update()

    def get_pv_domain(self):
        return self.config_parser['ChannelAccess']['PV_DOMAIN']

    def set_pv_domain(self, new_domain: str):
        self.config_parser.set('ChannelAccess', 'PV_DOMAIN', new_domain)
        self.update()


# endregion


Settings = _Settings()
