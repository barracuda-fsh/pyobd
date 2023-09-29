#!/usr/bin/env python
###########################################################################
# obd_sensors.py
#
# Copyright 2004 Donour Sizemore (donour@uchicago.edu)
# Copyright 2009 Secons Ltd. (www.obdtester.com)
# Copyright 2021 Jure Poljsak (https://github.com/barracuda-fsh/pyobd)
#
# This file is part of pyOBD.
#
# pyOBD is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# pyOBD is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pyOBD; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
###########################################################################


def hex_to_int(str):
    i = eval("0x" + str, {}, {})
    return i


def maf(code):
    code = hex_to_int(code)
    return code * 0.00132276


def throttle_pos(code):
    code = hex_to_int(code)
    return code * 100.0 / 255.0


def intake_m_pres(code):  # in kPa
    code = hex_to_int(code)
    return code / 0.14504


def rpm(code):
    code = hex_to_int(code)
    return code / 4


def speed(code):
    code = hex_to_int(code)
    return code / 1.609


def percent_scale(code):
    code = hex_to_int(code)
    return code * 100.0 / 255.0


def timing_advance(code):
    code = hex_to_int(code)
    return (code - 128) / 2.0


def sec_to_min(code):
    code = hex_to_int(code)
    return code / 60


def temp(code):
    code = hex_to_int(code)
    return code - 40


def cpass(code):
    # fixme
    return code


def fuel_trim_percent(code):
    code = hex_to_int(code)
    return (code - 128.0) * 100.0 / 128


def dtc_decrypt(code):
    # first byte is byte after PID and without spaces
    num = hex_to_int(code[:2])  # A byte
    res = []

    if num & 0x80:  # is mil light on
        mil = 1
    else:
        mil = 0

    # bit 0-6 are the number of dtc's.
    num = num & 0x7F

    res.append(num)
    res.append(mil)

    numB = hex_to_int(code[2:4])  # B byte

    for i in range(0, 3):
        res.append(((numB >> i) & 0x01) + ((numB >> (3 + i)) & 0x02))

    numC = hex_to_int(code[4:6])  # C byte
    numD = hex_to_int(code[6:8])  # D byte

    for i in range(0, 7):
        res.append(((numC >> i) & 0x01) + (((numD >> i) & 0x01) << 1))

    res.append(((numD >> 7) & 0x01))  # EGR SystemC7  bit of different

    return res


def hex_to_bitstring(str):
    bitstring = ""
    for i in str:
        # silly type safety, we don't want to eval random stuff
        if type(i) == type(""):
            v = eval("0x%s" % i)
            if v & 8:
                bitstring += "1"
            else:
                bitstring += "0"
            if v & 4:
                bitstring += "1"
            else:
                bitstring += "0"
            if v & 2:
                bitstring += "1"
            else:
                bitstring += "0"
            if v & 1:
                bitstring += "1"
            else:
                bitstring += "0"
    return bitstring


class Sensor:
    def __init__(self, sensorName, sensorcommand, sensorValueFunction, u):
        self.name = sensorName
        self.cmd = sensorcommand
        self.value = sensorValueFunction
        self.unit = u


SENSORS = [
    Sensor("          Supported PIDs", "0100", hex_to_bitstring, ""),
    Sensor("Status Since DTC Cleared", "0101", dtc_decrypt, ""),
    Sensor("DTC Causing Freeze Frame", "0102", cpass, ""),
    Sensor("      Fuel System Status", "0103", cpass, ""),
    Sensor("   Calculated Load Value", "0104", percent_scale, ""),
    Sensor("     Coolant Temperature", "0105", temp, "C"),
    Sensor("    Short Term Fuel Trim", "0106", fuel_trim_percent, "%"),
    Sensor("     Long Term Fuel Trim", "0107", fuel_trim_percent, "%"),
    Sensor("    Short Term Fuel Trim", "0108", fuel_trim_percent, "%"),
    Sensor("     Long Term Fuel Trim", "0109", fuel_trim_percent, "%"),
    Sensor("      Fuel Rail Pressure", "010A", cpass, ""),
    Sensor("Intake Manifold Pressure", "010B", intake_m_pres, "psi"),
    Sensor("              Engine RPM", "010C", rpm, ""),
    Sensor("           Vehicle Speed", "010D", speed, "MPH"),
    Sensor("          Timing Advance", "010E", timing_advance, "degrees"),
    Sensor("         Intake Air Temp", "010F", temp, "C"),
    Sensor("     Air Flow Rate (MAF)", "0110", maf, "lb/min"),
    Sensor("       Throttle Position", "0111", throttle_pos, "%"),
    Sensor("    Secondary Air Status", "0112", cpass, ""),
    Sensor("  Location of O2 sensors", "0113", cpass, ""),
    Sensor("        O2 Sensor: 1 - 1", "0114", fuel_trim_percent, "%"),
    Sensor("        O2 Sensor: 1 - 2", "0115", fuel_trim_percent, "%"),
    Sensor("        O2 Sensor: 1 - 3", "0116", fuel_trim_percent, "%"),
    Sensor("        O2 Sensor: 1 - 4", "0117", fuel_trim_percent, "%"),
    Sensor("        O2 Sensor: 2 - 1", "0118", fuel_trim_percent, "%"),
    Sensor("        O2 Sensor: 2 - 2", "0119", fuel_trim_percent, "%"),
    Sensor("        O2 Sensor: 2 - 3", "011A", fuel_trim_percent, "%"),
    Sensor("        O2 Sensor: 2 - 4", "011B", fuel_trim_percent, "%"),
    Sensor("         OBD Designation", "011C", cpass, ""),
    Sensor("  Location of O2 sensors", "011D", cpass, ""),
    Sensor("        Aux input status", "011E", cpass, ""),
    Sensor(" Time Since Engine Start", "011F", sec_to_min, "min"),
    Sensor("  Engine Run with MIL on", "014E", sec_to_min, "min"),
]


# ___________________________________________________________


def test():
    for i in SENSORS:
        print(i.name, i.value("F"))


if __name__ == "__main__":
    test()
