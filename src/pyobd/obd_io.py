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

import string
import time

import wx

from pyobd import obd
from pyobd.gui.gui_events import DebugEvent
import logging

from pyobd.obd import OBDStatus

logger = logging.getLogger(__name__)


def truncate(num, n):
    integer = int(num * (10 ** n)) / (10 ** n)
    return float(integer)


GET_DTC_COMMAND = "03"
CLEAR_DTC_COMMAND = "04"
GET_FREEZE_DTC_COMMAND = "07"


class OBDConnection:
    def __init__(self, port_name: str, _notify_window: wx.App, baudrate: int, timeout: int, reconnection_attempts: int,
                 fast: bool):
        self._notify_window = _notify_window
        if baudrate == "AUTO":
            baudrate = None
        if port_name == "AUTO":
            port_name = None
        if fast == "FAST":
            fast = True
        else:
            fast = False

        counter = 0
        while counter < reconnection_attempts:
            counter = counter + 1
            wx.PostEvent(
                self._notify_window,
                DebugEvent([2, "Connection attempt:" + str(counter)]),
            )
            try:
                self.connection.close()
            except:
                pass
            self.connection = obd.OBD(
                port=port_name,
                baudrate=baudrate,
                protocol=None,
                fast=fast,
                timeout=truncate(float(timeout), 1),
                check_voltage=False,
                start_low_power=False,
            )
            if self.connection.status == OBDStatus.CAR_CONNECTED:
                wx.PostEvent(
                    self._notify_window,
                    DebugEvent(
                        [2, "Connected to: " + str(self.connection.port_name())]
                    ),
                )
                break
            else:
                self.connection.close()
            time.sleep(1)

    def close(self):
        """Resets device and closes all associated filehandles"""
        self.connection.close()
        self.ELMver = "Unknown"

    def sensor(self, sensor_index):
        """Returns 3-tuple of given sensors. 3-tuple consists of
        (Sensor Name (string), Sensor Value (string), Sensor Unit (string) )"""
        ###for command in self.connection.supported_commands[1].name
        pass
        # sensor = obd_sensors.SENSORS[sensor_index]
        # r = self.get_sensor_value(sensor)
        # return (sensor.name,r, sensor.unit)

    def clear_dtc(self):
        """Clears all DTCs and freeze frame data"""
        # self.send_command(CLEAR_DTC_COMMAND)
        # r = self.get_result()
        r = self.connection.query(obd.commands["CLEAR_DTC"])
        return r

    def log(self, sensor_index, filename):
        file = open(filename, "w")
        start_time = time.time()
        if file:
            data = self.sensor(sensor_index)
            file.write("%s     \t%s(%s)\n" % ("Time", string.strip(data[0]), data[2]))
            while 1:
                now = time.time()
                data = self.sensor(sensor_index)
                line = "%.6f,\t%s\n" % (now - start_time, data[1])
                file.write(line)
                file.flush()
