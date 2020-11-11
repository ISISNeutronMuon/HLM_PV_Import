import os
import configparser
import win32serviceutil

VER = '1.0.0'
B_DATE = '10 November 2020'

# Placeholder, path to be asked when opening app, then saved so it's not asked all the time.
# Path can then be changed in the settings.
SERVICE_DIR = 'C:\\Users\\bgd37885\\PycharmProjects\\HLM_PV_Import'
SERVICE_SETTINGS = os.path.join(SERVICE_DIR, 'settings.ini')

config = configparser.ConfigParser()
config.optionxform = lambda option: option  # preserve case for letters
config.read(SERVICE_SETTINGS)


def update_config():
    with open(SERVICE_SETTINGS, 'w') as settings_file:
        config.write(settings_file)


# EPICS_CA_ADDR_LIST = config['ChannelAccess']['EPICS_CA_ADDR_LIST']
#
#
# class PvConfig:
#     PV_PREFIX = config['PVConfig']['PV_PREFIX']
#     PV_DOMAIN = config['PVConfig']['PV_DOMAIN']
#     CONN_TIMEOUT = config['PVConfig'].getfloat('ConnectionTimeout')
#     STALE_AFTER = config['PVConfig'].getfloat('PvStaleAfter')
#
#
# class Service:
#     NAME = config['Service']['Name']
#     DISPLAY_NAME = config['Service']['DisplayName']
#     DESCRIPTION = config['Service']['Description']
#
#
# # the HLM GAM DB
# class HEDB:
#     HOST = config['HeRecoveryDB']['Host']
#     NAME = config['HeRecoveryDB']['Name']
#     USER = win32serviceutil.GetServiceCustomOption(Service.NAME, 'DB_HE_USER')
#     PASS = win32serviceutil.GetServiceCustomOption(Service.NAME, 'DB_HE_PASS')
#
#
# class PvImportConst:
#     LOOP_TIMER = config['PVImport'].getfloat('LoopTimer')
#     DB_OBJ_NAME = config['PVImport']['DBObjectName']  # Helium DB PV Import object name
#     DB_OBJ_TYPE = config['PVImport']['DBObjectType']  # and its type name
#
