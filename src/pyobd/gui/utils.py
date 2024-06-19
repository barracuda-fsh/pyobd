import sys
from enum import IntEnum
from pathlib import Path


class AppTab(IntEnum):
    UNKNOWN = -1
    STATUS = 0
    TESTS = 1
    SENSORS = 2
    DTC = 3
    FREEZE_FRAME = 4
    SINGLE_GRAPH = 5
    MULTIPLE_GRAPHS = 6
    TRACE = 7

def resource_path(relative_path: str | Path) -> Path:
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = Path(sys._MEIPASS).resolve()
    except AttributeError:
        base_path = Path(__file__).resolve().parent.parent

    return base_path / relative_path


TESTS = [
    "MISFIRE_MONITORING",
    "FUEL_SYSTEM_MONITORING",
    "COMPONENT_MONITORING",
    "CATALYST_MONITORING",
    "HEATED_CATALYST_MONITORING",
    "EVAPORATIVE_SYSTEM_MONITORING",
    "SECONDARY_AIR_SYSTEM_MONITORING",
    "OXYGEN_SENSOR_MONITORING",
    "OXYGEN_SENSOR_HEATER_MONITORING",
    "EGR_VVT_SYSTEM_MONITORING",
    "NMHC_CATALYST_MONITORING",
    "NOX_SCR_AFTERTREATMENT_MONITORING",
    "BOOST_PRESSURE_MONITORING",
    "EXHAUST_GAS_SENSOR_MONITORING",
    "PM_FILTER_MONITORING",
]
