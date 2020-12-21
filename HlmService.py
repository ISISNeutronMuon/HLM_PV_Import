import servicemanager
import socket
import sys
import os
import win32event
import win32service
import win32serviceutil
from service_logging import logger, log_exception

from HLM_PV_Import.settings import Service
from HLM_PV_Import.ca_wrapper import PvMonitors
from HLM_PV_Import.user_config import UserConfig
from HLM_PV_Import.pv_import import PvImport
from HLM_PV_Import.settings import CA


class PVImportService(win32serviceutil.ServiceFramework):
    _svc_name_ = Service.NAME
    _svc_display_name_ = Service.DISPLAY_NAME
    _svc_description_ = Service.DESCRIPTION

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)
        self.pv_import = None
        self.pv_monitors = None

    # noinspection PyBroadException
    # noinspection PyPep8Naming
    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)

        try:
            self.stop()
        except Exception:
            log_exception(*sys.exc_info())

        win32event.SetEvent(self.hWaitStop)
        self.ReportServiceStatus(win32service.SERVICE_STOPPED)

    # noinspection PyBroadException
    # noinspection PyPep8Naming
    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_, ''))
        try:
            self.main()
        except Exception:
            log_exception(*sys.exc_info())

    def main(self):
        logger.info("Starting service")

        # Setup the channel access address list in order to connect to PVs
        os.environ['EPICS_CA_ADDR_LIST'] = CA.EPICS_CA_ADDR_LIST

        # Get the user configuration and the list of measurement PVs
        config = UserConfig()
        pv_list = config.get_measurement_pvs(no_duplicates=True, full_names=True)

        # Initialize the PV monitoring and set up the monitors for each measurement PV from the user config
        self.pv_monitors = PvMonitors(pv_list)

        # Initialize and set-up the PV import in charge of preparing the PV data, handling logging periods & tasks,
        # running content checks for the user config, and looping through each record every few seconds to check for
        # records scheduled to be updated with a new measurement.
        self.pv_import = PvImport(self.pv_monitors, config)
        self.pv_import.set_up()

        # Start the monitors and continuously store the PV data received on every update
        self.pv_monitors.start_monitors()

        # Start the PV import main loop to check each record
        self.pv_import.start()

    def stop(self):
        logger.info("Stop request received")
        self.pv_import.stop()


if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(PVImportService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(PVImportService)
