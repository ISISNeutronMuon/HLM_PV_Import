from HLM_PV_Import.__main__ import main

import servicemanager
import socket
import os
import sys
import win32event
import win32service
import win32serviceutil
from service_logging import logger, except_hook


class PVImportService(win32serviceutil.ServiceFramework):
    _svc_name_ = "HLMPVImport"
    _svc_display_name_ = "HLM PV Import"
    _svc_description_ = "Helium Level Monitoring - PV Import"

    def __init__(self, args):
        f = open("C:\\Users\\bgd37885\\Desktop\\test.txt", "a")
        f.write(f'args: {args}\n')
        key = win32serviceutil.GetServiceCustomOption("HLMPVImport", 'DB_HE_USER')
        f.write(f'custom option: {key}\n')
        f.close()
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
        except Exception as e:
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
