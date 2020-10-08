"""
Object classes in one place
"""
from dataclasses import dataclass
import time


class PvRecord:
    """
    Contains the PV value and record information from the IOC DB.

    Attributes:
        name:            The name of the PV
        value:           The value of the PV
        record_type:     The record type of the PV. (e.g. cacl, waveform, bi)
        desc:            The description of the PV.
        ioc_name:        The IOC of the PV.
    """
    def __init__(self, name, value, record_type, desc, ioc_name):
        self.name = name
        self.value = value
        self.record_type = record_type
        self.desc = desc
        self.ioc_name = ioc_name

    def set_value(self, value):
        self.value = value


@dataclass
class EpicsVessel:
    """
    For creating and adding a new vessel to the database.

    Attributes and record fields:
        +----------------------------+-------------------+
        | type_id (int):             | OB_OBJECTTYPE_ID  |
        +----------------------------+-------------------+
        | name (str):                | OB_NAME           |
        +----------------------------+-------------------+
        | comment (str):             | OB_COMMENT        |
        +----------------------------+-------------------+
        | pos_info (str):            | OB_POSINFORMATION |
        +----------------------------+-------------------+
        | active (bool):             | OB_ACTIVE         |
        +----------------------------+-------------------+
        | min_val (float):           | OB_MINVALUE       |
        +----------------------------+-------------------+
        | max_val (float):           | OB_MAXVALUE       |
        +----------------------------+-------------------+
        | crit_val (float):          | OB_CRITVALUE      |
        +----------------------------+-------------------+
        | tare (float):              | OB_TARE           |
        +----------------------------+-------------------+
        | span (float):              | OB_SPAN1          |
        +----------------------------+-------------------+
        | zero (float):              | OB_ZERO1          |
        +----------------------------+-------------------+
        | params_valid (bool):       | OB_ENABLED2       |
        +----------------------------+-------------------+
        | display_reversed (bool):   | OB_ENABLED3       |
        +----------------------------+-------------------+
        | interval_short (int):      | OB_SHORTINTERVAL  |
        +----------------------------+-------------------+
        | interval_long (int):       | OB_LONGINTERVAL   |
        +----------------------------+-------------------+
        | quench_time (int):         | OB_QUENCHTIME     |
        +----------------------------+-------------------+
        | quench_current (int):      | OB_QUENCHCURRENT  |
        +----------------------------+-------------------+
        | wait_time (int):           | OB_WAITTIME       |
        +----------------------------+-------------------+
        | measurement_current (int): | OB_MEASCURRENT    |
        +----------------------------+-------------------+
        | adc_loop (int):            | OB_ADCLOOP        |
        +----------------------------+-------------------+
        | fill_timeout (int):        | OB_FILLTIMEOUT    |
        +----------------------------+-------------------+
        | installed_date (str):      | OB_INSTALLED      |
        +----------------------------+-------------------+
        | serial_no (str):           | OB_SERNO          |
        +----------------------------+-------------------+
        | serial_no                  | OB_SERNO          |
        +----------------------------+-------------------+

    """
    type_id: int
    name: str
    comment: str = None
    pos_info: str = None
    active: bool = None
    min_val: float = None
    max_val: float = None
    crit_val: float = None
    tare: float = None
    span: float = None
    zero: float = None
    params_valid: bool = None
    display_reversed: bool = None
    interval_short: int = None
    interval_long: int = None
    quench_time: int = None
    quench_current: int = None
    wait_time: int = None
    measurement_current: int = None
    adc_loop: int = None
    fill_timeout: int = None
    installed_date: str = None  # '%Y-%m-%d %H:%M:%S'
    serial_no: str = None
