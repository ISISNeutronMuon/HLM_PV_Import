"""
Contains utilities for logging errors.
"""
import os
import sys
import time
from constants import UserConfigConst

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs', '')


def log_db_error(err, print_err=False):
    """
    Logs a MySQL DB error to the default log file.

    Args:
        err (str): the error message
        print_err (boolean, optional): Output the error message to console, Defaults to False.
    """
    err_msg = f"MySQL DB Error: {err}"
    log_error(err_msg)
    if print_err:
        sys.stderr.write(f'{err_msg}\n')


def log_ca_error(pv_name, err, print_err=False):
    """
    Logs a Channel Access error to the default log file.

    Args:
        pv_name (str): the name of the PV
        err (str): the error message
        print_err (boolean, optional): Output the error message to console, Defaults to False.
    """
    err_msg = f"Unable to connect to PV '{pv_name}': {err}"
    log_error(err_msg)
    if print_err:
        sys.stderr.write(f'{err_msg}\n')


def log_config_error(pv_name, config_file=UserConfigConst.FILE, print_err=False):
    """
    Logs a configuration error to the default log file.

    Args:
        pv_name (str, optional): the name of the PV
        err (str): the error message
        config_file (str, optional): the name of the configuration file
        print_err (boolean, optional): Output the error message to console, Defaults to False.
    """
    err_msg = f"KeyError: Could not find configuration entry for PV '{pv_name}' in '{config_file}'."
    log_error(err_msg)
    if print_err:
        sys.stderr.write(f'{err_msg}\n')


def log_error(err_msg):
    """
    Writes a message to the default log file.

    Can be used for error logging.

    Args:
        err_msg (str): the error message to log
    """

    try:
        curr_time = time.localtime()
        if not os.path.exists(LOG_DIR):
            os.makedirs(LOG_DIR)
        f_name = LOG_DIR + 'HeRecovery-' + time.strftime("%Y-%m-%d-%a", curr_time) + '.log'
        t_stamp = time.strftime("%Y-%m-%dT%H:%M:%S", curr_time)
        f = open(f_name, 'a')
        message = "%s\t(%s)\t%s\n" % (t_stamp, os.getpid(), err_msg)
        f.write(message)
        f.close()
    except Exception as e:
        print(e)
        pass


