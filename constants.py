import os

# Helium DB PV Import Class Name
PV_IMPORT = 'PV IMPORT'


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
    FILE = 'user_config.xml'
    PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), FILE)
    SCHEMA = 'user_config.xsd'
    SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), SCHEMA)
    ROOT = 'configuration'
    ENTRY = 'entry'
    RECORD = 'record_name'
    MEAS = 'measurements'
    PV = 'pv_name'
