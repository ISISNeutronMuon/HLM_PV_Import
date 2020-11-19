
import os
import sys
import time
from HLM_PV_Import.settings import PVConfigConst, LoggersConst

ERR_LOG_DIR = LoggersConst.ERR_LOG_DIR
DB_LOG_DIR = LoggersConst.DB_LOG_DIR


def log_db_error(err, print_err=False):
    """
    Logs a MySQL DB error to the error log file.

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
    Logs a Channel Access error to the error log file.

    Args:
        pv_name (str): the name of the PV
        err (str): the error message
        print_err (boolean, optional): Output the error message to console, Defaults to False.
    """
    err_msg = f"Unable to connect to PV '{pv_name}': {err}"
    log_error(err_msg)
    if print_err:
        sys.stderr.write(f'{err_msg}\n')


def log_stale_pv_warning(pv_name, time_since_last_update, print_err=False):
    """
    Logs a stale PV warning to the error log file.

    Args:
        pv_name (str): the name of the PV
        time_since_last_update (int): Time since last PV data update, in seconds.
        print_err (boolean, optional): Output the error message to console, Defaults to False.
    """
    time_since_last_update = '{:.1f}'.format(time_since_last_update)
    err_msg = f"Stale PV warning: PV '{pv_name}' has not received updates for {time_since_last_update} seconds."
    log_error(err_msg)
    if print_err:
        sys.stderr.write(f'{err_msg}\n')


def log_config_error(pv_name, config_file=PVConfigConst.FILE, print_err=False):
    """
    Logs a configuration error to the error log file.

    Args:
        pv_name (str): the name of the PV
        config_file (str, optional): the name of the configuration file
        print_err (boolean, optional): Output the error message to console, Defaults to False.
    """
    err_msg = f"KeyError: Could not find configuration entry for PV '{pv_name}' in '{config_file}'."
    log_error(err_msg)
    if print_err:
        sys.stderr.write(f'{err_msg}\n')


def log_error(msg):
    """
    Writes an error message to the errors log file.

    Args:
        msg (str): the error message to log
    """

    try:
        curr_time = time.localtime()
        if not os.path.exists(ERR_LOG_DIR):
            os.makedirs(ERR_LOG_DIR)
        f_name = ERR_LOG_DIR + 'HeRecovery-' + time.strftime("%Y-%m-%d-%a", curr_time) + '.log'
        t_stamp = time.strftime("%Y-%m-%dT%H:%M:%S", curr_time)
        f = open(f_name, 'a')
        message = "%s\t(%s)\t%s\n" % (t_stamp, os.getpid(), msg)
        f.write(message)
        f.close()
    except Exception as e:
        print(e)
        pass


class DBLogger:
    """
    Class for logging continuous database events.
    """
    def __init__(self):
        self.log_path = DB_LOG_DIR
        self.file_date = None
        self.log_file = None

    def make_log(self):
        """
        Creates the log file if it doesn't exist, and opens it for appending.
        """
        curr_time = time.localtime()
        if not os.path.exists(self.log_path):
            os.makedirs(self.log_path)
        self.file_date = time.strftime("%Y-%m-%d-%a", curr_time)
        file_name = self.log_path + 'HeRecovery-' + time.strftime("%Y-%m-%d-%a", curr_time) + '.log'
        self.log_file = open(file_name, 'a')

    def update_log(self):
        """
        Checks the date the current log file was created, and if it changed then make a new one.
        This is so that each day has a different log file.
        """
        curr_date = time.strftime("%Y-%m-%d-%a", time.localtime())
        if self.file_date != curr_date:
            self.log_file.close()
            self.make_log()

    def log_new_measurement(self, record_no, obj_id, obj_name, values, print_msg=False):
        """
        Logs details of the measurement added to the DB.

        Args:
            record_no (int): The measurement record ID
            obj_id (int): The ID of the object the values are for.
            obj_name (str): The name of the object.
            values (dict/list): The values of the measurement.
            print_msg (boolean, optional): Whether to print the log message to the console, Defaults to False.
        """
        msg = f'Added measurement {record_no} for {obj_name} ({obj_id}) with values: {values}'

        if print_msg:
            print(msg)

        self._log_write(msg)
    
    def _log_write(self, msg):
        """
        Writes a message to the database events log file.

        Args:
            msg (str): the message to log
        """
        self.update_log()
        curr_time = time.localtime()
        t_stamp = time.strftime("%Y-%m-%dT%H:%M:%S", curr_time)
        message = "%s\t(%s)\t%s\n" % (t_stamp, os.getpid(), msg)
        self.log_file.write(message)
        self.log_file.flush()
        os.fsync(self.log_file.fileno())  # ensure that all associated internal buffers are written to disk
