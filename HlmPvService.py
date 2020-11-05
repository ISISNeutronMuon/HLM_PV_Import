from HLM_PV_Import.__main__ import main
from HLM_PV_Import.constants import Service

import servicemanager
import socket
import sys
import win32event
import win32service
import win32serviceutil
from service_logging import logger, except_hook


class PVImportService(win32serviceutil.ServiceFramework):
    _svc_name_ = Service.NAME
    _svc_display_name_ = Service.DISPLAY_NAME
    _svc_description_ = Service.DESCRIPTION

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)

    def SvcStop(self):
        logger.info("Stop request received")
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        # sys.excepthook doesn't seem to work in this routine -
        # apparently, everything is handled by the ServiceFramework machinery
        try:
            logger.info("Starting service")
            main()
        except Exception:
            except_hook(*sys.exc_info())

        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_, ''))


if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(PVImportService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(PVImportService)
