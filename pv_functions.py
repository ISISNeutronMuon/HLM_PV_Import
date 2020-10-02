import db_functions
import ca_wrapper as ca_wrapper
import utilities


class PVRecord:
    """
    Contains the PV value and record information from the IOC DB.

    attributes:
        name            The name of the PV
        value           The value of the PV
        record_type     The record type of the PV. (e.g. cacl, waveform, bi)
        desc            The description of the PV.
        ioc_name        The IOC of the PV.
    """
    def __init__(self, name, value, record_type, desc, ioc_name):
        self.name = name
        self.value = value
        self.record_type = record_type
        self.desc = desc
        self.ioc_name = ioc_name

    def set_value(self, value):
        self.value = value


def get_pv_names():
    """
    Gets the list of names for the PVs currently in the IOC.

    Returns:
        The list of PV names.
    """
    records = db_functions.get_pv_records('pvname')
    return records


def get_pv_values():
    """
    Gets the list of values for the PVs currently in the IOC.

    Returns:
        The list of PV values.
    """
    values = []
    records = db_functions.get_pv_records('pvname')

    for pv in records:
        val = ca_wrapper.get_pv_value(pv)
        values.append(val)
    return values


def get_pv_names_and_values():
    """
    Gets the dictionary of names:values for the PVs currently in the IOC.

    Returns:
        The dict of PV names and values.
    """
    pv_dict = {}
    records = db_functions.get_pv_records('pvname')

    for pv in records:
        value = ca_wrapper.get_pv_value(pv)
        pv_dict[pv] = value

    return pv_dict


def get_pv_objects():
    """
    Gets a list of :class:`PVRecord` objects containing the value and record data for each PV currently in the IOC.

    Returns:
        The list of PV objects.
    """
    obj_list = []
    records = db_functions.get_pv_records()
    for pv in records:
        # 0: pvname, 1: record_type, 2: record_desc, 3: iocname
        obj = PVRecord(
            pv[0].decode('utf-8'),                             # pvname
            ca_wrapper.get_pv_value(pv[0].decode('utf-8')),    # value
            pv[1],                                             # record_type
            pv[2],                                             # record_desc
            pv[3]                                              # iocname
        )
        obj_list.append(obj)

    return obj_list
