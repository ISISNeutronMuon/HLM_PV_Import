from HLM_PV_Import.ca_wrapper import PvMonitors
from HLM_PV_Import.user_config import UserConfig
from HLM_PV_Import.db_functions import add_measurement
from HLM_PV_Import.settings import PvImportConfig
from HLM_PV_Import.logger import log_error
from HLM_PV_Import.settings import CA
from collections import defaultdict
import time

LOOP_TIMER = PvImportConfig.LOOP_TIMER   # The timer between each PV import loop


class PvImport:
    def __init__(self, pv_monitors: PvMonitors, user_config: UserConfig):
        self.pv_monitors = pv_monitors
        self.config = user_config
        self.tasks = {}
        self.running = False

    def set_up(self):
        """
        Requirements and checks before importing PV data.
        """
        # Check if the user configuration is valid
        self.config.run_checks()

        # Initialize tasks
        for record in self.config.records:
            self.tasks[record] = 0

    def start(self):
        """
        Starts the PV data importing loop.
        """
        self.running = True  # in case it was previously stopped
        start_time = time.time()

        while self.running:
            time.sleep(LOOP_TIMER - ((time.time() - start_time) % LOOP_TIMER))

            # For debugging
            # pv_data = copy.deepcopy(self.pv_monitors.get_data())
            # print(f"({datetime.now().strftime('%H:%M:%S')}) {len(pv_data)} {pv_data}")

            for record in self.config.records:

                # Check record next logging time in tasks, if not yet then go to next record
                if self.tasks[record] > time.time():
                    continue
                # If record is ready to be updated, set curr time + log period in minutes as next run, then proceed
                self.tasks[record] = time.time() + (60 * self.config.logging_periods[record])

                # Get the entry record's PVs, the initialize the blank measurement values dict (with None values)
                record_meas = self.config.get_record_measurement_pvs(record, full_names=True)
                mea_values = defaultdict(lambda: None)

                # Iterate through the list of PVs, get the values from the PV monitor data dict, and add them to the
                # measurement values.
                for mea_number, pv_name in record_meas.items():
                    # If the measurement doesn't have an assigned PV, go to the next one.
                    if not pv_name:
                        continue

                    # Add the PV value to the measurements. If the PV does not exist in the PV monitors data dict,
                    # then skip it. This could happen because of a monitor not receiving updates from the existing PV.
                    try:

                        # If the PV data is stale, then ignore it. If Add Stale PVs setting is enabled, add it anyway.
                        if self.pv_monitors.pv_data_is_stale(pv_name) and not CA.ADD_STALE_PVS:
                            continue

                        pv_value = self.pv_monitors.get_pv_data(pv_name)
                        mea_values[mea_number] = pv_value
                    except Exception as e:
                        log_error(f'{e}')
                        continue

                # If none of the measurement PVs values were found from the PV monitors data dict,
                # skip to the next record.
                if all(value is None for value in mea_values.values()):
                    print(f'No PV values for object with record ID {record}, skipping. ')
                    continue

                # Add a measurement with the values for the record/object
                add_measurement(object_id=record, mea_values=mea_values, mea_valid=True)

    def stop(self):
        """
        Stop the PV Import loop if it is currently running.
        """
        self.running = False
