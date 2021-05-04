from iteration_utilities import duplicates, unique_everseen
from HLM_PV_Import.logger import log_config_error
from HLM_PV_Import.settings import PVConfigConst
from HLM_PV_Import.db_functions import get_object
from HLM_PV_Import.logger import log_error
from HLM_PV_Import.utilities import get_full_pv_name
from HLM_PV_Import.ca_wrapper import get_connected_pvs
import json


class UserConfig:
    """
    User configuration class that stores entries, records, available PVs, and methods to work with them, including
    config schema and content validation.
    """

    def __init__(self):
        self.entries = self._get_all_entries()
        self.records = [entry[PVConfigConst.OBJ] for entry in self.entries]
        self.logging_periods = {entry[PVConfigConst.OBJ]: entry[PVConfigConst.LOG_PERIOD] for entry in self.entries}

    def run_checks(self):
        try:
            self._check_config_records_id_is_not_empty()
            self._check_records_have_at_least_one_measurement_pv()
            self._check_config_records_unique()
            self._check_config_records_exist()
            self._check_measurement_pvs_connect()
        except PVConfigurationException as e:
            log_error(str(e))
            raise e

    def _check_config_records_unique(self):
        """
        Checks whether all record names are unique (no double entries) or not (same record name used twice).

        Raises:
            ValueError: if duplicate record names were found
        """
        duplicate_records = list(unique_everseen(duplicates(self.records)))
        if duplicate_records:
            raise PVConfigurationException(f'User configuration contains duplicate entry '
                                           f'record names: {duplicate_records}')

    def _check_config_records_id_is_not_empty(self):
        """
        Throws error if a tag in the user configuration has an empty body (value None).

        Raises:
            ValueError: If one or more empty tags were found.
        """
        for record in self.records:
            if not record:
                raise PVConfigurationException('One or more elements in the user configuration is empty/null/None.')

    def _check_config_records_exist(self):
        """
        Checks if the record names from the user configuration exist in the database.

        Raises:
            ValueError: If one or more records were not found.
        """
        not_found = []
        for record in self.records:
            result = get_object(record)
            if not result:
                not_found.append(record)

        if not_found:
            raise PVConfigurationException(f'User configuration contains records IDs '
                                           f'that were not found in the DB: {not_found}')

    def _check_measurement_pvs_connect(self):
        """
        Checks whether the measurement PVs from the user configuration exist in the database.

        Raises:
            ValueError: If one or more PVs were not found.
        """
        print('PVConfig: Checking measurement PVs...')
        config_pvs = self.get_measurement_pvs(no_duplicates=True, full_names=True)
        connected_pvs = get_connected_pvs(config_pvs)
        not_connected = set(config_pvs) ^ set(connected_pvs)

        if not_connected:
            err_msg = f'Could not connect to one or more PVs: {not_connected}'
            print(f'PVConfig WARNING: {err_msg}')
        else:
            print('PVConfig: All PVs connected.')

    def _check_records_have_at_least_one_measurement_pv(self):
        """
        Verifies records have at least one existing PV in the measurements.

        Raises:
            ValueError: If one or more records has no measurement PVs.
        """
        records = [entry[PVConfigConst.OBJ] for entry in self.entries]
        records_with_no_pvs = []
        for record_id in records:
            try:
                pvs = self.get_record_measurement_pvs(record_id)
            except KeyError:
                pvs = None
            if not pvs:
                records_with_no_pvs.append(record_id)

        if records_with_no_pvs:
            raise PVConfigurationException(f'Records {records_with_no_pvs} have no measurement PVs.')

    def get_measurement_pvs(self, no_duplicates=True, full_names=False):
        """
        Gets a list of the measurement PVs, ignoring empty/null measurements.

        Args:
            no_duplicates (boolean, optional): If one PV is present in multiple measurements/records, add it to the list
                only once, Defaults to True.
            full_names (boolean, optional): Get the PV names with their prefix and domain, Defaults to False.

        Returns:
            (list): The list of PVs
        """
        if no_duplicates:
            config_pvs = set()
        else:
            config_pvs = []
        entries = self.entries

        for entry in entries:
            record_measurements = entry[PVConfigConst.MEAS]
            for measurement_no, pv_name in record_measurements.items():
                if pv_name:
                    if no_duplicates:
                        config_pvs.add(pv_name)
                    else:
                        config_pvs.append(pv_name)

        if isinstance(config_pvs, set):
            config_pvs = list(config_pvs)

        if full_names:
            config_pvs = [get_full_pv_name(pv) for pv in config_pvs]

        return config_pvs

    def get_record_measurement_pvs(self, record_id, full_names=False):
        """
        Get the measurement PVs of the given record, ignoring empty/null ones.

        Args:
            record_id (str): The record ID.
            full_names (boolean, optional): Get the PV names with their prefix and domain, Defaults to False.

        Returns:
            (dict): The measurements PVs, in measurement number/pv name pairs.
        """
        entries = self.entries
        record = next((item for item in entries if item[PVConfigConst.OBJ] == record_id), None)
        record_meas = record[PVConfigConst.MEAS]
        if full_names:
            record_meas = {key: get_full_pv_name(val) for key, val in record_meas.items() if val}
        else:
            record_meas = {key: val for key, val in record_meas.items() if val}

        return record_meas

    def _get_pv_config(self, pv_name):
        """
        Get the records containing the given PV as a measurement, as a list.

        Args:
            pv_name (str): Name of the PV

        Returns:
            (list): The records having the PV as a measurement.
        """
        entries = self.entries

        records = []
        for entry in entries:
            measurements = entry[PVConfigConst.MEAS]
            for mea_no, mea_pv in measurements.items():
                if mea_pv == pv_name:
                    records.append(entry)

        if not records:
            log_config_error(pv_name=f'{pv_name}', config_file=PVConfigConst.FILE, print_err=True)

        return records

    @staticmethod
    def _get_all_entries():
        """
        Get all record PV configs as a list.

        Returns:
            (list): The records' PV configurations.

        Raises:
            PVConfigurationException: If the config file is empty or does not have at least one entry.
        """
        config_file = PVConfigConst.PATH
        with open(config_file) as f:
            data = json.load(f)
            data = data[PVConfigConst.ROOT]

            if not data:
                err_msg = 'The configuration file has no entries.'
                log_error(err_msg)
                raise PVConfigurationException(err_msg)

            return data


class PVConfigurationException(ValueError):
    """
    There is a problem with the PV configuration.
    """
    def __init__(self, err_msg):
        super(PVConfigurationException, self).__init__(err_msg)
