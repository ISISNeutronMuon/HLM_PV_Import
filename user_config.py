from lxml import etree
import xmltodict
from iteration_utilities import duplicates, unique_everseen
from err_logger import log_config_error
from constants import UserConfig
from db_functions import get_object_id
from pv_functions import get_pv_names
from err_logger import log_error


def get_pv_config(pv_name):
    """
    Get the configuration of given PV. If PV is used as a measurement in multiple records, return each of those records
    in a list.

    Args:
        pv_name (str): Name of the PV

    Returns:
        (dict/list): The PV user configuration(s).
    """
    return_val = []
    config_file = UserConfig.PATH
    with open(config_file, 'rb') as f:
        config = xmltodict.parse(f.read(), dict_constructor=dict)

        for entry in config[UserConfig.ROOT][UserConfig.ENTRY]:
            if entry[UserConfig.MEAS][UserConfig.PV]:
                if pv_name in entry[UserConfig.MEAS][UserConfig.PV]:
                    return_val.append(entry)

        if not return_val:
            log_config_error(pv_name=f'{pv_name}', config_file=UserConfig.FILE, print_err=True)

        if isinstance(return_val, list) and len(return_val) == 1:
            return_val = return_val[0]

        return return_val


def get_all_configs():
    """
    Get all user configuration entries.

    Returns:
        (dict): The PV configurations dictionary.
    """
    config_file = UserConfig.PATH
    with open(config_file, 'rb') as f:
        config = xmltodict.parse(f.read(), dict_constructor=dict)
        return_val = config[UserConfig.ROOT]

        return return_val


def get_all_config_records():
    """
    Get the record names of all entries from the user configurations.

    Returns:
        (list): The record names.
    """
    config_file = UserConfig.PATH
    with open(config_file, 'rb') as f:
        config = xmltodict.parse(f.read(), dict_constructor=dict)
        records = []
        entries = config[UserConfig.ROOT][UserConfig.ENTRY]
        if not isinstance(entries, list):
            entries = [entries]
        for entry in entries:
            records.append(entry[UserConfig.RECORD])

        return records


class ValidateUserConfig:

    def __init__(self):
        self.configs = get_all_configs()
        self.records = get_all_config_records()
        self.available_pvs = get_pv_names(short_names=True)

    def run_checks(self):
        self.validate_config_with_schema()
        self.check_config_records_tag_not_empty()
        self.check_measurement_pvs_exist()
        self.check_config_records_exist()
        self.check_measurement_pvs_exist()

    @staticmethod
    def validate_config_with_schema():

        schema_file = UserConfig.SCHEMA_PATH
        with open(schema_file, 'rb') as f:
            schema_root = etree.XML(f.read())

        schema = etree.XMLSchema(schema_root)
        xml_parser = etree.XMLParser(schema=schema)

        config_file = UserConfig.PATH
        try:
            with open(config_file, 'rb') as f:
                etree.fromstring(f.read(), xml_parser)
            return True
        except etree.XMLSchemaError:
            return False

    def check_config_records_unique(self):
        """
        Checks whether all record names are unique (no double entries) or not (same record name used twice).

        Raises:
            ValueError: if duplicate record names were found
        """
        duplicate_records = list(unique_everseen(duplicates(self.records)))
        if duplicate_records:
            err_msg = f'User configuration contains duplicate entry record names: {duplicate_records}'
            log_error(err_msg)
            raise ValueError(err_msg)

    def check_config_records_tag_not_empty(self):
        """
        Throws error if a tag in the user configuration has an empty body (value None).

        Raises:
            ValueError: If one or more empty tags were found.
        """
        for record in self.records:
            if not record:
                err_msg = 'One or more elements in the user configuration is empty/null/None.'
                log_error('One or more elements in the user configuration is empty/null/None.')
                raise ValueError(err_msg)

    def check_config_records_exist(self):
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
            raise ValueError(err_msg)

    def check_measurement_pvs_exist(self):
        """
        Checks whether the measurement PVs from the user configuration exist in the database.

        Raises:
            ValueError: If one or more PVs were not found.
        """
        config_pvs = self._get_measurement_pvs(no_duplicates=True)

        not_found = []
        for pv in config_pvs:
            if pv not in self.available_pvs:
                not_found.append(pv)

        if not_found:
            err_msg = f'One or more PVs in the user configuration does not exist: {not_found}'
            log_error(err_msg)
            raise ValueError(err_msg)

    def _get_measurement_pvs(self, no_duplicates=True):
        """
        Gets a list of the measurement PVs.

        Args:
            no_duplicates (boolean, optional): If one PV is present in multiple measurements/records, add it to the list
                only once, Defaults to True.

        Returns:
            (list): The list of PVs
        """
        if no_duplicates:
            config_pvs = set()
        else:
            config_pvs = []
        entries = self.configs[UserConfig.ENTRY]

        if not isinstance(entries, list):
            entries = [entries]

        for entry in entries:
            if entry[UserConfig.MEAS][UserConfig.PV]:
                entry_pvs = entry[UserConfig.MEAS][UserConfig.PV]
                if not isinstance(entry_pvs, list):
                    entry_pvs = [entry_pvs]
                for pv_name in entry_pvs:
                    if no_duplicates:
                        config_pvs.add(pv_name)
                    else:
                        config_pvs.append(pv_name)

        if isinstance(config_pvs, set):
            config_pvs = list(config_pvs)

        return config_pvs
