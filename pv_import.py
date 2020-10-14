from utilities import get_all_pv_configs


def get_tasks_from_config():
    """
    Gets a dictionary of the PV/Logging Period for each entry in the config file.

    Returns:
        (dict): A PV/Logging Period dictionary.
    """
    tasks = {}
    configs = get_all_pv_configs()
    for pv, config in configs.items():
        tasks[f'{pv}'] = config['logging']

    return tasks

