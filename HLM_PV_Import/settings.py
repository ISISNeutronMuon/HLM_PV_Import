import sys
import os
import configparser
import win32serviceutil

if getattr(sys, 'frozen', False):
    # If the application is run as a bundle, the PyInstaller bootloader
    # extends the sys module by a flag frozen=True and sets the app
    # path into variable _MEIPASS'.
    # noinspection PyProtectedMember
    # noinspection PyUnresolvedReferences
    # BASE_PATH = sys._MEIPASS

    # sys._MEIPASS:
    # For a one-folder bundle, this is the path to that folder, wherever the user may have put it.
    # For a one-file bundle, this is the path to the _MEIxxxxxx temporary folder created by the bootloader.
    # To get the same path as the executable, use sys.executable for one-file executables.
    BASE_PATH = os.path.dirname(sys.executable)
else:
    BASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')


config = configparser.ConfigParser()
config.read(os.path.join(BASE_PATH, 'settings.ini'))


class CA:
    EPICS_CA_ADDR_LIST = config['ChannelAccess']['EPICS_CA_ADDR_LIST']  # Epics channel access address list
    CONN_TIMEOUT = config['ChannelAccess'].getfloat('ConnectionTimeout')
    STALE_AFTER = config['ChannelAccess'].getfloat('PvStaleAfter')
    PV_PREFIX = config['ChannelAccess']['PV_PREFIX']
    PV_DOMAIN = config['ChannelAccess']['PV_DOMAIN']


class LoggersConst:
    LOGS_DIR = 'logs'
    ERR_LOG_DIR = os.path.join(BASE_PATH, LOGS_DIR, 'err', '')
    DB_LOG_DIR = os.path.join(BASE_PATH, LOGS_DIR, 'db', '')


class Service:
    NAME = 'HLMPVImport'
    DISPLAY_NAME = 'HLM PV Import'
    DESCRIPTION = 'Helium Level Monitoring - PV Import'


# the HLM GAM DB
class HEDB:
    HOST = config['HeRecoveryDB']['Host']
    NAME = config['HeRecoveryDB']['Name']
    USER = win32serviceutil.GetServiceCustomOption(Service.NAME, 'DB_HE_USER')
    PASS = win32serviceutil.GetServiceCustomOption(Service.NAME, 'DB_HE_PASS')


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
class PVConfigConst:
    FILE = 'pv_config.json'
    PATH = os.path.join(BASE_PATH, FILE)
    ROOT = 'records'
    OBJ = 'object_id'
    MEAS = 'measurements'
    LOG_PERIOD = 'logging_period'
