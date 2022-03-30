import sys
import os
import configparser
import win32serviceutil
from shared.const import *

if getattr(sys, 'frozen', False):
    # If the application is run as a bundle, the PyInstaller bootloader
    # extends the sys module by a flag frozen=True and sets the app
    # path into variable _MEIPASS'.
    # noinspection PyProtectedMember
    # noinspection PyUnresolvedReferences
    # BASE_PATH = sys._MEIPASS

    # sys._MEIPASS:
    # For a one-folder bundle, this is the path to that folder, wherever the user may have put it.
    # For a one-file bundle, this is the path to the _MEIxxxxxx temporary folder created by the
    # bootloader.
    # To get the same path as the executable, use sys.executable for one-file executables.
    BASE_PATH = os.path.dirname(sys.executable)
else:
    BASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')

PVConfig.PATH = os.path.join(BASE_PATH, PVConfig.FILE)

config = configparser.ConfigParser()
config.read(os.path.join(BASE_PATH, 'settings.ini'))


class CA:
    # Epics channel access address list
    EPICS_CA_ADDR_LIST = config['ChannelAccess']['EPICS_CA_ADDR_LIST']
    CONN_TIMEOUT = config['ChannelAccess'].getfloat('ConnectionTimeout')
    STALE_AFTER = config['ChannelAccess'].getfloat('PvStaleAfter')
    ADD_STALE_PVS = config['ChannelAccess'].getboolean('AddStalePvs')
    PV_PREFIX = config['ChannelAccess']['PV_PREFIX'] if config['ChannelAccess']['PV_PREFIX'] else ''
    PV_DOMAIN = config['ChannelAccess']['PV_DOMAIN'] if config['ChannelAccess']['PV_DOMAIN'] else ''


class LoggingFiles:
    LOGS_DIR = os.path.join(BASE_PATH, 'logs')
    ERR_LOG = os.path.join(LOGS_DIR, 'error', 'error.log')
    DB_LOG = os.path.join(LOGS_DIR, 'db', 'db.log')
    PVS_LOG = os.path.join(LOGS_DIR, 'pvs', 'pvs.log')
    SRV_LOG = os.path.join(LOGS_DIR, 'service', 'service.log')


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


# PV Import Configuration
class PvImportConfig:
    LOOP_TIMER = config['PVImport'].getfloat('LoopTimer')
