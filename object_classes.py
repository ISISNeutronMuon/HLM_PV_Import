"""
Object classes in one place
"""


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


# class Coordinator:
#     """
#     The coordinator object class.
#
#     attributes:
#         OB_OBJECTTYPE_ID (int): ID of the type of this object. Set to 1 (coordinator).
#         OB_NAME (str): Name of object
#         OB_ADDRESS (str): The XBee Address (or IP for LAN Gascount. Mod.)
#         OB_COMMENT (str): Comments regarding this object
#         OB_POSINFORMATION (str): Physical position of the device
#         OB_LASTTIMEACTIVE (TDateTime):
#         OB_OUTOFOPERARTION (int):
#         OB_ACTIVE (boolean):
#         OB_IP (str): The IP address of the device
#         OB_COMPORT (str): Device COM Port
#         OB_NW_ID (int): ID of the network this object is on
#         OB_INSTALLED (TDateTime):
#         OB_SERNO (str):
#     """
#     def __init__(self, name, address, comment, posinformation, ip, comport, nw_id):
#         self.name = name
#         self.address = address
#         self.comment = comment
#         self.posinformation = posinformation
#         self.ip = ip
#         self.comport = comport
#         self.nw_id = nw_id
