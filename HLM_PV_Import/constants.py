import sys
import os

if getattr(sys, 'frozen', False):
    # If the application is run as a bundle, the PyInstaller bootloader
    # extends the sys module by a flag frozen=True and sets the app
    # path into variable _MEIPASS'.
    application_path = sys._MEIPASS
else:
    application_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')

# Helium DB PV Import Class Name
PV_IMPORT = 'PV IMPORT'


class LoggersConst:
    LOGS_DIR = 'logs'
    ERR_LOG_DIR = os.path.join(application_path, LOGS_DIR, 'err', '')
    DB_LOG_DIR = os.path.join(application_path, LOGS_DIR, 'db', '')


# the IOC DB containing the list of PVs
class IOCDB:
    HOST = "localhost"
    NAME = "iocdb"
    USER = os.environ.get('DB_IOC_USER')
    PASS = os.environ.get('DB_IOC_PASS')


# the HLM GAM DB
class HEDB:
    HOST = "localhost"
    NAME = "helium"
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
    PV_PREFIX = 'TE:NDW2123'
    PV_DOMAIN = 'HA:HLM'


# User Configuration
class UserConfigConst:
    CONFIG_DIR = 'config'
    FILE = 'user_config.xml'
    PATH = os.path.join(application_path, CONFIG_DIR, FILE)
    SCHEMA = 'user_config.xsd'
    SCHEMA_PATH = os.path.join(application_path, CONFIG_DIR, SCHEMA)
    ROOT = 'configuration'
    ENTRY = 'entry'
    RECORD = 'record_name'
    MEAS = 'measurements'
    PV = 'pv_name'
    LOG_PERIOD = 'logging_period'
