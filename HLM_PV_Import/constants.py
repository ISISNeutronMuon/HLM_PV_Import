import sys
import os
import configparser

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

# Helium DB PV Import Class Name
PV_IMPORT = config['PVImport']['DBObjectName']

# Epics channel access address list
EPICS_CA_ADDR_LIST = config['ChannelAccess']['EPICS_CA_ADDR_LIST']


class LoggersConst:
    LOGS_DIR = 'logs'
    ERR_LOG_DIR = os.path.join(application_path, LOGS_DIR, 'err', '')
    DB_LOG_DIR = os.path.join(application_path, LOGS_DIR, 'db', '')


# the IOC DB containing the list of PVs
class IOCDB:
    HOST = config['IOCDB']['Host']
    NAME = config['IOCDB']['Name']
    USER = os.environ.get('DB_IOC_USER')
    PASS = os.environ.get('DB_IOC_PASS')


# the HLM GAM DB
class HEDB:
    HOST = config['HeRecoveryDB']['Host']
    NAME = config['HeRecoveryDB']['Name']
    USER = os.environ.get('DB_HE_USER')
    PASS = os.environ.get('DB_HE_PASS')


# Helium DB Tables
class Tables:
    MEASUREMENT = 'gam_measurement'
    OBJECT = 'gam_object'
    OBJECT_TYPE = 'gam_objecttype'
    OBJECT_CLASS = 'gam_objectclass'
    OBJECT_RELATION = 'gam_objectrelation'
    FUNCTION = 'gam_function'


# PV Configuration
class PvConfig:
    PV_PREFIX = config['PVConfig']['PV_PREFIX']
    PV_DOMAIN = config['PVConfig']['PV_DOMAIN']


# User Configuration
class UserConfigConst:
    CONFIG_DIR = config['UserConfig']['DIRECTORY']
    FILE = config['UserConfig']['FILE']
    PATH = os.path.join(application_path, CONFIG_DIR, FILE)
    SCHEMA = config['UserConfig']['SCHEMA']
    SCHEMA_PATH = os.path.join(application_path, CONFIG_DIR, SCHEMA)
    ROOT = 'configuration'
    ENTRY = 'entry'
    RECORD = 'record_name'
    MEAS = 'measurements'
    PV = 'pv_name'
    LOG_PERIOD = 'logging_period'
