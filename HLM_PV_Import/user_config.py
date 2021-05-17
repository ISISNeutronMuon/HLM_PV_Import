from iteration_utilities import duplicates, unique_everseen
from HLM_PV_Import.logger import logger
from HLM_PV_Import.settings import PVConfig, CA
from HLM_PV_Import.ca_wrapper import get_connected_pvs
from HLM_PV_Import.db_func import get_object
import json

from shared.utils import get_full_pv_name


class UserConfig:
    """
    User configuration class that stores the entries, object IDs, available PVs, and methods to work with them,
    including config schema and content validation.
    """

    def __init__(self):
        self.entries = self._get_all_entries()
        self.object_ids = [entry[PVConfig.OBJ] for entry in self.entries]
        self.logging_periods = {entry[PVConfig.OBJ]: entry[PVConfig.LOG_PERIOD] for entry in self.entries}

        # Run config checks
        try:
            self._check_entries_have_object_ids()
            self._check_entries_have_measurement_pvs()
            self._check_no_duplicate_object_ids()
            self._check_objects_exist()
            self._check_measurement_pvs_connect()
        except PVConfigurationException as e:
            logger.error(e)
            raise e

    def _check_no_duplicate_object_ids(self):
        """
        Checks if all object IDs are unique.

        Raises:
            ValueError: if duplicate IDs were found
        """
        duplicate_obj_ids = list(unique_everseen(duplicates(self.object_ids)))
        if duplicate_obj_ids:
            raise PVConfigurationException(f'User configuration entries contain duplicate'
                                           f'object IDs: {duplicate_obj_ids}')

    def _check_entries_have_object_ids(self):
        """
        Throws error if a tag in the user configuration has an empty body (value None).

        Raises:
            ValueError: If one or more empty tags were found.
        """
        for obj_id in self.object_ids:
            if not obj_id:
                raise PVConfigurationException('One or more entries in the user configuration '
                                               'does not have an object ID.')

    def _check_objects_exist(self):
        """
        Checks if the object IDs from the user configuration exist in the database.

        Raises:
            ValueError: If one or more object IDs were not found in the database.
        """
        not_found = []
        for obj_id in self.object_ids:
            if not get_object(obj_id):
                not_found.append(obj_id)

        if not_found:
            raise PVConfigurationException(f'User configuration contains objects with IDs '
                                           f'that were not found in the DB: {not_found}')

    def _check_measurement_pvs_connect(self):
        """
        Checks whether the measurement PVs from the user configuration exist in the database.

        Raises:
            ValueError: If one or more PVs were not found.
        """
        logger.info('PVConfig: Checking measurement PVs...')
        config_pvs = self.get_measurement_pvs(no_duplicates=True, full_names=True)
        connected_pvs = get_connected_pvs(config_pvs)
        not_connected = set(config_pvs) ^ set(connected_pvs)

        if not_connected:
            logger.warning(f'PVConfig: Could not connect to one or more PVs: {not_connected}')
        else:
            logger.info('PVConfig: All PVs connected.')

    def _check_entries_have_measurement_pvs(self):
        """
        Verifies that each entry has at least one existing PV in its measurements.

        Raises:
            ValueError: If one or more entries has no measurement PVs.
        """
        objects_with_no_pvs = []
        for obj_id in self.object_ids:
            try:
                if not self.get_entry_measurement_pvs(obj_id):
                    objects_with_no_pvs.append(obj_id)
            except KeyError:
                objects_with_no_pvs.append(obj_id)

        if objects_with_no_pvs:
            raise PVConfigurationException(f'Objects {objects_with_no_pvs} have no measurement PVs.')

    def get_measurement_pvs(self, no_duplicates=True, full_names=False):
        """
        Gets a list of the measurement PVs, ignoring empty/null measurements.

        Args:
            no_duplicates (boolean, optional): If one PV is present in multiple entries, add it to the list
                only once, Defaults to True.
            full_names (boolean, optional): Get the PV names with their prefix and domain, Defaults to False.

        Returns:
            (list): The list of PVs
        """
        config_pvs = []

        for entry in self.entries:
            measurements = entry[PVConfig.MEAS]
            for pv_name in measurements.values():
                if pv_name:
                    config_pvs.append(pv_name)

        if full_names:
            config_pvs = [get_full_pv_name(pv_name, prefix=CA.PV_PREFIX, domain=CA.PV_DOMAIN) for pv_name in config_pvs]

        if no_duplicates:
            config_pvs = set(config_pvs)

        if isinstance(config_pvs, set):
            config_pvs = list(config_pvs)

        return config_pvs

    def get_entry_measurement_pvs(self, object_id, full_names=False):
        """
        Get the measurement PVs of the entry with the given object ID, ignoring empty/null ones.

        Args:
            object_id (str): The object ID.
            full_names (boolean, optional): Get the PV names with their prefix and domain, Defaults to False.

        Returns:
            (dict): The measurements PVs, in measurement number/pv name pairs.
        """
        # Get the measurements of the entry with the given object_id, None if not found
        entry_meas = next((x[PVConfig.MEAS] for x in self.entries if x[PVConfig.OBJ] == object_id), None)
        return {key: get_full_pv_name(val, prefix=CA.PV_PREFIX, domain=CA.PV_DOMAIN)
                if full_names else val for key, val in entry_meas.items() if val}

    @staticmethod
    def _get_all_entries():
        """
        Get all entries from the configuration as a list.

        Returns:
            (list): The configuration entries.

        Raises:
            PVConfigurationException: If the configuration file is either empty or does not have at least one entry.
        """
        config_file = PVConfig.PATH
        with open(config_file) as f:
            data = json.load(f)
            data = data[PVConfig.ROOT]

            if not data:
                err_msg = 'No entries have been found in the configuration file.'
                logger.error(err_msg)
                raise PVConfigurationException(err_msg)

            return data


class PVConfigurationException(ValueError):
    """
    There is a problem with the PV configuration.
    """

    def __init__(self, err_msg):
        super(PVConfigurationException, self).__init__(err_msg)
