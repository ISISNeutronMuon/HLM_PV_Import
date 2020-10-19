from lxml import etree
import xmltodict
from iteration_utilities import duplicates, unique_everseen
from err_logger import log_config_error
from constants import UserConfig
from db_functions import get_object_id
from pv_functions import get_pv_names


def get_pv_config(pv_name):
    """
    Get the configuration of given PV.

    Args:
        pv_name (str): Name of the PV

    Returns:
        (dict): The PV user configuration.
    """
    return_val = None
    config_file = UserConfig.PATH
    with open(config_file, 'rb') as f:
        config = xmltodict.parse(f.read(), dict_constructor=dict)

        for entry in config[UserConfig.ROOT][UserConfig.ENTRY]:
            if entry[UserConfig.MEAS][UserConfig.PV]:
                if pv_name in entry[UserConfig.MEAS][UserConfig.PV]:
                    return_val = entry

        if not return_val:
            log_config_error(pv_name=f'{pv_name}', config_file=UserConfig.FILE, print_err=True)

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

        Returns:
            (boolean): True if valid (no duplicate entries), False if invalid (same record name used twice)

        Raises:
            ValueError: if duplicate record names were found
        """
        duplicate_records = list(unique_everseen(duplicates(self.records)))
        if duplicate_records:
            raise ValueError(f'User configuration contains duplicate entry record names: {duplicate_records}')

    def check_config_records_tag_not_empty(self):
        """
        Throws error if a tag in the user configuration has an empty body (value None).

        Raises:
            ValueError: If one or more empty tags were found.
        """
        for record in self.records:
            if not record:
                raise ValueError('One or more elements in the user configuration is empty/null/None.')

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
            raise ValueError(f'User configuration contains record names that were not found in the DB: {not_found}')

    def check_measurement_pvs_exist(self):
        """
        Checks whether the measurement PVs from the user configuration exist in the database.

        Raises:
            ValueError: If one or more PVs were not found.
        """
        config_pvs = set()

        entries = self.configs[UserConfig.ENTRY]

        if not isinstance(entries, list):
            entries = [entries]

        for entry in entries:
            if entry[UserConfig.MEAS][UserConfig.PV]:
                pvs = entry[UserConfig.MEAS][UserConfig.PV]
                if not isinstance(pvs, list):
                    pvs = [pvs]
                for pv_name in pvs:
                    config_pvs.add(pv_name)

        not_found = []
        for pv in config_pvs:
            if pv not in self.available_pvs:
                not_found.append(pv)

        if not_found:
            raise ValueError(f'One or more PVs in the user configuration does not exist: {not_found}')
