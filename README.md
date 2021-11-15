# Helium Level Monitoring - HeRecovery DB Populator
 
Service and manager for updating the [HLM Database](https://github.com/SampleEnvironment/He-Management/wiki#helium-level-monitoring-database) with PV data from the [Helium Recovery PLC](https://github.com/ISISComputingGroup/ibex_developers_manual/wiki/Helium-Recovery-PLC) ([Omron FINS](https://github.com/ISISComputingGroup/ibex_developers_manual/wiki/Omron-FINS)).

This repository contains the [HLM PV Import Service](https://github.com/ISISNeutronMuon/HLM_PV_Import/tree/master/HLM_PV_Import) and the [Service Manager](https://github.com/ISISNeutronMuon/HLM_PV_Import/tree/master/ServiceManager). 
For information regarding both, please check the [HLM PV Import Wiki](https://github.com/ISISNeutronMuon/HLM_PV_Import/wiki).

### Links
* [HLM PV Import Wiki](https://github.com/ISISNeutronMuon/HLM_PV_Import/wiki)
* [HLM GAM Database](https://github.com/SampleEnvironment/He-Management/wiki#helium-level-monitoring-database) - the gas management database in which PV values are being imported as object measurements
* [Helium Recovery PLC](https://github.com/ISISComputingGroup/ibex_developers_manual/wiki/Helium-Recovery-PLC) - [FINS PLC](https://github.com/ISISComputingGroup/ibex_developers_manual/wiki/Omron-FINS) - used for monitoring various parameters related to the helium gas recovery system
* [HLM Project Sharepoint](http://www.facilities.rl.ac.uk/isis/projects/heliummgmt/_layouts/viewlsts.aspx?BaseType=1) - project management docs and other useful info
* [HLM View](https://github.com/ISISNeutronMuon/HLM_View) - data display website repo
* [Jenkins Build](https://epics-jenkins.isis.rl.ac.uk/job/HLM%20PV%20Import/) - automated testing

### How to build & run
1. Download the code and pip install requirements.
2. Run `pyinstaller HlmManager.spec` and `pyinstaller HlmService.spec` inside the project root. Both the manager and service should now be bundled, and the .exe files located in `\dist`.
3. Either copy the service `settings.ini` and `pv_config.json` from [HLM Settings, Config and HLM DB.zip](https://github.com/ISISComputingGroup/IBEX/files/5766092/HLM.Settings.Config.and.HLM.DB.zip) to the same directory as `HlmService.exe`, or run `HlmManager\HlmManager.exe` and select the directory path of `HlmService.exe` when prompted, which should create the default PV configuration and service settings files.
4. `HlmService.exe install` via terminal with admin rights, or put [service_setup.zip](https://github.com/ISISComputingGroup/IBEX/files/5766153/service_setup.zip) in the same directory and run it (does the same thing).
5. Run the manager with admin rights for full functionality.
6. Check out the [Service Setup & Manager Manual](https://github.com/ISISNeutronMuon/HLM_PV_Import/wiki/Service-Setup-&-Manager-Manual). 

**Notes**: 
* When builing, update the `B_DATE` (and `VER`, if done any changes) in `ServiceManager\constants.py`.
* Do not forget to set up the database. The schema creation script can be found in `\\isis\inst$\Kits$\CompGroup\Helium Level Meters\For Review`. When first starting the HLM PV Import manager, configure the "DB Connection" settings. The DB user & password are saved in the windows registry as parameters of the service.  
* If it helps with setting-up (to check configuration/settings files/registry etc.), the service is currently running on the server machine, you can check the files there.
* The [Helium Recovery PLC](https://github.com/ISISComputingGroup/ibex_developers_manual/wiki/Helium-Recovery-PLC) must also be set up and running on the machine: [Notes on NDAHEMON static build setup](https://github.com/ISISComputingGroup/ibex_developers_manual/wiki/Helium-Recovery-PLC#ndahemon-fins-setup-notes-procserv-no-ibex)

The service directory should look like this:

```
.
├── logs
│   └── ...
├── HlmService.exe
├── pv_config.json
├── settings.ini
├── service_setup.bat* (optional)
```


The manager can be placed anywhere, as long as it is given the correct service directory path. The service requires the `settings.ini` and `pv_config.json` files. The `service_setup.bat` is optional; logs will be created once the service has run.

### Running in an IDE (e.g. PyCharm)
To test the manager or the service in an IDE (as it's easier to make changes), run `\HlmManager.py` for manager, and `\HLM_PV_Import\__main__.py` for service.

Note that for running the service script directly from the IDE, the PV config and settings.ini will need to be added to the project root.
Depending on the user, the manager's settings and logs may differ (as they are saved in `<user>\AppData\Local\HLM Service Manager`).

### To check test coverege 
To check the test coverge you first need to install coverge `pip install coverage` and then ensure that you can run from command line. This poses an issue with the service mains imports, this can be resolved by editing the virtual environments `activate.ps1` to contain the following in the deactivate function.
```
# The prior PYTHONPATH:
    if (Test-Path -Path Env:_OLD_PYTHON_PATH){
        Copy-Item -Path Env:_OLD_PYTHON_PATH -Destination env:PYTHONPATH
        Remove-Item -Path Env:_OLD_PYTHON_PATH
    }elseif(Test-Path -Path Env:NOPYTHONPATH){
        Remove-Item -Path Env:PYTHONPATH
        Remove-Item -Path Env:NOPYTHONPATH
    }
```
And the following to the end of the file.
```
# Add the venv to the PYTHONPATH
if (Test-Path env:PYTHONPATH) {
    copy-item env:PYTHONPATH env:_OLD_PYTHON_PATH
}else {
    $env:NOPYTHONPATH = "NOPATH"
}
$env:PYTHONPATH = "$(Resolve-Path "$env:VIRTUAL_ENV\..");$env:PYTHONPATH"
```
Once this is the case it should be possible to run `python .\HLM_PV_Import\__main__.py` if this is working correctly coverege should now work properly on the tests.

### Manual tests:
[hlm_manual_system_tests_v1.0.0.xlsx](https://github.com/ISISComputingGroup/IBEX/files/5766350/hlm_manual_system_tests_v1.0.0.xlsx) (feel free to add to this as you run your own tests)

