"""
Contains utilities for logging errors that may occur when accessing and reading PVs.
"""
import os
import time

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs', '')


def log_error(pv_name, err):
    """
    Writes a message to the default log file.

    Can be used for error logging.

    Args:
        pv_name: the name of the pv
        err: the error message to log
    """

    try:
        curr_time = time.localtime()
        if not os.path.exists(LOG_DIR):
            os.makedirs(LOG_DIR)
        f_name = LOG_DIR + 'HeRecovery-' + time.strftime("%Y-%m-%d-%a", curr_time) + '.log'
        t_stamp = time.strftime("%Y-%m-%dT%H:%M:%S", curr_time)
        f = open(f_name, 'a')
        err_msg = "Unable to connect to PV {0}: {1}".format(pv_name, err)
        message = "%s\t(%s)\t%s\n" % (t_stamp, os.getpid(), err_msg)
        f.write(message)
        f.close()
    except Exception as e:
        print(e)
        pass
