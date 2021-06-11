from HLM_PV_Import.ca_wrapper import PvMonitors
from HLM_PV_Import.user_config import UserConfig
from HLM_PV_Import.settings import PvImportConfig
from HLM_PV_Import.logger import logger, pv_logger
from HLM_PV_Import.settings import CA
from HLM_PV_Import.db_func import add_measurement, get_obj_id_and_create_if_not_exist
from collections import defaultdict
import time

LOOP_TIMER = PvImportConfig.LOOP_TIMER   # The timer between each PV import loop
EXTERNAL_PVS_UPDATE_INTERVAL = 3600
EXTERNAL_PVS_TASK = 'External PVs'


class PvImport:
    def __init__(self, pv_monitors: PvMonitors, user_config: UserConfig, external_pvs_list: list):
        self.pv_monitors = pv_monitors
        self.config = user_config
        self.external_pvs_list = external_pvs_list  # Configurations for PVs not part of the Helium Recovery PLC
        self.tasks = {}
        self.running = False

        # Initialize tasks
        for obj_id in self.config.object_ids:
            self.tasks[obj_id] = 0
        self.tasks[EXTERNAL_PVS_TASK] = 0

    def start(self):
        """
        Starts the PV data importing loop.
        """
        self.running = True  # in case it was previously stopped

        while self.running:
            time.sleep(LOOP_TIMER)

            # Helium Recovery PLC Measurements
            for object_id in self.config.object_ids:
                # Check the object's next logging time in tasks, if not yet then go to next object_id
                if self.tasks[object_id] > time.time():
                    continue
                # If object is ready to be updated, set curr time + log period in minutes as next run, then proceed
                self.tasks[object_id] = time.time() + (60 * self.config.logging_periods[object_id])

                # Get the object measurement PVs names
                object_meas = self.config.get_entry_measurement_pvs(object_id, full_names=True)

                # Get the measurement PV values
                mea_values = self._get_mea_values(object_meas)

                # If none of the measurement PVs values were found in the PV data,
                # skip to the next object.
                if all(value is None for value in mea_values.values()):
                    logger.warning(f'No PV values for measurement of object {object_id}, skipping. ')
                    continue

                # Create a new measurement with the PV values for the object
                add_measurement(object_id=object_id, mea_values=mea_values)

            # External (Non-PLC) Measurements

            # Update external PV measurements only every 'EXTERNAL_PVS_UPDATE_INTERVAL' seconds
            if self.tasks[EXTERNAL_PVS_TASK] > time.time():
                continue
            # noinspection PyTypeChecker
            self.tasks[EXTERNAL_PVS_TASK] = time.time() + EXTERNAL_PVS_UPDATE_INTERVAL

            for external_pvs_config in self.external_pvs_list:
                for obj_name, mea_pvs in external_pvs_config.pv_config.items():
                    mea_values = self._get_mea_values({f'{i+1}': pv for i, pv in enumerate(mea_pvs)},
                                                      ignore_stale_pvs=True)
                    if all(value is None for value in mea_values.values()):
                        continue

                    comment = f'Non-PLC PVs ({external_pvs_config.name})'
                    obj_id = get_obj_id_and_create_if_not_exist(obj_name, external_pvs_config.objects_type, comment)

                    add_measurement(object_id=obj_id, mea_values=mea_values)

    def stop(self):
        """
        Stop the PV Import loop if it is currently running.
        """
        self.running = False

    def _get_mea_values(self, meas_pv_config: dict, ignore_stale_pvs: bool = False):
        """
        Iterate through the list of PVs, get the values from the PV monitor data dict, and add them to the
        measurement values.

        Args:
            meas_pv_config (dict): The Measurement No./PV Name configuration.
            ignore_stale_pvs (bool): Don't add stale PVs to values, no matter the CA settings.

        Returns:
            (defaultdict): The measurement values.
        """
        mea_values = defaultdict(lambda: None)
        for mea_number, pv_name in meas_pv_config.items():
            # If the measurement doesn't have an assigned PV, go to the next one.
            if not pv_name:
                continue

            # Add the PV value to the measurements. If the PV does not exist in the PV monitors data dict,
            # then skip it. This could happen because of a monitor not receiving updates from the existing PV.
            try:

                # If the PV data is stale, then ignore it. If Add Stale PVs setting is enabled, add it anyway.
                # If called with 'ignore stale PVs' set to True, don't add stale PVs, no matter the CA settings.
                if self.pv_monitors.pv_data_is_stale(pv_name) and not CA.ADD_STALE_PVS and not ignore_stale_pvs:
                    continue

                pv_value = self.pv_monitors.get_pv_data(pv_name)
                mea_values[mea_number] = pv_value
            except Exception as e:
                pv_logger.warning(f'No PV data found for {e}')
                continue

        return mea_values
