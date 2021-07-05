SERVICE_NAME = 'HLMPVImport'
PV_CONFIG_FILE_NAME = 'pv_config.json'


# User Configuration
class PVConfig:
    FILE = 'pv_config.json'
    ROOT = 'records'
    OBJ = 'object_id'
    MEAS = 'measurements'
    LOG_PERIOD = 'logging_period'
    PATH = None  # set in Service/Manager settings


class DBClassIDs:
    VESSEL = 2
    CRYOSTAT = 4
    GAS_COUNTER = 7
    HE_LVL_MODULE = 17


class DBTypeIDs:
    SLD = 18
