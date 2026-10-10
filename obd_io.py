#!/usr/bin/env python
###########################################################################
# odb_io.py
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

from pdb import set_trace as bp
import serial
from serial.tools import list_ports
import string
import time
from math import ceil
import wx #due to debugEvent messaging

import re

import obd_sensors

from obd_sensors import hex_to_int

import obd
import decimal
import math


class _FakeMonitorStatus:
    def __init__(self, available=True, complete=True):
        self.available = available
        self.complete = complete


class _FakeStatusValue:
    def __init__(self):
        monitor_names = [
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
        for name in monitor_names:
            setattr(self, name, _FakeMonitorStatus(True, True))

        self.MIL = False
        self.DTC_count = 0
        self.ignition_type = "spark"

    def __str__(self):
        return "MIL OFF, DTC Count: 0"


class _FakeMisfireValue:
    def __init__(self, count):
        self.MISFIRE_COUNT = count


class _FakeQuantity:
    def __init__(self, magnitude, unit=""):
        self.magnitude = float(magnitude)
        self.unit = unit

    def __str__(self):
        if self.unit:
            return f"{self.magnitude:.2f} {self.unit}"
        return f"{self.magnitude:.2f}"


class _FakeResponse:
    def __init__(self, value=None):
        self.value = value

    def is_null(self):
        return self.value is None


class _FakeInterface:
    def __init__(self, baudrate):
        try:
            self._baudrate = int(baudrate)
        except Exception:
            self._baudrate = 38400

    def baudrate(self):
        return self._baudrate


class _DemoConnection:
    def __init__(self, baudrate=None):
        self._start = time.time()
        self._dtc_active = [("P0301", "Cylinder 1 Misfire Detected")]
        self._freeze_dtc = ("P0301", "Cylinder 1 Misfire Detected")
        self.interface = _FakeInterface(baudrate)

    def status(self):
        return "Car Connected"

    def close(self):
        return None

    def port_name(self):
        return "DEMO"

    def protocol_name(self):
        return "SAE J1979 (Demo)"

    def _seconds(self):
        return max(0.0, time.time() - self._start)

    def _wave(self, period=6.0):
        s = self._seconds()
        return math.sin((2.0 * math.pi * s) / max(period, 0.2))

    def _command_code(self, command):
        code = getattr(command, "command", b"")
        if isinstance(code, bytes):
            return code
        if isinstance(code, str):
            return code.encode("ascii", errors="ignore")
        return b""

    def query(self, command):
        code = self._command_code(command)

        # Adapter info
        if command == obd.commands.ELM_VERSION:
            return _FakeResponse("ELM327 v2.1 (Demo)")
        if command == obd.commands.ELM_VOLTAGE:
            volts = 13.8 + 0.3 * self._wave(9.0)
            return _FakeResponse(_FakeQuantity(volts, "V"))
        if command == obd.commands.VIN:
            return _FakeResponse(b"DEMO0000000000001")

        # Keepalive
        if command == obd.commands.RPM:
            rpm = 900 + 350 * self._wave(5.0)
            return _FakeResponse(_FakeQuantity(max(700, rpm), "rpm"))

        # Readiness/monitor status (0101)
        if code in (b"0101", b"0141"):
            return _FakeResponse(_FakeStatusValue())

        # Fuel system status (0103)
        if code in (b"0103", b"0203"):
            return _FakeResponse(("Closed loop", "Closed loop"))

        # O2 sensor location (0113)
        if code in (b"0113", b"0213"):
            return _FakeResponse({1: [True, True, False, False], 2: [False, False, False, False]})

        # Mode 03/07/04 DTC handling
        if command == obd.commands.GET_DTC:
            return _FakeResponse(list(self._dtc_active))
        if command == obd.commands.FREEZE_DTC:
            return _FakeResponse(self._freeze_dtc)
        if command == obd.commands["CLEAR_DTC"]:
            self._dtc_active = []
            self._freeze_dtc = ("P0000", "No stored freeze code")
            return _FakeResponse("OK")

        # Misfire monitor commands used in tests tab.
        monitor_names = [
            "MONITOR_MISFIRE_CYLINDER_1",
            "MONITOR_MISFIRE_CYLINDER_2",
            "MONITOR_MISFIRE_CYLINDER_3",
            "MONITOR_MISFIRE_CYLINDER_4",
            "MONITOR_MISFIRE_CYLINDER_5",
            "MONITOR_MISFIRE_CYLINDER_6",
            "MONITOR_MISFIRE_CYLINDER_7",
            "MONITOR_MISFIRE_CYLINDER_8",
            "MONITOR_MISFIRE_CYLINDER_9",
            "MONITOR_MISFIRE_CYLINDER_10",
            "MONITOR_MISFIRE_CYLINDER_11",
            "MONITOR_MISFIRE_CYLINDER_12",
        ]
        for idx, name in enumerate(monitor_names, start=1):
            if hasattr(obd.commands, name) and command == getattr(obd.commands, name):
                count = int(abs(self._wave(7.0 + idx * 0.2)) * 3)
                return _FakeResponse(_FakeMisfireValue(count))

        # Common live PID values for sensors and graphs.
        if code in (b"0104", b"0204"):
            return _FakeResponse(_FakeQuantity(32 + 8 * self._wave(7.0), "%"))
        if code in (b"0105", b"0205"):
            return _FakeResponse(_FakeQuantity(87 + 6 * self._wave(14.0), "C"))
        if code in (b"0106", b"0206"):
            return _FakeResponse(_FakeQuantity(1.5 + 4.0 * self._wave(9.0), "%"))
        if code in (b"0107", b"0207"):
            return _FakeResponse(_FakeQuantity(0.7 + 3.0 * self._wave(10.0), "%"))
        if code in (b"0108", b"0208"):
            return _FakeResponse(_FakeQuantity(1.0 + 4.0 * self._wave(8.5), "%"))
        if code in (b"0109", b"0209"):
            return _FakeResponse(_FakeQuantity(0.3 + 3.0 * self._wave(9.5), "%"))
        if code in (b"010A", b"020A"):
            return _FakeResponse(_FakeQuantity(42 + 3 * self._wave(6.5), "psi"))
        if code in (b"010B", b"020B"):
            return _FakeResponse(_FakeQuantity(12 + 2 * self._wave(8.0), "psi"))
        if code in (b"010D", b"020D"):
            return _FakeResponse(_FakeQuantity(35 + 10 * self._wave(6.0), "mph"))
        if code in (b"010E", b"020E"):
            return _FakeResponse(_FakeQuantity(18 + 6 * self._wave(7.5), "degrees"))
        if code in (b"010F", b"020F"):
            return _FakeResponse(_FakeQuantity(30 + 4 * self._wave(10.0), "C"))
        if code in (b"0110", b"0210"):
            return _FakeResponse(_FakeQuantity(1.9 + 0.4 * self._wave(5.0), "lb/min"))
        if code in (b"0111", b"0211"):
            return _FakeResponse(_FakeQuantity(22 + 9 * self._wave(4.5), "%"))
        if code in (b"0112", b"0212"):
            return _FakeResponse("Upstream")
        if code in (b"0114", b"0214"):
            return _FakeResponse(_FakeQuantity(0.18 + 0.07 * self._wave(8.0), "V"))
        if code in (b"0115", b"0215"):
            return _FakeResponse(_FakeQuantity(0.20 + 0.08 * self._wave(8.5), "V"))
        if code in (b"0116", b"0216"):
            return _FakeResponse(_FakeQuantity(0.19 + 0.06 * self._wave(9.0), "V"))
        if code in (b"0117", b"0217"):
            return _FakeResponse(_FakeQuantity(0.17 + 0.08 * self._wave(7.5), "V"))
        if code in (b"0118", b"0218"):
            return _FakeResponse(_FakeQuantity(0.16 + 0.07 * self._wave(8.2), "V"))
        if code in (b"0119", b"0219"):
            return _FakeResponse(_FakeQuantity(0.19 + 0.06 * self._wave(9.2), "V"))
        if code in (b"011A", b"021A"):
            return _FakeResponse(_FakeQuantity(0.21 + 0.07 * self._wave(8.7), "V"))
        if code in (b"011B", b"021B"):
            return _FakeResponse(_FakeQuantity(0.18 + 0.07 * self._wave(7.7), "V"))
        if code in (b"011C", b"021C"):
            return _FakeResponse("OBD II")
        if code in (b"011D", b"021D"):
            return _FakeResponse("2 banks")
        if code in (b"011E", b"021E"):
            return _FakeResponse("PTO off")
        if code in (b"011F", b"021F"):
            minutes = self._seconds() / 60.0
            return _FakeResponse(_FakeQuantity(minutes, "min"))

        # Fallback: return a generic value for most mode 01/02 PIDs.
        if code.startswith(b"01") or code.startswith(b"02"):
            baseline = 20.0 + ((sum(code) % 40) / 2.0)
            return _FakeResponse(_FakeQuantity(baseline + 5.0 * self._wave(8.0), "u"))

        return _FakeResponse(None)


def truncate(num, n):
    integer = int(num * (10**n))/(10**n)
    return float(integer)

GET_DTC_COMMAND   = "03"
CLEAR_DTC_COMMAND = "04"
GET_FREEZE_DTC_COMMAND = "07"
import traceback
from debugEvent import *
import logging
logger = logging.getLogger(__name__)


class OBDConnection:

    def __init__(self,portnum,_notify_window, baud, SERTIMEOUT,RECONNATTEMPTS, FAST):
        self._notify_window = _notify_window
        if baud == 'AUTO':
            baud = None
        original_baud = baud
        if portnum == 'AUTO':
            portnum = None
        if FAST == 'FAST':
            FAST = True
        else:
            FAST = False

        # Translate logical adapter target (Wi-Fi/Bluetooth/Serial/AUTO) to a pyserial URL or port.
        portnum = self._normalize_adapter_target(portnum)

        class _DisconnectedConnection:
            def __init__(self, status_text="Disconnected"):
                self._status_text = status_text

            def status(self):
                return self._status_text

            def close(self):
                return None

            def port_name(self):
                return "----"

        self.connection = _DisconnectedConnection("Disconnected")

        if portnum == 'DEMO':
            self.connection = _DemoConnection(original_baud)
            wx.PostEvent(self._notify_window, DebugEvent([1, "Demo mode active (simulated vehicle data)."] ))
            return

        if portnum is None:
            candidate_ports = [p.device for p in list_ports.comports() if p.device]
            candidate_ports = sorted(candidate_ports)
            if not candidate_ports:
                wx.PostEvent(self._notify_window, DebugEvent([1, "No connected serial ports detected."]))
                self.connection = _DisconnectedConnection("Not Connected")
                return
            port_attempts = candidate_ports
        else:
            max_attempts = max(1, int(RECONNATTEMPTS))
            port_attempts = [portnum] * max_attempts

        for counter, candidate_port in enumerate(port_attempts, start=1):
            wx.PostEvent(self._notify_window, DebugEvent([2, "Connection attempt:" + str(counter) + " (" + str(candidate_port) + ")"]))
            try:
                self.connection.close()
            except:
                pass

            try:
                self.connection = obd.OBD(
                    portstr=candidate_port,
                    baudrate=baud,
                    protocol=None,
                    fast=FAST,
                    timeout=truncate(float(SERTIMEOUT), 1),
                    check_voltage=False,
                    start_low_power=False,
                )
            except Exception as ex:
                wx.PostEvent(self._notify_window, DebugEvent([1, "Open failed on " + str(candidate_port) + ": " + str(ex)]))
                self.connection = _DisconnectedConnection("Not Connected")
                continue

            if self.connection.status() == "Car Connected":
                wx.PostEvent(self._notify_window, DebugEvent([2, "Connected to: " + str(self.connection.port_name())]))
                break

            self.connection.close()
            self.connection = _DisconnectedConnection("Not Connected")
            time.sleep(0.2)

    def _normalize_adapter_target(self, portnum):
        """Normalize config input into serial port or pyserial URL string."""
        if portnum is None:
            return None

        if not isinstance(portnum, str):
            return portnum

        target = portnum.strip()
        if target.upper() == 'AUTO' or target == '':
            return None

        if target.upper() == 'DEMO':
            return 'DEMO'

        # Already a pyserial URL (socket://, rfc2217://, loop://, etc.)
        if '://' in target:
            return target

        # Wi-Fi adapters are commonly configured as host[:port] without scheme.
        if target.startswith('WIFI:'):
            host_port = target[5:].strip()
            if host_port and ':' not in host_port:
                host_port += ':35000'
            return 'socket://' + host_port

        # Bluetooth target may be an RFCOMM URL or COM port (on Windows SPP).
        if target.startswith('BT:'):
            bt_target = target[3:].strip()
            if '://' in bt_target:
                return bt_target
            if bt_target.upper().startswith('COM'):
                return bt_target
            return 'rfcomm://' + bt_target + ':1'

        return target

    def close(self):
        """ Resets device and closes all associated filehandles"""
        self.connection.close()
        self.ELMver = "Unknown"

    def sensor(self , sensor_index):
        """Returns 3-tuple of given sensors. 3-tuple consists of
         (Sensor Name (string), Sensor Value (string), Sensor Unit (string) ) """
        ###for command in self.connection.supported_commands[1].name
        pass
        #sensor = obd_sensors.SENSORS[sensor_index]
        #r = self.get_sensor_value(sensor)
        #return (sensor.name,r, sensor.unit)

    def clear_dtc(self):
        """Clears all DTCs and freeze frame data"""
        #self.send_command(CLEAR_DTC_COMMAND)
        #r = self.get_result()
        r = self.connection.query(obd.commands["CLEAR_DTC"])
        return r

    def log(self, sensor_index, filename): 
        file = open(filename, "w")
        start_time = time.time() 
        if file:
            data = self.sensor(sensor_index)
            file.write("%s     \t%s(%s)\n" % \
                         ("Time", string.strip(data[0]), data[2])) 
            while 1:
                now = time.time()
                data = self.sensor(sensor_index)
                line = "%.6f,\t%s\n" % (now - start_time, data[1])
                file.write(line)
                file.flush()
          
