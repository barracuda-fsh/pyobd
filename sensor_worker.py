"""Background vehicle polling worker for pyOBD."""

import datetime
from collections import deque
import threading
import time
import traceback

import numpy as np
import wx

import obd
import obd_io
from app_events import *
from debugEvent import DebugEvent
from obd.utils import OBDStatus


class SensorProducer(threading.Thread):
    @staticmethod
    def _target_loop_interval(demo_mode):
        return (1.0 / 30.0) if demo_mode else (1.0 / 12.0)

    @staticmethod
    def _graph_commands_to_poll(commands, isolated_key):
        if isolated_key is None:
            return list(commands)
        return [command for command in commands if command.command == isolated_key]

    def __init__(self, _notify_window, portName, SERTIMEOUT, RECONNATTEMPTS, BAUDRATE, FAST, _nb):
        #from queue import Queue
        self.portName = portName
        self.RECONNATTEMPTS = RECONNATTEMPTS
        self.SERTIMEOUT = SERTIMEOUT
        self.port = None
        self._notify_window = _notify_window
        self.baudrate = BAUDRATE
        self.FAST = FAST
        self._nb = _nb
        self.demo_mode = str(portName).upper() == "DEMO"
        threading.Thread.__init__(self)
        self.state = "started"

    @staticmethod
    def _is_connected_status(status):
        return status in ("Car Connected", OBDStatus.CAR_CONNECTED)

    def initCommunication(self):
        try:
            self.connection.close()
        except:
            pass
        wx.PostEvent(self._notify_window, StatusEvent([0, 1, "Connecting...."]))
        self.connection = obd_io.OBDConnection(self.portName, self._notify_window, self.baudrate, self.SERTIMEOUT,self.RECONNATTEMPTS, self.FAST)
        current_status = self.connection.connection.status()
        if not self._is_connected_status(current_status):  # Cant open serial port
            print(current_status)
            #wx.PostEvent(self._notify_window, StatusEvent([666]))  # signal apl, that communication was disconnected
            #wx.PostEvent(self._notify_window, StatusEvent([0, 1, "Error cant connect..."]))
            #self.state="finished"
            self.stop()
            return None
        elif self._is_connected_status(current_status):
            wx.PostEvent(self._notify_window, DebugEvent([1, "Communication initialized..."]))
            wx.PostEvent(self._notify_window, StatusEvent([0, 1, "Car connected!"]))

            r = self.connection.connection.query(obd.commands.ELM_VERSION)
            self.ELMver = str(r.value)
            r = self.connection.connection.query(obd.commands.ELM_VOLTAGE)
            self.ELMvoltage = str(r.value)
            wx.PostEvent(self._notify_window, StatusEvent([5, 1, str(self.ELMvoltage)]))
            self.protocol = self.connection.connection.protocol_name()

            wx.PostEvent(self._notify_window, StatusEvent([2, 1, str(self.ELMver)]))
            wx.PostEvent(self._notify_window, StatusEvent([1, 1, str(self.protocol)]))
            wx.PostEvent(self._notify_window, StatusEvent([3, 1, str(self.connection.connection.port_name())]))
            try:
                r = self.connection.connection.query(obd.commands.VIN)
                if r.value != None:
                    self.VIN = r.value.decode()
                    wx.PostEvent(self._notify_window, StatusEvent([4, 1, str(self.VIN)]))
            except:
                pass
                #traceback.print_exc()

            return "OK"


    def run(self):

        if self.initCommunication() != "OK":
            self._notify_window.ThreadControl = 666
            self.state = "finished"
            return None

        self.baudrate = self.connection.connection.interface.baudrate()
        self.portName = self.connection.connection.port_name()

        prevstate = -1
        curstate = -1
        first_time_sensors = True
        first_time_freezeframe = True

        first_time_graph = True
        first_time_graphs = True
        first_time_8graphs = True
        self.first_time_graph_plot = True
        self.first_time_graphs_plot = True
        self.first_time_8graphs_plot = True
        self.graph_counter = 0
        self.graph_counter1 = 0
        self.graph_counter8_1 = 0
        self.graph_dirty1 = False
        self.graph_dirty2 = False
        self.graph_dirty3 = False
        self.graph_dirty4 = False

        self.graph_dirty8_1 = False
        self.graph_dirty8_2 = False
        self.graph_dirty8_3 = False
        self.graph_dirty8_4 = False
        self.graph_dirty8_5 = False
        self.graph_dirty8_6 = False
        self.graph_dirty8_7 = False
        self.graph_dirty8_8 = False
        #sensor_list = []
        misfire_cylinder_supported = True
        first_time=True
        #pimp_counter = 0
        #time_prev = datetime.datetime.now()
        #time_now = datetime.datetime.now()

        def init_all_graphs():
            self.graph_x_vals = np.array([])
            self.graph_y_vals = np.array([])
            self.graph_counter = 0

            self.graph_x_vals1 = np.array([])
            self.graph_y_vals1 = np.array([])
            self.graph_x_vals2 = np.array([])
            self.graph_y_vals2 = np.array([])
            self.graph_x_vals3 = np.array([])
            self.graph_y_vals3 = np.array([])
            self.graph_x_vals4 = np.array([])
            self.graph_y_vals4 = np.array([])
            self.graph_counter1 = 0
            self.graph_counter2 = 0
            self.graph_counter3 = 0
            self.graph_counter4 = 0

            self.graph_x_vals8_1 = np.array([])
            self.graph_y_vals8_1 = np.array([])
            self.graph_x_vals8_2 = np.array([])
            self.graph_y_vals8_2 = np.array([])
            self.graph_x_vals8_3 = np.array([])
            self.graph_y_vals8_3 = np.array([])
            self.graph_x_vals8_4 = np.array([])
            self.graph_y_vals8_4 = np.array([])
            self.graph_x_vals8_5 = np.array([])
            self.graph_y_vals8_5 = np.array([])
            self.graph_x_vals8_6 = np.array([])
            self.graph_y_vals8_6 = np.array([])
            self.graph_x_vals8_7 = np.array([])
            self.graph_y_vals8_7 = np.array([])
            self.graph_x_vals8_8 = np.array([])
            self.graph_y_vals8_8 = np.array([])
            self.graph_counter8_1 = 0
            self.graph_counter8_2 = 0
            self.graph_counter8_3 = 0
            self.graph_counter8_4 = 0
            self.graph_counter8_5 = 0
            self.graph_counter8_6 = 0
            self.graph_counter8_7 = 0
            self.graph_counter8_8 = 0


        init_all_graphs()
        def reconnect():
            init_all_graphs()
            if self.initCommunication() != "OK":
                self._notify_window.ThreadControl = 666

        while self._notify_window.ThreadControl != 666:
            if not self._is_connected_status(self.connection.connection.status()):
                reconnect()
                continue
            prevstate = curstate
            curstate = self._nb.GetSelection()  # picking the tab in the GUI




            if not first_time:
                diff = (time_end - time_start).total_seconds()
                target_interval = self._target_loop_interval(self.demo_mode)
                if 0 < diff < target_interval:
                    sleep_time = target_interval - diff
                    time.sleep(sleep_time)
            time_start = datetime.datetime.now()



            if curstate != 5 and self.graph_counter != 0:
                self.graph_series = {}
                self.graph_counter = 0
                self.first_time_graph_plot = True
                wx.PostEvent(self._notify_window, GraphEvent([[], self.graph_counter, self.first_time_graph_plot]))
                self.first_time_graph_plot = False



            if hasattr(self._notify_window, "graphs_panel") and curstate != 6 and self.graph_counter1 != 0:
                self.graph_x_vals1 = np.array([])
                self.graph_y_vals1 = np.array([])
                self.graph_x_vals2 = np.array([])
                self.graph_y_vals2 = np.array([])
                self.graph_x_vals3 = np.array([])
                self.graph_y_vals3 = np.array([])
                self.graph_x_vals4 = np.array([])
                self.graph_y_vals4 = np.array([])
                self.graph_counter1 = 0
                self.graph_counter2 = 0
                self.graph_counter3 = 0
                self.graph_counter4 = 0
                self.first_time_graphs_plot = True
                wx.PostEvent(self._notify_window, GraphsEvent(
                    [(self.graph_x_vals1, self.graph_y_vals1, self.unit1, desc1, self.graph_counter1),
                     (self.graph_x_vals2, self.graph_y_vals2, self.unit2, desc2, self.graph_counter2),
                     (self.graph_x_vals3, self.graph_y_vals3, self.unit3, desc3, self.graph_counter3),
                     (self.graph_x_vals4, self.graph_y_vals4, self.unit4, desc4, self.graph_counter4),
                     (self.first_time_graphs_plot)
                     ]))
                wx.PostEvent(self._notify_window, GraphsValueEvent([0, 0, self.current_command1.command]))
                wx.PostEvent(self._notify_window, GraphsValueEvent([0, 1, self.current_command1.desc]))

                wx.PostEvent(self._notify_window, GraphsValueEvent([1, 0, self.current_command2.command]))
                wx.PostEvent(self._notify_window, GraphsValueEvent([1, 1, self.current_command2.desc]))

                wx.PostEvent(self._notify_window, GraphsValueEvent([2, 0, self.current_command3.command]))
                wx.PostEvent(self._notify_window, GraphsValueEvent([2, 1, self.current_command3.desc]))

                wx.PostEvent(self._notify_window, GraphsValueEvent([3, 0, self.current_command4.command]))
                wx.PostEvent(self._notify_window, GraphsValueEvent([3, 1, self.current_command4.desc]))

            if hasattr(self._notify_window, "graphs8_panel") and curstate != 7 and self.graph_counter8_1 != 0:
                self.graph_x_vals8_1 = np.array([])
                self.graph_y_vals8_1 = np.array([])
                self.graph_x_vals8_2 = np.array([])
                self.graph_y_vals8_2 = np.array([])
                self.graph_x_vals8_3 = np.array([])
                self.graph_y_vals8_3 = np.array([])
                self.graph_x_vals8_4 = np.array([])
                self.graph_y_vals8_4 = np.array([])
                self.graph_x_vals8_5 = np.array([])
                self.graph_y_vals8_5 = np.array([])
                self.graph_x_vals8_6 = np.array([])
                self.graph_y_vals8_6 = np.array([])
                self.graph_x_vals8_7 = np.array([])
                self.graph_y_vals8_7 = np.array([])
                self.graph_x_vals8_8 = np.array([])
                self.graph_y_vals8_8 = np.array([])

                self.graph_counter8_1 = 0
                self.graph_counter8_2 = 0
                self.graph_counter8_3 = 0
                self.graph_counter8_4 = 0
                self.graph_counter8_5 = 0
                self.graph_counter8_6 = 0
                self.graph_counter8_7 = 0
                self.graph_counter8_8 = 0
                self.first_time_graphs8_plot = True
                wx.PostEvent(self._notify_window, Graphs8Event(
                    [(self.graph_x_vals8_1, self.graph_y_vals8_1, self.unit8_1, desc8_1, self.graph_counter8_1),
                     (self.graph_x_vals8_2, self.graph_y_vals8_2, self.unit8_2, desc8_2, self.graph_counter8_2),
                     (self.graph_x_vals8_3, self.graph_y_vals8_3, self.unit8_3, desc8_3, self.graph_counter8_3),
                     (self.graph_x_vals8_4, self.graph_y_vals8_4, self.unit8_4, desc8_4, self.graph_counter8_4),
                     (self.graph_x_vals8_5, self.graph_y_vals8_5, self.unit8_5, desc8_5, self.graph_counter8_5),
                     (self.graph_x_vals8_6, self.graph_y_vals8_6, self.unit8_6, desc8_6, self.graph_counter8_6),
                     (self.graph_x_vals8_7, self.graph_y_vals8_7, self.unit8_7, desc8_7, self.graph_counter8_7),
                     (self.graph_x_vals8_8, self.graph_y_vals8_8, self.unit8_8, desc8_8, self.graph_counter8_8),
                     (self.first_time_graphs8_plot)
                     ]))
                wx.PostEvent(self._notify_window, Graphs8ValueEvent([0, 0, self.current_command8_1.command]))
                wx.PostEvent(self._notify_window, Graphs8ValueEvent([0, 1, self.current_command8_1.desc]))

                wx.PostEvent(self._notify_window, Graphs8ValueEvent([1, 0, self.current_command8_2.command]))
                wx.PostEvent(self._notify_window, Graphs8ValueEvent([1, 1, self.current_command8_2.desc]))

                wx.PostEvent(self._notify_window, Graphs8ValueEvent([2, 0, self.current_command8_3.command]))
                wx.PostEvent(self._notify_window, Graphs8ValueEvent([2, 1, self.current_command8_3.desc]))

                wx.PostEvent(self._notify_window, Graphs8ValueEvent([3, 0, self.current_command8_4.command]))
                wx.PostEvent(self._notify_window, Graphs8ValueEvent([3, 1, self.current_command8_4.desc]))

                wx.PostEvent(self._notify_window, Graphs8ValueEvent([4, 0, self.current_command8_5.command]))
                wx.PostEvent(self._notify_window, Graphs8ValueEvent([4, 1, self.current_command8_5.desc]))

                wx.PostEvent(self._notify_window, Graphs8ValueEvent([5, 0, self.current_command8_6.command]))
                wx.PostEvent(self._notify_window, Graphs8ValueEvent([5, 1, self.current_command8_6.desc]))

                wx.PostEvent(self._notify_window, Graphs8ValueEvent([6, 0, self.current_command8_7.command]))
                wx.PostEvent(self._notify_window, Graphs8ValueEvent([6, 1, self.current_command8_7.desc]))

                wx.PostEvent(self._notify_window, Graphs8ValueEvent([7, 0, self.current_command8_8.command]))
                wx.PostEvent(self._notify_window, Graphs8ValueEvent([7, 1, self.current_command8_8.desc]))

            if curstate == 0:  # show status tab
                r = self.connection.connection.query(obd.commands.RPM)
                if r.value == None:
                    reconnect()
                    continue

                r = self.connection.connection.query(obd.commands.ELM_VOLTAGE)
                self.ELMvoltage = str(r.value)
                wx.PostEvent(self._notify_window, StatusEvent([5, 1, str(self.ELMvoltage)]))



            elif curstate == 1:  # show tests tab
                try:
                    r = self.connection.connection.query(obd.commands.RPM)
                    if r.value == None:
                        reconnect()
                        continue
                    r = self.connection.connection.query(obd.commands[1][1])
                    if r.value == None:
                        # NOT SUPPORTED, so do nothing
                        continue

                    if r.value.MISFIRE_MONITORING.available:
                        wx.PostEvent(self._notify_window, TestEvent([0, 1, "Available"]))
                        if r.value.MISFIRE_MONITORING.complete:
                            wx.PostEvent(self._notify_window, TestEvent([0, 2, "Complete"]))
                        else:
                            wx.PostEvent(self._notify_window, TestEvent([0, 2, "Incomplete"]))
                    if r.value.FUEL_SYSTEM_MONITORING.available:
                        wx.PostEvent(self._notify_window, TestEvent([1, 1, "Available"]))
                        if r.value.FUEL_SYSTEM_MONITORING.complete:
                            wx.PostEvent(self._notify_window, TestEvent([1, 2, "Complete"]))
                        else:
                            wx.PostEvent(self._notify_window, TestEvent([1, 2, "Incomplete"]))
                    if r.value.COMPONENT_MONITORING.available:
                        wx.PostEvent(self._notify_window, TestEvent([2, 1, "Available"]))
                        if r.value.COMPONENT_MONITORING.complete:
                            wx.PostEvent(self._notify_window, TestEvent([2, 2, "Complete"]))
                        else:
                            wx.PostEvent(self._notify_window, TestEvent([2, 2, "Incomplete"]))

                    if r.value.CATALYST_MONITORING.available:
                        wx.PostEvent(self._notify_window, TestEvent([3, 1, "Available"]))
                        if r.value.CATALYST_MONITORING.complete:
                            wx.PostEvent(self._notify_window, TestEvent([3, 2, "Complete"]))
                        else:
                            wx.PostEvent(self._notify_window, TestEvent([3, 2, "Incomplete"]))

                    if r.value.HEATED_CATALYST_MONITORING.available:
                        wx.PostEvent(self._notify_window, TestEvent([4, 1, "Available"]))
                        if r.value.HEATED_CATALYST_MONITORING.complete:
                            wx.PostEvent(self._notify_window, TestEvent([4, 2, "Complete"]))
                        else:
                            wx.PostEvent(self._notify_window, TestEvent([4, 2, "Incomplete"]))

                    if r.value.EVAPORATIVE_SYSTEM_MONITORING.available:
                        wx.PostEvent(self._notify_window, TestEvent([5, 1, "Available"]))
                        if r.value.EVAPORATIVE_SYSTEM_MONITORING.complete:
                            wx.PostEvent(self._notify_window, TestEvent([5, 2, "Complete"]))
                        else:
                            wx.PostEvent(self._notify_window, TestEvent([5, 2, "Incomplete"]))

                    if r.value.SECONDARY_AIR_SYSTEM_MONITORING.available:
                        wx.PostEvent(self._notify_window, TestEvent([6, 1, "Available"]))
                        if r.value.SECONDARY_AIR_SYSTEM_MONITORING.complete:
                            wx.PostEvent(self._notify_window, TestEvent([6, 2, "Complete"]))
                        else:
                            wx.PostEvent(self._notify_window, TestEvent([6, 2, "Incomplete"]))

                    if r.value.OXYGEN_SENSOR_MONITORING.available:
                        wx.PostEvent(self._notify_window, TestEvent([7, 1, "Available"]))
                        if r.value.OXYGEN_SENSOR_MONITORING.complete:
                            wx.PostEvent(self._notify_window, TestEvent([7, 2, "Complete"]))
                        else:
                            wx.PostEvent(self._notify_window, TestEvent([7, 2, "Incomplete"]))

                    if r.value.OXYGEN_SENSOR_HEATER_MONITORING.available:
                        wx.PostEvent(self._notify_window, TestEvent([8, 1, "Available"]))
                        if r.value.OXYGEN_SENSOR_HEATER_MONITORING.complete:
                            wx.PostEvent(self._notify_window, TestEvent([8, 2, "Complete"]))
                        else:
                            wx.PostEvent(self._notify_window, TestEvent([8, 2, "Incomplete"]))

                    if r.value.EGR_VVT_SYSTEM_MONITORING.available:
                        wx.PostEvent(self._notify_window, TestEvent([9, 1, "Available"]))
                        if r.value.EGR_VVT_SYSTEM_MONITORING.complete:
                            wx.PostEvent(self._notify_window, TestEvent([9, 2, "Complete"]))
                        else:
                            wx.PostEvent(self._notify_window, TestEvent([9, 2, "Incomplete"]))

                    if r.value.NMHC_CATALYST_MONITORING.available:
                        wx.PostEvent(self._notify_window, TestEvent([10, 1, "Available"]))
                        if r.value.NMHC_CATALYST_MONITORING.complete:
                            wx.PostEvent(self._notify_window, TestEvent([10, 2, "Complete"]))
                        else:
                            wx.PostEvent(self._notify_window, TestEvent([10, 2, "Incomplete"]))

                    if r.value.NOX_SCR_AFTERTREATMENT_MONITORING.available:
                        wx.PostEvent(self._notify_window, TestEvent([11, 1, "Available"]))
                        if r.value.NOX_SCR_AFTERTREATMENT_MONITORING.complete:
                            wx.PostEvent(self._notify_window, TestEvent([11, 2, "Complete"]))
                        else:
                            wx.PostEvent(self._notify_window, TestEvent([11, 2, "Incomplete"]))

                    if r.value.BOOST_PRESSURE_MONITORING.available:
                        wx.PostEvent(self._notify_window, TestEvent([12, 1, "Available"]))
                        if r.value.BOOST_PRESSURE_MONITORING.complete:
                            wx.PostEvent(self._notify_window, TestEvent([12, 2, "Complete"]))
                        else:
                            wx.PostEvent(self._notify_window, TestEvent([12, 2, "Incomplete"]))

                    if r.value.EXHAUST_GAS_SENSOR_MONITORING.available:
                        wx.PostEvent(self._notify_window, TestEvent([13, 1, "Available"]))
                        if r.value.EXHAUST_GAS_SENSOR_MONITORING.complete:
                            wx.PostEvent(self._notify_window, TestEvent([13, 2, "Complete"]))
                        else:
                            wx.PostEvent(self._notify_window, TestEvent([13, 2, "Incomplete"]))

                    if r.value.PM_FILTER_MONITORING.available:
                        wx.PostEvent(self._notify_window, TestEvent([14, 1, "Available"]))
                        if r.value.PM_FILTER_MONITORING.complete:
                            wx.PostEvent(self._notify_window, TestEvent([14, 2, "Complete"]))
                        else:
                            wx.PostEvent(self._notify_window, TestEvent([14, 2, "Incomplete"]))

                    response = self.connection.connection.query(obd.commands.MONITOR_MISFIRE_CYLINDER_1)
                    if response.value != None:
                        result = response.value.MISFIRE_COUNT
                        wx.PostEvent(self._notify_window, TestEvent([15, 2, str(result)]))
                    response = self.connection.connection.query(obd.commands.MONITOR_MISFIRE_CYLINDER_2)
                    if response.value != None:
                        result = response.value.MISFIRE_COUNT
                        wx.PostEvent(self._notify_window, TestEvent([16, 2, str(result)]))
                    response = self.connection.connection.query(obd.commands.MONITOR_MISFIRE_CYLINDER_3)
                    if response.value != None:
                        result = response.value.MISFIRE_COUNT
                        wx.PostEvent(self._notify_window, TestEvent([17, 2, str(result)]))
                    response = self.connection.connection.query(obd.commands.MONITOR_MISFIRE_CYLINDER_4)
                    if response.value != None:
                        result = response.value.MISFIRE_COUNT
                        wx.PostEvent(self._notify_window, TestEvent([18, 2, str(result)]))
                    response = self.connection.connection.query(obd.commands.MONITOR_MISFIRE_CYLINDER_5)
                    if response.value != None:
                        result = response.value.MISFIRE_COUNT
                        wx.PostEvent(self._notify_window, TestEvent([19, 2, str(result)]))
                    response = self.connection.connection.query(obd.commands.MONITOR_MISFIRE_CYLINDER_6)
                    if response.value != None:
                        result = response.value.MISFIRE_COUNT
                        wx.PostEvent(self._notify_window, TestEvent([20, 2, str(result)]))
                    response = self.connection.connection.query(obd.commands.MONITOR_MISFIRE_CYLINDER_7)
                    if response.value != None:
                        result = response.value.MISFIRE_COUNT
                        wx.PostEvent(self._notify_window, TestEvent([21, 2, str(result)]))
                    response = self.connection.connection.query(obd.commands.MONITOR_MISFIRE_CYLINDER_8)
                    if response.value != None:
                        result = response.value.MISFIRE_COUNT
                        wx.PostEvent(self._notify_window, TestEvent([22, 2, str(result)]))
                    response = self.connection.connection.query(obd.commands.MONITOR_MISFIRE_CYLINDER_9)
                    if response.value != None:
                        result = response.value.MISFIRE_COUNT
                        wx.PostEvent(self._notify_window, TestEvent([23, 2, str(result)]))
                    response = self.connection.connection.query(obd.commands.MONITOR_MISFIRE_CYLINDER_10)
                    if response.value != None:
                        result = response.value.MISFIRE_COUNT
                        wx.PostEvent(self._notify_window, TestEvent([24, 2, str(result)]))
                    response = self.connection.connection.query(obd.commands.MONITOR_MISFIRE_CYLINDER_11)
                    if response.value != None:
                        result = response.value.MISFIRE_COUNT
                        wx.PostEvent(self._notify_window, TestEvent([25, 2, str(result)]))
                    response = self.connection.connection.query(obd.commands.MONITOR_MISFIRE_CYLINDER_12)
                    if response.value != None:
                        result = response.value.MISFIRE_COUNT
                        wx.PostEvent(self._notify_window, TestEvent([26, 2, str(result)]))

                except:
                    traceback.print_exc()


                """
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
                "PM_FILTER_MONITORING"
                """

            elif curstate == 2:  # show sensor tab
                r = self.connection.connection.query(obd.commands.RPM)
                if r.value == None:
                    reconnect()
                    continue

                if first_time_sensors:
                    sensor_list = []
                    counter = 0
                    first_time_sensors = False
                    for command in obd.commands[1]:
                        if command:
                            if command.command not in (b"0100", b"0120", b"0140"): #, b"0103", b"0141" #b"0101", b"0103", b"0102", b"011C", b"0151", b"0113"
                                r = self.connection.connection.query(command)
                                if r.value == None and command.command != b"0103":
                                    continue
                                else:
                                    sensor_list.append([command, command.desc])

                                    #app.sensors.InsertItem(counter, "")
                                    wx.PostEvent(self._notify_window, InsertSensorRowEvent(counter))
                                    wx.PostEvent(self._notify_window, ResultEvent([counter, 0, command.command]))
                                    wx.PostEvent(self._notify_window, ResultEvent([counter, 1, str(command.desc)]))
                                    if command.command == b"0101" or command.command == b"0141":
                                        wx.PostEvent(self._notify_window, ResultEvent([counter, 2, "MIL ON: "+str(r.value.MIL)+", DTC Count: "+str(r.value.DTC_count)+", Ignition type: "+str(r.value.ignition_type)+", Misfire monitoring complete: "+str(r.value.MISFIRE_MONITORING.complete)]))
                                    elif command.command == b"0113":
                                        wx.PostEvent(self._notify_window, ResultEvent([counter, 2, "Bank1S1: "+str(r.value[1][0])+", Bank1S2: "+str(r.value[1][1])+", Bank1S3: "+str(r.value[1][2])+", Bank1S4: "+str(r.value[1][3])+" Bank2S1: "+str(r.value[2][0])+", Bank2S2: "+str(r.value[2][1])+", Bank2S3: "+str(r.value[2][2])+", Bank2S4: "+str(r.value[2][3])]))
                                    elif command.command == b"0103" and r.value != None:
                                        wx.PostEvent(self._notify_window, ResultEvent([counter, 2, str(r.value[0])]))
                                    else:
                                        wx.PostEvent(self._notify_window, ResultEvent([counter, 2, self._notify_window.format_measurement_value(r.value)]))
                                    counter = counter + 1
                    #r = self.connection.connection.query(obd.commands.ELM_VOLTAGE)
                    #sensor_list.append([obd.commands.ELM_VOLTAGE, obd.commands.ELM_VOLTAGE.desc, str(r.value)])
                    #wx.PostEvent(self._notify_window, InsertSensorRowEvent(counter))
                    #wx.PostEvent(self._notify_window, ResultEvent([counter, 0, str(obd.commands.ELM_VOLTAGE.command)]))
                    #wx.PostEvent(self._notify_window, ResultEvent([counter, 1, str(obd.commands.ELM_VOLTAGE.desc)]))
                    #wx.PostEvent(self._notify_window, ResultEvent([counter, 2, str(r.value)]))
                else:

                    #for i in range(0, app.sensors.GetItemCount()):
                    #    app.sensors.DeleteItem(0)
                    counter = 0
                    for sens in sensor_list:
                        r = self.connection.connection.query(sens[0])
                        if r.value == None and sens[0].command != b"0103":
                            #reconnect()
                            continue
                        wx.PostEvent(self._notify_window, ResultEvent([counter, 0, sens[0].command]))
                        wx.PostEvent(self._notify_window, ResultEvent([counter, 1, str(sens[1])]))

                        if sens[0].command == b"0101" or sens[0].command == b"0141":
                            wx.PostEvent(self._notify_window, ResultEvent([counter, 2, "MIL ON: " + str(
                                r.value.MIL) + ", DTC Count: " + str(r.value.DTC_count) + ", Ignition type: " + str(
                                r.value.ignition_type) + ", Misfire monitoring complete: " + str(
                                r.value.MISFIRE_MONITORING.complete)]))
                        elif sens[0].command == b"0113":
                            wx.PostEvent(self._notify_window, ResultEvent([counter, 2, "Bank1S1: "+str(r.value[1][0])+", Bank1S2: "+str(r.value[1][1])+", Bank1S3: "+str(r.value[1][2])+", Bank1S4: "+str(r.value[1][3])+" Bank2S1: "+str(r.value[2][0])+", Bank2S2: "+str(r.value[2][1])+", Bank2S3: "+str(r.value[2][2])+", Bank2S4: "+str(r.value[2][3])]))
                        elif sens[0].command == b"0103" and r.value != None:
                            wx.PostEvent(self._notify_window, ResultEvent([counter, 2, str(r.value[0])]))
                        else:
                            wx.PostEvent(self._notify_window, ResultEvent([counter, 2, self._notify_window.format_measurement_value(r.value)]))

                        counter = counter + 1

            elif curstate == 3:  # show DTC tab

                r = self.connection.connection.query(obd.commands.RPM)
                if r.value == None:
                    reconnect()
                    continue

                if self._notify_window.ThreadControl == 1:  # clear DTC
                    r = self.connection.connection.query(obd.commands["CLEAR_DTC"])

                    if self._notify_window.ThreadControl == 666:  # before reset ThreadControl we must check if main thread did not want us to finish
                        break

                    self._notify_window.ThreadControl = 0
                    prevstate = -1  # to reread DTC
                if self._notify_window.ThreadControl == 2:  # reread DTC

                    prevstate = -1

                    if self._notify_window.ThreadControl == 666:
                        break

                    self._notify_window.ThreadControl = 0

                    pass
                if prevstate != 3:

                    wx.PostEvent(self._notify_window, DTCEvent(0))  # clear list
                    r = self.connection.connection.query(obd.commands.GET_DTC)
                    DTCCODES = []
                    print ("DTCCODES:",r.value)
                    if r.value != None:
                        for dtccode in r.value:
                            DTCCODES.append((dtccode[0], "Active", dtccode[1]))
                    r = self.connection.connection.query(obd.commands.FREEZE_DTC)
                    print ("FREEZECODES:",r.value)
                    if r.value != None:
                        dtccode = r.value
                        if "P0000" not in dtccode:
                            DTCCODES.append((dtccode[0], "Passive", dtccode[1]))

                    print ("DTCcodes and FREEZEcodes:", DTCCODES)
                    if len(DTCCODES) > 0:
                        for dtccode in DTCCODES:
                            wx.PostEvent(self._notify_window, DTCEvent(dtccode))
                    elif len(DTCCODES) == 0:
                        wx.PostEvent(self._notify_window, DTCEvent(["", "", "No DTC codes (codes cleared)"]))

            elif curstate == 4:  # show freezeframe tab
                r = self.connection.connection.query(obd.commands.RPM)
                if r.value == None:
                    reconnect()
                    continue
                if first_time_freezeframe:
                    freezeframe_list = []
                    counter = 0
                    first_time_freezeframe = False
                    for command in obd.commands[2]:
                        if command:
                            if command.command not in (b"0200" , b"0201", b"0220", b"0240", b"0203", b"0202", b"021C", b"0213", b"0241", b"0251"):
                                r = self.connection.connection.query(command)
                                if r.value == None:
                                    continue
                                else:
                                    freezeframe_list.append([command.command, command.desc, self._notify_window.format_measurement_value(r.value)])
                                    wx.PostEvent(self._notify_window, InsertFreezeframeRowEvent(counter))
                                    wx.PostEvent(self._notify_window, FreezeframeResultEvent([counter, 0, command.command]))
                                    wx.PostEvent(self._notify_window, FreezeframeResultEvent([counter, 1, str(command.desc)]))
                                    wx.PostEvent(self._notify_window, FreezeframeResultEvent([counter, 2, self._notify_window.format_measurement_value(r.value)]))
                                    counter = counter + 1
                else:
                    counter = 0
                    for sens in freezeframe_list:
                        for command in obd.commands[2]:
                            if command.command == sens[0]:
                                r = self.connection.connection.query(command)
                                if r.value == None:
                                    #reconnect()
                                    continue
                                freezeframe_list[counter] = [command.command, command.desc, self._notify_window.format_measurement_value(r.value)]
                                counter = counter + 1
                    counter = 0
                    for sens in freezeframe_list:
                        wx.PostEvent(self._notify_window, FreezeframeResultEvent([counter, 0, sens[0]]))
                        wx.PostEvent(self._notify_window, FreezeframeResultEvent([counter, 1, str(sens[1])]))
                        wx.PostEvent(self._notify_window, FreezeframeResultEvent([counter, 2, str(sens[2])]))
                        counter = counter + 1
                        #if sens[2] == "None" and sens[0]!='0203':
                        #    raise AttributeError

            elif curstate == 5:  # show Graph tab
                if first_time_graph:
                    self.graph_counter = 0
                    self.graph_series = {}
                    self.graph_emit_counter = 0
                    self.graph_stream_active_last = False
                    first_time_graph = False

                if not self._notify_window.graph_streaming_enabled:
                    if self.graph_stream_active_last:
                        self.graph_counter = 0
                        self.graph_emit_counter = 0
                        self.graph_series = {}
                        self.first_time_graph_plot = True
                        wx.PostEvent(self._notify_window, GraphEvent([[], 0, self.first_time_graph_plot]))
                    self.graph_stream_active_last = False
                    continue

                self.graph_stream_active_last = True

                selected_commands = list(self._notify_window.selected_graph_commands)
                isolated_key = getattr(self._notify_window, "isolated_graph_command_key", None)
                selected_commands = self._graph_commands_to_poll(selected_commands, isolated_key)
                selected_keys = {command.command for command in selected_commands}

                for stale_key in list(self.graph_series.keys()):
                    if stale_key not in selected_keys:
                        del self.graph_series[stale_key]

                plot_series = []
                for row, command in enumerate(selected_commands):
                    command_key = command.command
                    if command_key not in self.graph_series:
                        self.graph_series[command_key] = {
                            "x": deque(maxlen=450),
                            "y": deque(maxlen=450),
                            "unit": "value",
                            "desc": command.desc,
                        }

                    r = self.connection.connection.query(command)
                    if r.value is None:
                        if self.graph_emit_counter < 2 or (self.graph_emit_counter % 3) == 0:
                            wx.PostEvent(self._notify_window, GraphValueEvent([command_key, 2, "No data"]))
                        continue

                    series = self.graph_series[command_key]
                    series["x"].append(self.graph_counter)
                    converted_magnitude, converted_unit, value_text = self._notify_window.get_measurement_components(r.value)
                    try:
                        series["y"].append(float(converted_magnitude))
                    except (AttributeError, TypeError, ValueError):
                        series["y"].append(0.0)

                    unit = converted_unit if converted_unit else "value"

                    series["unit"] = unit
                    series["desc"] = command.desc

                    if self.graph_emit_counter < 2 or (self.graph_emit_counter % 3) == 0:
                        wx.PostEvent(self._notify_window, GraphValueEvent([command_key, 2, value_text]))

                    plot_series.append((series["x"], series["y"], series["unit"], series["desc"], command_key))

                if self.graph_emit_counter < 2 or (self.graph_emit_counter % 2) == 0:
                    plot_snapshot = [
                        (tuple(series[0]), tuple(series[1]), series[2], series[3], series[4])
                        for series in plot_series
                    ]
                    wx.PostEvent(self._notify_window, GraphEvent([plot_snapshot, self.graph_counter, self.first_time_graph_plot]))
                    self.first_time_graph_plot = False
                self.graph_emit_counter = self.graph_emit_counter + 1
                self.graph_counter = self.graph_counter + 1

            elif hasattr(self._notify_window, "graphs_panel") and curstate == 6:  # show 4Graphs tab
                if first_time_graphs:
                    print("First time graph")
                    #wx.PostEvent(self._notify_window, DestroyComboBoxEvent([]))
                    self.graph_x_vals1 = np.array([])
                    self.graph_y_vals1 = np.array([])
                    self.graph_x_vals2 = np.array([])
                    self.graph_y_vals2 = np.array([])
                    self.graph_x_vals3 = np.array([])
                    self.graph_y_vals3 = np.array([])
                    self.graph_x_vals4 = np.array([])
                    self.graph_y_vals4 = np.array([])
                    self.graph_counter1 = 0
                    self.graph_counter2 = 0
                    self.graph_counter3 = 0
                    self.graph_counter4 = 0
                    self.current_command1 = None
                    self.current_command2 = None
                    self.current_command3 = None
                    self.current_command4 = None

                    graph_commands = []
                    #wx.PostEvent(self._notify_window, GraphEvent((self.current_command, [], [])))
                    prev_command1 = None
                    prev_command2 = None
                    prev_command3 = None
                    prev_command4 = None
                    first_time_graphs = False
                    for command in obd.commands[1]:
                        if command:
                            if command.command not in (b"0100" , b"0101", b"0120", b"0140", b"0103", b"0102", b"011C", b"0113", b"0141", b"0151"):
                                r = self.connection.connection.query(command)
                                if r.value == None:
                                    continue
                                else:
                                    graph_commands.append(command)
                    graph_commands.append(obd.commands.ELM_VOLTAGE)
                    sensor_descriptions = []
                    #sensor_descriptions.append("None")
                    for command in graph_commands:
                        sensor_descriptions.append(command.desc)
                    self._notify_window.build_combobox_graphs_event_finished = False
                    wx.PostEvent(self._notify_window, BuildComboBoxGraphsEvent(sensor_descriptions))
                    while not self._notify_window.build_combobox_graphs_event_finished:
                        time.sleep(0.01)
                    self._notify_window.combobox_graphs_set_sel_finished=False
                    wx.PostEvent(self._notify_window, SetSelectionComboBoxGraphsEvent([]))
                    while not self._notify_window.combobox_graphs_set_sel_finished:
                        time.sleep(0.01)
                else:

                    self._notify_window.combobox_graphs_get_sel_finished = False
                    wx.PostEvent(self._notify_window, GetSelectionComboBoxGraphsEvent([]))
                    while not self._notify_window.combobox_graphs_get_sel_finished:
                        time.sleep(0.01)
                    curr_selection1 = self._notify_window.combobox1_selection
                    curr_selection2 = self._notify_window.combobox2_selection
                    curr_selection3 = self._notify_window.combobox3_selection
                    curr_selection4 = self._notify_window.combobox4_selection
                    if sensor_descriptions[curr_selection1] == "None":
                        curr_selection1 = -1
                    if curr_selection1 != -1:
                        prev_command1 = self.current_command1
                        self.current_command1 = graph_commands[curr_selection1]
                    else:
                        self.current_command1 = None

                    if sensor_descriptions[curr_selection2] == "None":
                        curr_selection2 = -1
                    if curr_selection2 != -1:
                        prev_command2 = self.current_command2
                        self.current_command2 = graph_commands[curr_selection2]
                    else:
                        self.current_command2 = None

                    if sensor_descriptions[curr_selection3] == "None":
                        curr_selection3 = -1
                    if curr_selection3 != -1:
                        prev_command3 = self.current_command3
                        self.current_command3 = graph_commands[curr_selection3]
                    else:
                        self.current_command3 = None

                    if sensor_descriptions[curr_selection4] == "None":
                        curr_selection4 = -1
                    if curr_selection4 != -1:
                        prev_command4 = self.current_command4
                        self.current_command4 = graph_commands[curr_selection4]
                    else:
                        self.current_command4 = None

                    if self.current_command1 != None:
                        if (prev_command1 == None) or (prev_command1 != self.current_command1):
                            self.graph_x_vals1 = np.array([])
                            self.graph_y_vals1 = np.array([])
                            #self.graph_x_vals1 = []
                            #self.graph_y_vals1 = []
                            self.graph_counter1 = 0
                            wx.PostEvent(self._notify_window, GraphsValueEvent([0, 0, self.current_command1.command]))
                            wx.PostEvent(self._notify_window, GraphsValueEvent([0, 1, self.current_command1.desc]))
                        else:
                            r = self.connection.connection.query(self.current_command1)
                            if r.value == None:
                                reconnect()
                                continue
                            #if r.value == None:
                            #    print("r.value is None!")
                            #    raise AttributeError
                            self.graph_x_vals1 = np.append(self.graph_x_vals1, self.graph_counter1)
                            try:
                                self.graph_y_vals1 = np.append(self.graph_y_vals1, float(r.value.magnitude))
                            except AttributeError:
                                self.graph_y_vals1 = np.append(self.graph_y_vals1, float(0))
                            #self.graph_x_vals1.append(self.graph_counter1)
                            #self.graph_y_vals1.append(float(r.value.magnitude))
                            if len(self.graph_x_vals1) > 200:
                                self.graph_x_vals1 = np.delete(self.graph_x_vals1, (0))
                                self.graph_y_vals1 = np.delete(self.graph_y_vals1, (0))
                                #self.graph_x_vals1.pop(0)
                                #self.graph_y_vals1.pop(0)

                            self.graph_counter1 = self.graph_counter1 + 1
                            prev_command1 = self.current_command1
                            self.graph_dirty1 = True
                            #wx.PostEvent(self._notify_window, GraphEvent(self.current_command1))
                            if r.value == None:
                                wx.PostEvent(self._notify_window, GraphsValueEvent([0, 2, str(0)]))
                                self.unit1 = "unit"
                            else:
                                wx.PostEvent(self._notify_window, GraphsValueEvent([0, 2, str(r.value)]))
                                try:
                                    self.unit1 = str(r.value).split(' ')[1]
                                except IndexError:
                                    self.unit1 = "unit"
                    else:
                        self.graph_x_vals1 = np.array([])
                        self.graph_y_vals1 = np.array([])
                        self.graph_counter1 = 0

                    if self.current_command2 != None:
                        if (prev_command2 == None) or (prev_command2 != self.current_command2):
                            self.graph_x_vals2 = np.array([])
                            self.graph_y_vals2 = np.array([])
                            #self.graph_x_vals2 = []
                            #self.graph_y_vals2 = []
                            self.graph_counter2 = 0
                            wx.PostEvent(self._notify_window, GraphsValueEvent([1, 0, self.current_command2.command]))
                            wx.PostEvent(self._notify_window, GraphsValueEvent([1, 1, self.current_command2.desc]))
                        else:
                            r = self.connection.connection.query(self.current_command2)
                            if r.value == None:
                                reconnect()
                                continue
                            #if r.value == None:
                            #    print("r.value is None!")
                            #    raise AttributeError
                            self.graph_x_vals2 = np.append(self.graph_x_vals2, self.graph_counter2)
                            try:
                                self.graph_y_vals2 = np.append(self.graph_y_vals2, float(r.value.magnitude))
                            except AttributeError:
                                self.graph_y_vals2 = np.append(self.graph_y_vals2, float(0))
                            #self.graph_x_vals2.append(self.graph_counter2)
                            #self.graph_y_vals2.append(float(r.value.magnitude))
                            if len(self.graph_x_vals2) > 200:
                                self.graph_x_vals2 = np.delete(self.graph_x_vals2, (0))
                                self.graph_y_vals2 = np.delete(self.graph_y_vals2, (0))
                                #self.graph_x_vals2.pop(0)
                                #self.graph_y_vals2.pop(0)

                            self.graph_counter2 = self.graph_counter2 + 1
                            prev_command2 = self.current_command2
                            self.graph_dirty2 = True
                            #wx.PostEvent(self._notify_window, GraphEvent(self.current_command2))
                            if r.value == None:
                                wx.PostEvent(self._notify_window, GraphsValueEvent([1, 2, str(0)]))
                                self.unit2 = "unit"
                            else:
                                wx.PostEvent(self._notify_window, GraphsValueEvent([1, 2, str(r.value)]))
                                try:
                                    self.unit2 = str(r.value).split(' ')[1]
                                except IndexError:
                                    self.unit2 = "unit"
                    else:
                        self.graph_x_vals2 = np.array([])
                        self.graph_y_vals2 = np.array([])
                        self.graph_counter2 = 0

                    if self.current_command3 != None:
                        if (prev_command3 == None) or (prev_command3 != self.current_command3):
                            self.graph_x_vals3 = np.array([])
                            self.graph_y_vals3 = np.array([])
                            #self.graph_x_vals3 = []
                            #self.graph_y_vals3 = []
                            self.graph_counter3 = 0
                            wx.PostEvent(self._notify_window, GraphsValueEvent([2, 0, self.current_command3.command]))
                            wx.PostEvent(self._notify_window, GraphsValueEvent([2, 1, self.current_command3.desc]))
                        else:
                            r = self.connection.connection.query(self.current_command3)
                            if r.value == None:
                                reconnect()
                                continue
                            #if r.value == None:
                            #    print("r.value is None!")
                            #    raise AttributeError
                            self.graph_x_vals3 = np.append(self.graph_x_vals3, self.graph_counter3)
                            try:
                                self.graph_y_vals3 = np.append(self.graph_y_vals3, float(r.value.magnitude))
                            except AttributeError:
                                self.graph_y_vals3 = np.append(self.graph_y_vals3, float(0))
                            #self.graph_x_vals3.append(self.graph_counter3)
                            #self.graph_y_vals3.append(float(r.value.magnitude))
                            if len(self.graph_x_vals3) > 200:
                                self.graph_x_vals3 = np.delete(self.graph_x_vals3, (0))
                                self.graph_y_vals3 = np.delete(self.graph_y_vals3, (0))
                                #self.graph_x_vals3.pop(0)
                                #self.graph_y_vals3.pop(0)

                            self.graph_counter3 = self.graph_counter3 + 1
                            prev_command3 = self.current_command3
                            self.graph_dirty3 = True
                            #wx.PostEvent(self._notify_window, GraphEvent(self.current_command3))
                            if r.value == None:
                                wx.PostEvent(self._notify_window, GraphsValueEvent([2, 2, str(0)]))
                                self.unit3 = "unit"
                            else:
                                wx.PostEvent(self._notify_window, GraphsValueEvent([2, 2, str(r.value)]))
                                try:
                                    self.unit3 = str(r.value).split(' ')[1]
                                except IndexError:
                                    self.unit3 = "unit"
                    else:
                        self.graph_x_vals3 = np.array([])
                        self.graph_y_vals3 = np.array([])
                        self.graph_counter3 = 0

                    if self.current_command4 != None:
                        if (prev_command4 == None) or (prev_command4 != self.current_command4):
                            self.graph_x_vals4 = np.array([])
                            self.graph_y_vals4 = np.array([])
                            #self.graph_x_vals4 = []
                            #self.graph_y_vals4 = []
                            self.graph_counter4 = 0
                            wx.PostEvent(self._notify_window, GraphsValueEvent([3, 0, self.current_command4.command]))
                            wx.PostEvent(self._notify_window, GraphsValueEvent([3, 1, self.current_command4.desc]))
                        else:
                            r = self.connection.connection.query(self.current_command4)
                            if r.value == None:
                                reconnect()
                                continue
                            #if r.value == None:
                            #    print("r.value is None!")
                            #    raise AttributeError
                            self.graph_x_vals4 = np.append(self.graph_x_vals4, self.graph_counter4)

                            try:
                                self.graph_y_vals4 = np.append(self.graph_y_vals4, float(r.value.magnitude))
                            except AttributeError:
                                self.graph_y_vals4 = np.append(self.graph_y_vals4, float(0))

                            #self.graph_x_vals4.append(self.graph_counter4)
                            #self.graph_y_vals4.append(float(r.value.magnitude))
                            if len(self.graph_x_vals4) > 200:
                                self.graph_x_vals4 = np.delete(self.graph_x_vals4, (0))
                                self.graph_y_vals4 = np.delete(self.graph_y_vals4, (0))
                                #self.graph_x_vals4.pop(0)
                                #self.graph_y_vals4.pop(0)

                            self.graph_counter4 = self.graph_counter4 + 1
                            prev_command4 = self.current_command4
                            self.graph_dirty4 = True
                            #wx.PostEvent(self._notify_window, GraphEvent(self.current_command4))
                            if r.value == None:
                                wx.PostEvent(self._notify_window, GraphsValueEvent([3, 2, str(0)]))
                                self.unit4 = "unit"
                            else:
                                wx.PostEvent(self._notify_window, GraphsValueEvent([3, 2, str(r.value)]))
                                try:
                                    self.unit4 = str(r.value).split(' ')[1]
                                except IndexError:
                                    self.unit4 = "unit"
                    else:
                        self.graph_x_vals4 = np.array([])
                        self.graph_y_vals4 = np.array([])
                        self.graph_counter4 = 0

                    if self.first_time_graphs_plot:
                        self.unit1 = 'unit'
                        self.unit2 = 'unit'
                        self.unit3 = 'unit'
                        self.unit4 = 'unit'
                    if self.current_command1 == None:
                        desc1 = 'None'
                    else:
                        desc1 = self.current_command1.desc
                    if self.current_command2 == None:
                        desc2 = 'None'
                    else:
                        desc2 = self.current_command2.desc
                    if self.current_command3 == None:
                        desc3 = 'None'
                    else:
                        desc3 = self.current_command3.desc
                    if self.current_command4 == None:
                        desc4 = 'None'
                    else:
                        desc4 = self.current_command4.desc
                    wx.PostEvent(self._notify_window, GraphsEvent([(self.graph_x_vals1,self.graph_y_vals1, self.unit1, desc1, self.graph_counter1),
                                                                  (self.graph_x_vals2,self.graph_y_vals2, self.unit2, desc2, self.graph_counter2),
                                                                  (self.graph_x_vals3,self.graph_y_vals3, self.unit3, desc3, self.graph_counter3),
                                                                  (self.graph_x_vals4,self.graph_y_vals4, self.unit4, desc4, self.graph_counter4),
                                                                  (self.first_time_graphs_plot)
                                                                  ]))
                    self.first_time_graphs_plot = False
                    #time.sleep(0.2)
            elif hasattr(self._notify_window, "graphs8_panel") and curstate == 7:  # show 8Graphs tab
                if first_time_8graphs:
                    print("First time 8graphs")
                    # wx.PostEvent(self._notify_window, DestroyComboBoxEvent([]))
                    self.graph_x_vals8_1 = np.array([])
                    self.graph_y_vals8_1 = np.array([])
                    self.graph_x_vals8_2 = np.array([])
                    self.graph_y_vals8_2 = np.array([])
                    self.graph_x_vals8_3 = np.array([])
                    self.graph_y_vals8_3 = np.array([])
                    self.graph_x_vals8_4 = np.array([])
                    self.graph_y_vals8_4 = np.array([])
                    self.graph_x_vals8_5 = np.array([])
                    self.graph_y_vals8_5 = np.array([])
                    self.graph_x_vals8_6 = np.array([])
                    self.graph_y_vals8_6 = np.array([])
                    self.graph_x_vals8_7 = np.array([])
                    self.graph_y_vals8_7 = np.array([])
                    self.graph_x_vals8_8 = np.array([])
                    self.graph_y_vals8_8 = np.array([])
                    self.graph_counter8_1 = 0
                    self.graph_counter8_2 = 0
                    self.graph_counter8_3 = 0
                    self.graph_counter8_4 = 0
                    self.graph_counter8_5 = 0
                    self.graph_counter8_6 = 0
                    self.graph_counter8_7 = 0
                    self.graph_counter8_8 = 0
                    self.current_command8_1 = None
                    self.current_command8_2 = None
                    self.current_command8_3 = None
                    self.current_command8_4 = None
                    self.current_command8_5 = None
                    self.current_command8_6 = None
                    self.current_command8_7 = None
                    self.current_command8_8 = None

                    graph_commands = []
                    # wx.PostEvent(self._notify_window, GraphEvent((self.current_command, [], [])))
                    prev_command8_1 = None
                    prev_command8_2 = None
                    prev_command8_3 = None
                    prev_command8_4 = None
                    prev_command8_5 = None
                    prev_command8_6 = None
                    prev_command8_7 = None
                    prev_command8_8 = None
                    first_time_8graphs = False
                    for command in obd.commands[1]:
                        if command:
                            if command.command not in (
                            b"0100", b"0101", b"0120", b"0140", b"0103", b"0102", b"011C", b"0113", b"0141",
                            b"0151"):
                                r = self.connection.connection.query(command)
                                if r.value == None:
                                    continue
                                else:
                                    graph_commands.append(command)
                    graph_commands.append(obd.commands.ELM_VOLTAGE)
                    sensor_descriptions = []
                    # sensor_descriptions.append("None")
                    for command in graph_commands:
                        sensor_descriptions.append(command.desc)
                    self._notify_window.build_combobox_graphs8_event_finished = False
                    wx.PostEvent(self._notify_window, BuildComboBoxGraphs8Event(sensor_descriptions))
                    while not self._notify_window.build_combobox_graphs8_event_finished:
                        time.sleep(0.01)
                    self._notify_window.combobox_graphs8_set_sel_finished = False
                    wx.PostEvent(self._notify_window, SetSelectionComboBoxGraphs8Event([]))
                    while not self._notify_window.combobox_graphs8_set_sel_finished:
                        time.sleep(0.01)
                else: # second or more times

                    self._notify_window.combobox_graphs8_get_sel_finished = False
                    wx.PostEvent(self._notify_window, GetSelectionComboBoxGraphs8Event([]))
                    while not self._notify_window.combobox_graphs8_get_sel_finished:
                        time.sleep(0.01)
                    curr_selection8_1 = self._notify_window.combobox8_1_selection
                    curr_selection8_2 = self._notify_window.combobox8_2_selection
                    curr_selection8_3 = self._notify_window.combobox8_3_selection
                    curr_selection8_4 = self._notify_window.combobox8_4_selection
                    curr_selection8_5 = self._notify_window.combobox8_5_selection
                    curr_selection8_6 = self._notify_window.combobox8_6_selection
                    curr_selection8_7 = self._notify_window.combobox8_7_selection
                    curr_selection8_8 = self._notify_window.combobox8_8_selection
                    if sensor_descriptions[curr_selection8_1] == "None":
                        curr_selection8_1 = -1
                    if curr_selection8_1 != -1:
                        prev_command8_1 = self.current_command8_1
                        self.current_command8_1 = graph_commands[curr_selection8_1]
                    else:
                        self.current_command8_1 = None

                    if sensor_descriptions[curr_selection8_2] == "None":
                        curr_selection8_2 = -1
                    if curr_selection8_2 != -1:
                        prev_command8_2 = self.current_command8_2
                        self.current_command8_2 = graph_commands[curr_selection8_2]
                    else:
                        self.current_command8_2 = None

                    if sensor_descriptions[curr_selection8_3] == "None":
                        curr_selection8_3 = -1
                    if curr_selection8_3 != -1:
                        prev_command8_3 = self.current_command8_3
                        self.current_command8_3 = graph_commands[curr_selection8_3]
                    else:
                        self.current_command8_3 = None

                    if sensor_descriptions[curr_selection8_4] == "None":
                        curr_selection8_4 = -1
                    if curr_selection8_4 != -1:
                        prev_command8_4 = self.current_command8_4
                        self.current_command8_4 = graph_commands[curr_selection8_4]
                    else:
                        self.current_command8_4 = None

                    if sensor_descriptions[curr_selection8_5] == "None":
                        curr_selection8_5 = -1
                    if curr_selection8_5 != -1:
                        prev_command8_5 = self.current_command8_5
                        self.current_command8_5 = graph_commands[curr_selection8_5]
                    else:
                        self.current_command8_5 = None

                    if sensor_descriptions[curr_selection8_6] == "None":
                        curr_selection8_6 = -1
                    if curr_selection8_6 != -1:
                        prev_command8_6 = self.current_command8_6
                        self.current_command8_6 = graph_commands[curr_selection8_6]
                    else:
                        self.current_command8_6 = None

                    if sensor_descriptions[curr_selection8_7] == "None":
                        curr_selection8_7 = -1
                    if curr_selection8_7 != -1:
                        prev_command8_7 = self.current_command8_7
                        self.current_command8_7 = graph_commands[curr_selection8_7]
                    else:
                        self.current_command8_7 = None

                    if sensor_descriptions[curr_selection8_8] == "None":
                        curr_selection8_8 = -1
                    if curr_selection8_8 != -1:
                        prev_command8_8 = self.current_command8_8
                        self.current_command8_8 = graph_commands[curr_selection8_8]
                    else:
                        self.current_command8_8 = None

                    if self.current_command8_1 != None:
                        if (prev_command8_1 == None) or (prev_command8_1 != self.current_command8_1):
                            self.graph_x_vals8_1 = np.array([])
                            self.graph_y_vals8_1 = np.array([])
                            # self.graph_x_vals1 = []
                            # self.graph_y_vals1 = []
                            self.graph_counter8_1 = 0
                            wx.PostEvent(self._notify_window,
                                         Graphs8ValueEvent([0, 0, self.current_command8_1.command]))
                            wx.PostEvent(self._notify_window, Graphs8ValueEvent([0, 1, self.current_command8_1.desc]))
                        else:
                            r = self.connection.connection.query(self.current_command8_1)
                            if r.value == None:
                                reconnect()
                                continue
                            # if r.value == None:
                            #    print("r.value is None!")
                            #    raise AttributeError
                            self.graph_x_vals8_1 = np.append(self.graph_x_vals8_1, self.graph_counter8_1)
                            try:
                                self.graph_y_vals8_1 = np.append(self.graph_y_vals8_1, float(r.value.magnitude))
                            except AttributeError:
                                self.graph_y_vals8_1 = np.append(self.graph_y_vals8_1, float(0))
                            # self.graph_x_vals1.append(self.graph_counter1)
                            # self.graph_y_vals1.append(float(r.value.magnitude))
                            if len(self.graph_x_vals8_1) > 200:
                                self.graph_x_vals8_1 = np.delete(self.graph_x_vals8_1, (0))
                                self.graph_y_vals8_1 = np.delete(self.graph_y_vals8_1, (0))
                                # self.graph_x_vals1.pop(0)
                                # self.graph_y_vals1.pop(0)

                            self.graph_counter8_1 = self.graph_counter8_1 + 1
                            prev_command8_1 = self.current_command8_1
                            self.graph_dirty8_1 = True
                            # wx.PostEvent(self._notify_window, GraphEvent(self.current_command1))
                            if r.value == None:
                                wx.PostEvent(self._notify_window, Graphs8ValueEvent([0, 2, str(0)]))
                                self.unit8_1 = "unit"
                            else:
                                wx.PostEvent(self._notify_window, Graphs8ValueEvent([0, 2, str(r.value)]))
                                try:
                                    self.unit8_1 = str(r.value).split(' ')[1]
                                except IndexError:
                                    self.unit8_1 = "unit"
                    else:
                        self.graph_x_vals8_1 = np.array([])
                        self.graph_y_vals8_1 = np.array([])
                        self.graph_counter8_1 = 0

                    if self.current_command8_2 != None:
                        if (prev_command8_2 == None) or (prev_command8_2 != self.current_command8_2):
                            self.graph_x_vals8_2 = np.array([])
                            self.graph_y_vals8_2 = np.array([])
                            # self.graph_x_vals2 = []
                            # self.graph_y_vals2 = []
                            self.graph_counter8_2 = 0
                            wx.PostEvent(self._notify_window,
                                         Graphs8ValueEvent([1, 0, self.current_command8_2.command]))
                            wx.PostEvent(self._notify_window, Graphs8ValueEvent([1, 1, self.current_command8_2.desc]))
                        else:
                            r = self.connection.connection.query(self.current_command8_2)
                            if r.value == None:
                                reconnect()
                                continue
                            # if r.value == None:
                            #    print("r.value is None!")
                            #    raise AttributeError
                            self.graph_x_vals8_2 = np.append(self.graph_x_vals8_2, self.graph_counter8_2)
                            try:
                                self.graph_y_vals8_2 = np.append(self.graph_y_vals8_2, float(r.value.magnitude))
                            except AttributeError:
                                self.graph_y_vals8_2 = np.append(self.graph_y_vals8_2, float(0))
                            # self.graph_x_vals2.append(self.graph_counter2)
                            # self.graph_y_vals2.append(float(r.value.magnitude))
                            if len(self.graph_x_vals8_2) > 200:
                                self.graph_x_vals8_2 = np.delete(self.graph_x_vals8_2, (0))
                                self.graph_y_vals8_2 = np.delete(self.graph_y_vals8_2, (0))
                                # self.graph_x_vals2.pop(0)
                                # self.graph_y_vals2.pop(0)

                            self.graph_counter8_2 = self.graph_counter8_2 + 1
                            prev_command8_2 = self.current_command8_2
                            self.graph_dirty8_2 = True
                            # wx.PostEvent(self._notify_window, GraphEvent(self.current_command2))
                            if r.value == None:
                                wx.PostEvent(self._notify_window, Graphs8ValueEvent([1, 2, str(0)]))
                                self.unit8_2 = "unit"
                            else:
                                wx.PostEvent(self._notify_window, Graphs8ValueEvent([1, 2, str(r.value)]))
                                try:
                                    self.unit8_2 = str(r.value).split(' ')[1]
                                except IndexError:
                                    self.unit8_2 = "unit"
                    else:
                        self.graph_x_vals8_2 = np.array([])
                        self.graph_y_vals8_2 = np.array([])
                        self.graph_counter8_2 = 0

                    if self.current_command8_3 != None:
                        if (prev_command8_3 == None) or (prev_command8_3 != self.current_command8_3):
                            self.graph_x_vals8_3 = np.array([])
                            self.graph_y_vals8_3 = np.array([])
                            # self.graph_x_vals3 = []
                            # self.graph_y_vals3 = []
                            self.graph_counter8_3 = 0
                            wx.PostEvent(self._notify_window,
                                         Graphs8ValueEvent([2, 0, self.current_command8_3.command]))
                            wx.PostEvent(self._notify_window, Graphs8ValueEvent([2, 1, self.current_command8_3.desc]))
                        else:
                            r = self.connection.connection.query(self.current_command8_3)
                            if r.value == None:
                                reconnect()
                                continue
                            # if r.value == None:
                            #    print("r.value is None!")
                            #    raise AttributeError
                            self.graph_x_vals8_3 = np.append(self.graph_x_vals8_3, self.graph_counter8_3)
                            try:
                                self.graph_y_vals8_3 = np.append(self.graph_y_vals8_3, float(r.value.magnitude))
                            except AttributeError:
                                self.graph_y_vals8_3 = np.append(self.graph_y_vals8_3, float(0))
                            # self.graph_x_vals3.append(self.graph_counter3)
                            # self.graph_y_vals3.append(float(r.value.magnitude))
                            if len(self.graph_x_vals8_3) > 200:
                                self.graph_x_vals8_3 = np.delete(self.graph_x_vals8_3, (0))
                                self.graph_y_vals8_3 = np.delete(self.graph_y_vals8_3, (0))
                                # self.graph_x_vals3.pop(0)
                                # self.graph_y_vals3.pop(0)

                            self.graph_counter8_3 = self.graph_counter8_3 + 1
                            prev_command8_3 = self.current_command8_3
                            self.graph_dirty8_3 = True
                            # wx.PostEvent(self._notify_window, GraphEvent(self.current_command3))
                            if r.value == None:
                                wx.PostEvent(self._notify_window, Graphs8ValueEvent([2, 2, str(0)]))
                                self.unit8_3 = "unit"
                            else:
                                wx.PostEvent(self._notify_window, Graphs8ValueEvent([2, 2, str(r.value)]))
                                try:
                                    self.unit8_3 = str(r.value).split(' ')[1]
                                except IndexError:
                                    self.unit8_3 = "unit"
                    else:
                        self.graph_x_vals8_3 = np.array([])
                        self.graph_y_vals8_3 = np.array([])
                        self.graph_counter8_3 = 0

                    if self.current_command8_4 != None:
                        if (prev_command8_4 == None) or (prev_command8_4 != self.current_command8_4):
                            self.graph_x_vals8_4 = np.array([])
                            self.graph_y_vals8_4 = np.array([])
                            # self.graph_x_vals4 = []
                            # self.graph_y_vals4 = []
                            self.graph_counter8_4 = 0
                            wx.PostEvent(self._notify_window,
                                         Graphs8ValueEvent([3, 0, self.current_command8_4.command]))
                            wx.PostEvent(self._notify_window, Graphs8ValueEvent([3, 1, self.current_command8_4.desc]))
                        else:
                            r = self.connection.connection.query(self.current_command8_4)
                            if r.value == None:
                                reconnect()
                                continue
                            # if r.value == None:
                            #    print("r.value is None!")
                            #    raise AttributeError
                            self.graph_x_vals8_4 = np.append(self.graph_x_vals8_4, self.graph_counter8_4)

                            try:
                                self.graph_y_vals8_4 = np.append(self.graph_y_vals8_4, float(r.value.magnitude))
                            except AttributeError:
                                self.graph_y_vals8_4 = np.append(self.graph_y_vals8_4, float(0))

                            # self.graph_x_vals4.append(self.graph_counter4)
                            # self.graph_y_vals4.append(float(r.value.magnitude))
                            if len(self.graph_x_vals8_4) > 200:
                                self.graph_x_vals8_4 = np.delete(self.graph_x_vals8_4, (0))
                                self.graph_y_vals8_4 = np.delete(self.graph_y_vals8_4, (0))
                                # self.graph_x_vals4.pop(0)
                                # self.graph_y_vals4.pop(0)

                            self.graph_counter8_4 = self.graph_counter8_4 + 1
                            prev_command8_4 = self.current_command8_4
                            self.graph_dirty8_4 = True
                            # wx.PostEvent(self._notify_window, GraphEvent(self.current_command4))
                            if r.value == None:
                                wx.PostEvent(self._notify_window, Graphs8ValueEvent([3, 2, str(0)]))
                                self.unit8_4 = "unit"
                            else:
                                wx.PostEvent(self._notify_window, Graphs8ValueEvent([3, 2, str(r.value)]))
                                try:
                                    self.unit8_4 = str(r.value).split(' ')[1]
                                except IndexError:
                                    self.unit8_4 = "unit"
                    else:
                        self.graph_x_vals8_4 = np.array([])
                        self.graph_y_vals8_4 = np.array([])
                        self.graph_counter8_4 = 0






                    if self.current_command8_5 != None:
                        if (prev_command8_5 == None) or (prev_command8_5 != self.current_command8_5):
                            self.graph_x_vals8_5 = np.array([])
                            self.graph_y_vals8_5 = np.array([])
                            # self.graph_x_vals1 = []
                            # self.graph_y_vals1 = []
                            self.graph_counter8_5 = 0
                            wx.PostEvent(self._notify_window,
                                         Graphs8ValueEvent([4, 0, self.current_command8_5.command]))
                            wx.PostEvent(self._notify_window, Graphs8ValueEvent([4, 1, self.current_command8_5.desc]))
                        else:
                            r = self.connection.connection.query(self.current_command8_5)
                            if r.value == None:
                                reconnect()
                                continue
                            # if r.value == None:
                            #    print("r.value is None!")
                            #    raise AttributeError
                            self.graph_x_vals8_5 = np.append(self.graph_x_vals8_5, self.graph_counter8_5)
                            try:
                                self.graph_y_vals8_5 = np.append(self.graph_y_vals8_5, float(r.value.magnitude))
                            except AttributeError:
                                self.graph_y_vals8_5 = np.append(self.graph_y_vals8_5, float(0))
                            # self.graph_x_vals1.append(self.graph_counter1)
                            # self.graph_y_vals1.append(float(r.value.magnitude))
                            if len(self.graph_x_vals8_5) > 200:
                                self.graph_x_vals8_5 = np.delete(self.graph_x_vals8_5, (0))
                                self.graph_y_vals8_5 = np.delete(self.graph_y_vals8_5, (0))
                                # self.graph_x_vals1.pop(0)
                                # self.graph_y_vals1.pop(0)

                            self.graph_counter8_5 = self.graph_counter8_5 + 1
                            prev_command8_5 = self.current_command8_5
                            self.graph_dirty8_5 = True
                            # wx.PostEvent(self._notify_window, GraphEvent(self.current_command1))
                            if r.value == None:
                                wx.PostEvent(self._notify_window, Graphs8ValueEvent([4, 2, str(0)]))
                                self.unit8_5 = "unit"
                            else:
                                wx.PostEvent(self._notify_window, Graphs8ValueEvent([4, 2, str(r.value)]))
                                try:
                                    self.unit8_5 = str(r.value).split(' ')[1]
                                except IndexError:
                                    self.unit8_5 = "unit"
                    else:
                        self.graph_x_vals8_5 = np.array([])
                        self.graph_y_vals8_5 = np.array([])
                        self.graph_counter8_5 = 0



                    if self.current_command8_6 != None:
                        if (prev_command8_6 == None) or (prev_command8_6 != self.current_command8_6):
                            self.graph_x_vals8_6 = np.array([])
                            self.graph_y_vals8_6 = np.array([])
                            # self.graph_x_vals2 = []
                            # self.graph_y_vals2 = []
                            self.graph_counter8_6 = 0
                            wx.PostEvent(self._notify_window,
                                         Graphs8ValueEvent([5, 0, self.current_command8_6.command]))
                            wx.PostEvent(self._notify_window, Graphs8ValueEvent([5, 1, self.current_command8_6.desc]))
                        else:
                            r = self.connection.connection.query(self.current_command8_6)
                            if r.value == None:
                                reconnect()
                                continue
                            # if r.value == None:
                            #    print("r.value is None!")
                            #    raise AttributeError
                            self.graph_x_vals8_6 = np.append(self.graph_x_vals8_6, self.graph_counter8_6)
                            try:
                                self.graph_y_vals8_6 = np.append(self.graph_y_vals8_6, float(r.value.magnitude))
                            except AttributeError:
                                self.graph_y_vals8_6 = np.append(self.graph_y_vals8_6, float(0))
                            # self.graph_x_vals2.append(self.graph_counter2)
                            # self.graph_y_vals2.append(float(r.value.magnitude))
                            if len(self.graph_x_vals8_6) > 200:
                                self.graph_x_vals8_6 = np.delete(self.graph_x_vals8_6, (0))
                                self.graph_y_vals8_6 = np.delete(self.graph_y_vals8_6, (0))
                                # self.graph_x_vals2.pop(0)
                                # self.graph_y_vals2.pop(0)

                            self.graph_counter8_6 = self.graph_counter8_6 + 1
                            prev_command6 = self.current_command8_6
                            self.graph_dirty8_6 = True
                            # wx.PostEvent(self._notify_window, GraphEvent(self.current_command2))
                            if r.value == None:
                                wx.PostEvent(self._notify_window, Graphs8ValueEvent([5, 2, str(0)]))
                                self.unit8_6 = "unit"
                            else:
                                wx.PostEvent(self._notify_window, Graphs8ValueEvent([5, 2, str(r.value)]))
                                try:
                                    self.unit8_6 = str(r.value).split(' ')[1]
                                except IndexError:
                                    self.unit8_6 = "unit"
                    else:
                        self.graph_x_vals8_6 = np.array([])
                        self.graph_y_vals8_6 = np.array([])
                        self.graph_counter8_6 = 0



                    if self.current_command8_7 != None:
                        if (prev_command8_7 == None) or (prev_command8_7 != self.current_command8_7):
                            self.graph_x_vals8_7 = np.array([])
                            self.graph_y_vals8_7 = np.array([])
                            # self.graph_x_vals3 = []
                            # self.graph_y_vals3 = []
                            self.graph_counter8_7 = 0
                            wx.PostEvent(self._notify_window,
                                         Graphs8ValueEvent([6, 0, self.current_command8_7.command]))
                            wx.PostEvent(self._notify_window, Graphs8ValueEvent([6, 1, self.current_command8_7.desc]))
                        else:
                            r = self.connection.connection.query(self.current_command8_7)
                            if r.value == None:
                                reconnect()
                                continue
                            # if r.value == None:
                            #    print("r.value is None!")
                            #    raise AttributeError
                            self.graph_x_vals8_7 = np.append(self.graph_x_vals8_7, self.graph_counter8_7)
                            try:
                                self.graph_y_vals8_7 = np.append(self.graph_y_vals8_7, float(r.value.magnitude))
                            except AttributeError:
                                self.graph_y_vals8_7 = np.append(self.graph_y_vals8_7, float(0))
                            # self.graph_x_vals3.append(self.graph_counter3)
                            # self.graph_y_vals3.append(float(r.value.magnitude))
                            if len(self.graph_x_vals8_7) > 200:
                                self.graph_x_vals8_7 = np.delete(self.graph_x_vals8_7, (0))
                                self.graph_y_vals8_7 = np.delete(self.graph_y_vals8_7, (0))
                                # self.graph_x_vals3.pop(0)
                                # self.graph_y_vals3.pop(0)

                            self.graph_counter8_7 = self.graph_counter8_7 + 1
                            prev_command8_7 = self.current_command8_7
                            self.graph_dirty8_7 = True
                            # wx.PostEvent(self._notify_window, GraphEvent(self.current_command3))
                            if r.value == None:
                                wx.PostEvent(self._notify_window, Graphs8ValueEvent([6, 2, str(0)]))
                                self.unit8_7 = "unit"
                            else:
                                wx.PostEvent(self._notify_window, Graphs8ValueEvent([6, 2, str(r.value)]))
                                try:
                                    self.unit8_7 = str(r.value).split(' ')[1]
                                except IndexError:
                                    self.unit8_7 = "unit"
                    else:
                        self.graph_x_vals8_7 = np.array([])
                        self.graph_y_vals8_7 = np.array([])
                        self.graph_counter8_7 = 0

                    if self.current_command8_8 != None:
                        if (prev_command8_8 == None) or (prev_command8_8 != self.current_command8_8):
                            self.graph_x_vals8_8 = np.array([])
                            self.graph_y_vals8_8 = np.array([])
                            # self.graph_x_vals4 = []
                            # self.graph_y_vals4 = []
                            self.graph_counter8_8 = 0
                            wx.PostEvent(self._notify_window,
                                         Graphs8ValueEvent([7, 0, self.current_command8_8.command]))
                            wx.PostEvent(self._notify_window, Graphs8ValueEvent([7, 1, self.current_command8_8.desc]))
                        else:
                            r = self.connection.connection.query(self.current_command8_8)
                            if r.value == None:
                                reconnect()
                                continue
                            # if r.value == None:
                            #    print("r.value is None!")
                            #    raise AttributeError
                            self.graph_x_vals8_8 = np.append(self.graph_x_vals8_8, self.graph_counter8_8)

                            try:
                                self.graph_y_vals8_8 = np.append(self.graph_y_vals8_8, float(r.value.magnitude))
                            except AttributeError:
                                self.graph_y_vals8_8 = np.append(self.graph_y_vals8_8, float(0))

                            # self.graph_x_vals4.append(self.graph_counter4)
                            # self.graph_y_vals4.append(float(r.value.magnitude))
                            if len(self.graph_x_vals8_8) > 200:
                                self.graph_x_vals8_8 = np.delete(self.graph_x_vals8_8, (0))
                                self.graph_y_vals8_8 = np.delete(self.graph_y_vals8_8, (0))
                                # self.graph_x_vals4.pop(0)
                                # self.graph_y_vals4.pop(0)

                            self.graph_counter8_8 = self.graph_counter8_8 + 1
                            prev_command8_8 = self.current_command8_8
                            self.graph_dirty8_8 = True
                            # wx.PostEvent(self._notify_window, GraphEvent(self.current_command4))
                            if r.value == None:
                                wx.PostEvent(self._notify_window, Graphs8ValueEvent([7, 2, str(0)]))
                                self.unit8_8 = "unit"
                            else:
                                wx.PostEvent(self._notify_window, Graphs8ValueEvent([7, 2, str(r.value)]))
                                try:
                                    self.unit8_8 = str(r.value).split(' ')[1]
                                except IndexError:
                                    self.unit8_8 = "unit"
                    else:
                        self.graph_x_vals8_8 = np.array([])
                        self.graph_y_vals8_8 = np.array([])
                        self.graph_counter8_8 = 0



                    if self.first_time_8graphs_plot:
                        self.unit8_1 = 'unit'
                        self.unit8_2 = 'unit'
                        self.unit8_3 = 'unit'
                        self.unit8_4 = 'unit'
                        self.unit8_5 = 'unit'
                        self.unit8_6 = 'unit'
                        self.unit8_7 = 'unit'
                        self.unit8_8 = 'unit'
                    if self.current_command8_1 == None:
                        desc8_1 = 'None'
                    else:
                        desc8_1 = self.current_command8_1.desc


                    if self.current_command8_2 == None:
                        desc8_2 = 'None'
                    else:
                        desc8_2 = self.current_command8_2.desc


                    if self.current_command8_3 == None:
                        desc8_3 = 'None'
                    else:
                        desc8_3 = self.current_command8_3.desc


                    if self.current_command8_4 == None:
                        desc8_4 = 'None'
                    else:
                        desc8_4 = self.current_command8_4.desc


                    if self.current_command8_5 == None:
                        desc8_5 = 'None'
                    else:
                        desc8_5 = self.current_command8_5.desc


                    if self.current_command8_6 == None:
                        desc8_6 = 'None'
                    else:
                        desc8_6 = self.current_command8_6.desc



                    if self.current_command8_7 == None:
                        desc8_7 = 'None'
                    else:
                        desc8_7 = self.current_command8_7.desc
                    if self.current_command8_8 == None:
                        desc8_8 = 'None'
                    else:
                        desc8_8 = self.current_command8_8.desc

                    wx.PostEvent(self._notify_window, Graphs8Event(
                        [(self.graph_x_vals8_1, self.graph_y_vals8_1, self.unit8_1, desc8_1, self.graph_counter8_1),
                         (self.graph_x_vals8_2, self.graph_y_vals8_2, self.unit8_2, desc8_2, self.graph_counter8_2),
                         (self.graph_x_vals8_3, self.graph_y_vals8_3, self.unit8_3, desc8_3, self.graph_counter8_3),
                         (self.graph_x_vals8_4, self.graph_y_vals8_4, self.unit8_4, desc8_4, self.graph_counter8_4),
                         (self.graph_x_vals8_5, self.graph_y_vals8_5, self.unit8_5, desc8_5, self.graph_counter8_5),
                         (self.graph_x_vals8_6, self.graph_y_vals8_6, self.unit8_6, desc8_6, self.graph_counter8_6),
                         (self.graph_x_vals8_7, self.graph_y_vals8_7, self.unit8_7, desc8_7, self.graph_counter8_7),
                         (self.graph_x_vals8_8, self.graph_y_vals8_8, self.unit8_8, desc8_8, self.graph_counter8_8),
                         (self.first_time_8graphs_plot)
                         ]))
                    self.first_time_8graphs_plot = False
                    # time.sleep(0.2)
            elif curstate == 8:
                r = self.connection.connection.query(obd.commands.RPM)
                if r.value == None:
                    reconnect()
                    continue
            time_end = datetime.datetime.now()
            first_time = False

        self.state = "finished"
        print ("state is finished")
        self.stop()



    """
    def off(self, id):
        if id >= 0 and id < len(self.active): 
            self.active[id] = 0
        else:
            debug("Invalid sensor id")
    def on(self, id):
        if id >= 0 and id < len(self.active): 
            self.active[id] = 1
        else:
            debug("Invalid sensor id")

    def all_off(self):
        for i in range(0, len(self.active)):
            self.off(i)
    def all_on(self):
        for i in range(0, len(self.active)):
            self.off(i)
    """

    def stop(self):
        #self._notify_window.ThreadControl = 666

        try: # if stop is called before any connection port is not defined (and not connected )
            self.connection.connection.close()
        except Exception as e:\
            print(e)

        #if self.port != None: #if stop is called before any connection port is not defined (and not connected )
        #  self.port.close()
        wx.PostEvent(self._notify_window, StatusEvent([0, 1, "Disconnected"]))
        wx.PostEvent(self._notify_window, StatusEvent([1, 1, "----"]))
        wx.PostEvent(self._notify_window, StatusEvent([2, 1, "----"]))
        wx.PostEvent(self._notify_window, StatusEvent([3, 1, "----"]))
        wx.PostEvent(self._notify_window, StatusEvent([4, 1, "----"]))
        wx.PostEvent(self._notify_window, StatusEvent([5, 1, "----"]))
        wx.PostEvent(self._notify_window, CloseEvent([]))
        print("Sensor producer has stopped.")

# class producer end

