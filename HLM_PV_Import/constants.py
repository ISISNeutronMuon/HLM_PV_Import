import sys
import os
import configparser
import win32serviceutil

if getattr(sys, 'frozen', False):
    # If the application is run as a bundle, the PyInstaller bootloader
    # extends the sys module by a flag frozen=True and sets the app
    # path into variable _MEIPASS'.
    # application_path = sys._MEIPASS

    # Using sys._MEIPASS does not work for one-file executables. From the docs: For a one-folder bundle, this is the
    # path to that folder, wherever the user may have put it. For a one-file bundle, this is the path to the _MEIxxxxxx
    # temporary folder created by the bootloader . Use sys.executable for one-file executables.
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')


config = configparser.ConfigParser()
config.read(os.path.join(application_path, 'settings.ini'))


class CA:
    EPICS_CA_ADDR_LIST = config['ChannelAccess']['EPICS_CA_ADDR_LIST']  # Epics channel access address list
    CONN_TIMEOUT = config['ChannelAccess'].getfloat('ConnectionTimeout')
    STALE_AFTER = config['ChannelAccess'].getfloat('PvStaleAfter')
    PV_PREFIX = config['ChannelAccess']['PV_PREFIX']
    PV_DOMAIN = config['ChannelAccess']['PV_DOMAIN']


class LoggersConst:
    _config_logs_dir = config['Logging']['DirectoryPath']
    LOGS_DIR = 'logs' if not _config_logs_dir else _config_logs_dir
    ERR_LOG_DIR = os.path.join(application_path, LOGS_DIR, 'err', '')
    DB_LOG_DIR = os.path.join(application_path, LOGS_DIR, 'db', '')


class Service:
    NAME = config['Service']['Name']
    DISPLAY_NAME = config['Service']['DisplayName']
    DESCRIPTION = config['Service']['Description']


# the HLM GAM DB
class HEDB:
    HOST = config['HeRecoveryDB']['Host']
    NAME = config['HeRecoveryDB']['Name']
    USER = win32serviceutil.GetServiceCustomOption(Service.NAME, 'DB_HE_USER')
    PASS = win32serviceutil.GetServiceCustomOption(Service.NAME, 'DB_HE_PASS')
    DB_OBJ_NAME = config['PVImport']['DBObjectName']  # Helium DB PV Import object name
    DB_OBJ_TYPE = config['PVImport']['DBObjectType']  # and its type name


# Helium DB Tables
class Tables:
    MEASUREMENT = 'gam_measurement'
    OBJECT = 'gam_object'
    OBJECT_TYPE = 'gam_objecttype'
    OBJECT_CLASS = 'gam_objectclass'
    OBJECT_RELATION = 'gam_objectrelation'
    FUNCTION = 'gam_function'


# PV Import Configuration
class PvImportConfig:
    LOOP_TIMER = config['PVImport'].getfloat('LoopTimer')


# User Configuration
class UserConfigConst:
    CONFIG_DIR = config['UserConfig']['DIRECTORY']
    FILE = config['UserConfig']['FILE']
    SCHEMA = config['UserConfig']['SCHEMA']

    PATH = os.path.join(application_path, CONFIG_DIR, FILE)
    SCHEMA_PATH = os.path.join(application_path, CONFIG_DIR, SCHEMA)
    ROOT = 'configuration'
    ENTRY = 'entry'
    RECORD = 'record_name'
    MEAS = 'measurements'
    PV = 'pv_name'
    LOG_PERIOD = 'logging_period'
