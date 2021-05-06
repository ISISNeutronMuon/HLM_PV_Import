import servicemanager
import socket
import sys
import win32event
import win32service
import win32serviceutil

import HLM_PV_Import.__main__ as main_
from HLM_PV_Import.settings import Service
from HLM_PV_Import.logger import log_exception, logger


class PVImportService(win32serviceutil.ServiceFramework):
    _svc_name_ = Service.NAME
    _svc_display_name_ = Service.DISPLAY_NAME
    _svc_description_ = Service.DESCRIPTION

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)

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

    @staticmethod
    def main():
        logger.info("Starting service")
        main_.main()

    @staticmethod
    def stop():
        logger.info("Stop request received")
        main_.pv_import.stop()


if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(PVImportService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(PVImportService)
