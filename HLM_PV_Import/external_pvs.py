""" PVs that are not part of the Helium Recovery PLC """
from HLM_PV_Import.ca_wrapper import get_instrument_list
from HLM_PV_Import.settings import DBTypeIDs


class MercuryPVs:
    def __init__(self):
        self.full_inst_list = get_instrument_list()

        self.instruments = [x['name'] for x in self.full_inst_list]
        self.ignored_instruments = ['DEMO', 'DETMON', 'RIKENFE', 'MUONFE', 'ENGINX', 'INES', 'NIMROD', 'SANDALS',
                                    'IMAT', 'ALF', 'CRISP', 'INTER', 'LOQ', 'SURF', 'TOSCA', 'VESUVIO']
        # Add _SETUP instruments to ignored
        self.ignored_instruments.extend([x['name'] for x in self.full_inst_list if '_SETUP' in x['name']])
        self.IOCs = ['MERCURY_01', 'MERCURY_02']
        self.PVs = ['LEVEL:1:HELIUM']  # max 5

        self.inst_to_check = list(set(self.instruments) ^ set(self.ignored_instruments))
        self.prefixes = {x['name']: x['pvPrefix'] for x in self.full_inst_list if x['name'] in self.inst_to_check}

        self.pv_config = self._get_config()

        self.name = 'Mercury Cryostat Controllers'
        self.objects_type = DBTypeIDs.MERCURY_CRYOSTAT

    def _get_config(self):
        pv_config = {}
        for name, prefix in self.prefixes.items():
            for ioc in self.IOCs:
                obj_name = f'{name} {ioc}'
                pv_config[obj_name] = [f'{prefix}{ioc}:{pv}' for pv in self.PVs]
        return pv_config

    def get_full_pv_list(self):
        return [f'{prefix}{ioc}:{pv}' for prefix in self.prefixes.values() for ioc in self.IOCs for pv in self.PVs]
