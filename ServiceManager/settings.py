import os
import sys
import json
import configparser
import win32serviceutil
from ServiceManager.constants import MANAGER_SETTINGS_FILE, MANAGER_SETTINGS_TEMPLATE, SERVICE_SETTINGS_FILE_NAME, \
    SERVICE_SETTINGS_TEMPLATE, SERVICE_NAME, PV_CONFIG_FILE_NAME
from ServiceManager.logger import manager_logger, log_exception
from ServiceManager.utilities import setup_settings_file
from ServiceManager.db_func import db_connect, db_connected, DBConnectionError
from shared import db_models
from shared.utils import get_full_pv_name as get_full_pv_name_, get_short_pv_name as get_short_pv_name_


class _Settings:
    def __init__(self):
        self.Manager = ManagerSettings(MANAGER_SETTINGS_FILE)
        self.Service = None

    def init_service_settings(self, service_path):
        self.Service = ServiceSettings(service_path)
        self.Service.connect_to_db()


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

    def set_service_path(self, new_path: str):
        self.config_parser.set('Service', 'Directory', new_path)
        self.update()

    def get_default_meas_update_interval(self):
        return self.config_parser['Defaults'].getint('MeasurementsUpdateInterval')

    def set_default_meas_update_interval(self, new_val: int):
        self.config_parser['Defaults']['MeasurementsUpdateInterval'] = f'{new_val}'
        self.update()

    def get_new_entry_auto_pv_check(self):
        return self.config_parser['General'].getboolean('AutoPVConnectionCheck')

    def set_new_entry_auto_pv_check(self, checked: bool):
        self.config_parser['General']['AutoPVConnectionCheck'] = f'{checked}'
        self.update()

    def get_auto_load_existing_config(self):
        return self.config_parser['General'].getboolean('AutoLoadExistingConfig')

    def set_auto_load_existing_config(self, checked: bool):
        self.config_parser['General']['AutoLoadExistingConfig'] = f'{checked}'
        self.update()


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
        self.HeliumDB = _HeliumDB(self.config_parser, self.update)
        self.CA = _CA(self.config_parser, self.update)
        self.Logging = _Logging(self.service_path)
        self.PVConfig = _PVConfig(self.service_path, self.config_parser)

    def update(self):
        with open(self.settings_path, 'w') as settings_file:
            self.config_parser.write(settings_file)

    def connect_to_db(self):
        db_models.initialize_database(name=self.HeliumDB.get_name(), host=self.HeliumDB.get_host(),
                                      user=self.HeliumDB.get_user(), password=self.HeliumDB.get_pass())
        try:
            db_connect()
        except DBConnectionError:
            log_exception(*sys.exc_info())
        finally:
            return db_connected()


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
        return os.path.join(self.service_path, PV_CONFIG_FILE_NAME)

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
            data = data[self.ROOT]

            if not data:
                manager_logger.warning('PV configuration file is empty or does not exist.')
            return data

    def get_entry_with_id(self, obj_id: int):
        """
        Gets entry matching the given object ID.

        Args:
            obj_id (int): The object ID.

        Returns:
            (dict): The object config, or None if it was not found.
        """
        entries = self.get_entries()
        for entry in entries:
            if entry[self.OBJ] == obj_id:
                return entry

    def get_entry_object_ids(self):
        """
        Get a list of existing object IDs from the PV config.

        Returns:
            (list): List of object IDs.
        """
        return [entry[self.OBJ] for entry in self.get_entries()]

    def add_entry(self, new_entry: dict, overwrite: bool = False):
        """
        Add a new record config entry to PV Config.

        Args:
            new_entry (dict): The record config.
            overwrite (bool, optional): If True, overwrites the entry that matches the object ID, Defaults to False.
        """
        data = self.get_entries()
        if overwrite:
            overwritten = False
            for index, entry in enumerate(data):
                if entry[self.OBJ] == new_entry[self.OBJ]:
                    data[index] = new_entry
                    overwritten = True
                    break
            if not overwritten:
                manager_logger.error(f'Entry with object ID {new_entry[self.OBJ]} was not overwritten.')
                return
        else:
            data.append(new_entry)

        data = {self.ROOT: data}
        self._json_dump(data)
        manager_logger.info(f'Added new PV configuration entry: {new_entry}' if not overwrite
                            else f'Updated PV configuration entry: {new_entry}')

    def delete_entry(self, object_id: int):
        data = self.get_entries()
        deleted = False
        for index, entry in enumerate(data):
            if entry[self.OBJ] == object_id:
                data.remove(entry)
                deleted = True
                break

        if not deleted:
            manager_logger.warning(f'Entry with object ID {object_id} should have been deleted but was not.')

        data = {self.ROOT: data}
        self._json_dump(data)

        if deleted:
            manager_logger.info(f'Deleted PV configuration entry for object ID: {object_id}.')

    def _json_dump(self, data):
        with open(self.get_path(), 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)


class _Logging:
    def __init__(self, service_path):
        self.service_path = service_path
        logs_dir = os.path.join(service_path, 'logs')
        self._log_path = os.path.join(logs_dir, 'service', 'service.log')

    def get_log_path(self):
        return self._log_path


class _HeliumDB:
    def __init__(self, config_parser, update):
        self.config_parser = config_parser
        self.update = update
        self.user_option = 'DB_HE_USER'
        self.pass_option = 'DB_HE_PASS'

    def get_name(self):
        return self.config_parser['HeRecoveryDB']['Name']

    def get_host(self):
        return self.config_parser['HeRecoveryDB']['Host']

    def get_user(self):
        return self._get_credentials(self.user_option)

    def get_pass(self):
        return self._get_credentials(self.pass_option)

    @staticmethod
    def _get_credentials(service_option):
        if not SERVICE_NAME:
            return
        try:
            return win32serviceutil.GetServiceCustomOption(serviceName=SERVICE_NAME, option=service_option)
        except Exception as e:
            manager_logger.error(e)

    def set_name(self, new_name: str):
        self.config_parser['HeRecoveryDB']['Name'] = new_name
        self.update()

    def set_host(self, new_host: str):
        self.config_parser['HeRecoveryDB']['Host'] = new_host
        self.update()

    def set_user(self, new_user):
        self._set_credentials(self.user_option, new_user, 'DB Connection user could not be set as Service Name '
                                                          'was not found.')

    def set_pass(self, new_pass):
        self._set_credentials(self.pass_option, new_pass, 'DB Connection password could not be set as Service Name '
                                                          'was not found.')

    @staticmethod
    def _set_credentials(service_option, new_value, err_msg: str):
        if not SERVICE_NAME:
            manager_logger.error(err_msg)
            return
        try:
            win32serviceutil.SetServiceCustomOption(
                serviceName=SERVICE_NAME, option=service_option, value=new_value
            )
        except Exception as e:
            manager_logger.error(e)


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
        self.config_parser['ChannelAccess']['EPICS_CA_ADDR_LIST'] = new_list
        self.update()

    def get_conn_timeout(self):
        return self.config_parser['ChannelAccess']['ConnectionTimeout']

    def set_conn_timeout(self, new_timeout: int):
        self.config_parser['ChannelAccess']['ConnectionTimeout'] = f'{new_timeout}'
        self.update()

    def get_pv_stale_after(self):
        return self.config_parser['ChannelAccess']['PvStaleAfter']

    def set_pv_stale_after(self, new_threshold: int):
        self.config_parser['ChannelAccess']['PvStaleAfter'] = f'{new_threshold}'
        self.update()

    def get_pv_prefix(self):
        return self.config_parser['ChannelAccess']['PV_PREFIX'] \
            if self.config_parser['ChannelAccess']['PV_PREFIX'] else ''

    def set_pv_prefix(self, new_prefix: str):
        self.config_parser['ChannelAccess']['PV_PREFIX'] = new_prefix
        self.update()

    def get_pv_domain(self):
        return self.config_parser['ChannelAccess']['PV_DOMAIN'] \
            if self.config_parser['ChannelAccess']['PV_DOMAIN'] else ''

    def set_pv_domain(self, new_domain: str):
        self.config_parser['ChannelAccess']['PV_DOMAIN'] = new_domain
        self.update()

    def get_add_stale_pvs(self):
        return self.config_parser['ChannelAccess'].getboolean('AddStalePvs')

    def set_add_stale_pvs(self, checked: bool):
        self.config_parser['ChannelAccess']['AddStalePvs'] = f'{checked}'
        self.update()

    def get_full_pv_name(self, name):
        return get_full_pv_name_(name, prefix=self.get_pv_prefix(), domain=self.get_pv_domain())

    def get_short_pv_name(self, name):
        return get_short_pv_name_(name, prefix=self.get_pv_prefix(), domain=self.get_pv_domain())
# endregion


Settings = _Settings()
