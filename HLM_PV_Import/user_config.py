from lxml import etree
import xmltodict
from iteration_utilities import duplicates, unique_everseen
from HLM_PV_Import.logger import log_config_error
from HLM_PV_Import.constants import UserConfigConst
from HLM_PV_Import.db_functions import get_object_id
from HLM_PV_Import.pv_functions import get_pv_names
from HLM_PV_Import.logger import log_error
from HLM_PV_Import.utilities import get_full_pv_name


class UserConfig:
    """
    User configuration class that stores entries, records, available PVs, and methods to work with them, including
    config schema and content validation.
    """

    def __init__(self):
        self._validate_config_with_schema()
        self.entries = self._get_all_entries()
        self.records = self._get_all_entry_records()
        self.available_pvs = get_pv_names(short_names=True)
        self.logging_periods = self._get_logging_periods()

    def run_checks(self):
        self._check_config_records_tag_not_empty()
        self._check_records_have_at_least_one_measurement_pv()
        self._check_config_records_unique()
        self._check_config_records_exist()
        self._check_measurement_pvs_exist()

    @staticmethod
    def _validate_config_with_schema():

        schema_file = UserConfigConst.SCHEMA_PATH
        with open(schema_file, 'rb') as f:
            schema_root = etree.XML(f.read())

        schema = etree.XMLSchema(schema_root)
        xml_parser = etree.XMLParser(schema=schema)

        config_file = UserConfigConst.PATH
        try:
            with open(config_file, 'rb') as f:
                etree.fromstring(f.read(), xml_parser)
            return True
        except etree.XMLSchemaError:
            return False

    def _check_config_records_unique(self):
        """
        Checks whether all record names are unique (no double entries) or not (same record name used twice).

        Raises:
            ValueError: if duplicate record names were found
        """
        duplicate_records = list(unique_everseen(duplicates(self.records)))
        if duplicate_records:
            err_msg = f'User configuration contains duplicate entry record names: {duplicate_records}'
            log_error(err_msg)
            raise UserConfigurationException(err_msg)

    def _check_config_records_tag_not_empty(self):
        """
        Throws error if a tag in the user configuration has an empty body (value None).

        Raises:
            ValueError: If one or more empty tags were found.
        """
        for record in self.records:
            if not record:
                err_msg = 'One or more elements in the user configuration is empty/null/None.'
                log_error('One or more elements in the user configuration is empty/null/None.')
                raise UserConfigurationException(err_msg)

    def _check_config_records_exist(self):
        """
        Checks if the record names from the user configuration exist in the database.

        Raises:
            ValueError: If one or more records were not found.
        """
        not_found = []
        for record in self.records:
            result = get_object_id(record)
            if not result:
                not_found.append(record)

        if not_found:
            err_msg = f'User configuration contains record names that were not found in the DB: {not_found}'
            log_error(err_msg)
            raise UserConfigurationException(err_msg)

    def _check_measurement_pvs_exist(self):
        """
        Checks whether the measurement PVs from the user configuration exist in the database.

        Raises:
            ValueError: If one or more PVs were not found.
        """
        config_pvs = self.get_measurement_pvs(no_duplicates=True)

        not_found = []
        for pv in config_pvs:
            if pv and pv not in self.available_pvs:
                not_found.append(pv)

        if not_found:
            err_msg = f'One or more PVs in the user configuration does not exist: {not_found}'
            log_error(err_msg)
            raise UserConfigurationException(err_msg)

    def _check_records_have_at_least_one_measurement_pv(self):
        """
        Verifies records have at least one existing PV in the measurements.

        Raises:
            ValueError: If one or more records has no measurement PVs.
        """
        entries = self.entries[UserConfigConst.ENTRY]

        if not isinstance(entries, list):
            entries = [entries]

        records_with_no_pvs = []
        for entry in entries:
            if not entry[UserConfigConst.MEAS][UserConfigConst.PV]:
                records_with_no_pvs.append(entry[UserConfigConst.RECORD])

        if records_with_no_pvs:
            err_msg = f'Records {records_with_no_pvs} have no measurement PVs.'
            log_error(err_msg)
            raise UserConfigurationException(err_msg)

    def get_measurement_pvs(self, no_duplicates=True, full_names=False):
        """
        Gets a list of the measurement PVs, ignoring empty measurements.

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
        entries = self.entries[UserConfigConst.ENTRY]

        if not isinstance(entries, list):
            entries = [entries]

        for entry in entries:
            if entry[UserConfigConst.MEAS][UserConfigConst.PV]:
                entry_pvs = entry[UserConfigConst.MEAS][UserConfigConst.PV]
                if not isinstance(entry_pvs, list):
                    entry_pvs = [entry_pvs]
                for pv_name in entry_pvs:
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

    def get_record_measurement_pvs(self, record_name, full_names=False):
        """
        Get the list of measurement PVs of the given record.

        Args:
            record_name (str): The record name.
            full_names (boolean, optional): Get the PV names with their prefix and domain, Defaults to False.

        Returns:
            (list): The list of record measurements PVs.
        """
        entries = self.entries[UserConfigConst.ENTRY]
        entry_pvs = []
        for entry in entries:
            if entry[UserConfigConst.RECORD] == record_name:
                if entry[UserConfigConst.MEAS][UserConfigConst.PV]:
                    entry_pvs = entry[UserConfigConst.MEAS][UserConfigConst.PV]
                    if not isinstance(entry_pvs, list):
                        entry_pvs = [entry_pvs]
        if full_names:
            entry_pvs = [get_full_pv_name(pv) for pv in entry_pvs]

        return entry_pvs

    def _get_logging_periods(self):
        """
        Gets a dictionary of records and their database logging period from the user configuration.

        Returns:
            (dict): The records and their logging period (int).
        """
        entries = self.entries[UserConfigConst.ENTRY]
        if not isinstance(entries, list):
            entries = [entries]
        records_and_periods = {}
        for entry in entries:
            record_name = entry[UserConfigConst.RECORD]
            log_period = int(entry[UserConfigConst.LOG_PERIOD])
            records_and_periods[record_name] = log_period

        return records_and_periods

    @staticmethod
    def _get_pv_config(pv_name):
        """
        Get the configuration of given PV. If PV is used as a measurement in multiple records, return each
        of those records in a list.

        Args:
            pv_name (str): Name of the PV

        Returns:
            (dict/list): The PV user configuration(s).
        """
        return_val = []
        config_file = UserConfigConst.PATH
        with open(config_file, 'rb') as f:
            config = xmltodict.parse(f.read(), dict_constructor=dict)

            for entry in config[UserConfigConst.ROOT][UserConfigConst.ENTRY]:
                if entry[UserConfigConst.MEAS][UserConfigConst.PV]:
                    if pv_name in entry[UserConfigConst.MEAS][UserConfigConst.PV]:
                        return_val.append(entry)

            if not return_val:
                log_config_error(pv_name=f'{pv_name}', config_file=UserConfigConst.FILE, print_err=True)

            if isinstance(return_val, list) and len(return_val) == 1:
                return_val = return_val[0]

            return return_val

    @staticmethod
    def _get_all_entries():
        """
        Get all user configuration entries.

        Returns:
            (dict): The PV configurations dictionary.
        """
        config_file = UserConfigConst.PATH
        with open(config_file, 'rb') as f:
            config = xmltodict.parse(f.read(), dict_constructor=dict)
            return_val = config[UserConfigConst.ROOT]

            return return_val

    @staticmethod
    def _get_all_entry_records():
        """
        Get the record names of all entries from the user configurations.

        Returns:
            (list): The record names.
        """
        config_file = UserConfigConst.PATH
        with open(config_file, 'rb') as f:
            config = xmltodict.parse(f.read(), dict_constructor=dict)
            records = []
            entries = config[UserConfigConst.ROOT][UserConfigConst.ENTRY]
            if not isinstance(entries, list):
                entries = [entries]
            for entry in entries:
                records.append(entry[UserConfigConst.RECORD])

            return records


class UserConfigurationException(ValueError):
    """
    There is a problem with the user configuration.
    """
    def __init__(self, err_msg):
        super(UserConfigurationException, self).__init__(err_msg)
