#!/usr/bin/env python
############################################################################
#
# wxgui.py
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
############################################################################

#import pint
#from mem_top import mem_top
#import logging
import numpy as np
#import multiprocessing
#from multiprocessing import Queue, Process
# import wxversion
# wxversion.select("2.6")
#import matplotlib
from wx.lib import plot as wxplot
#from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas

#from matplotlib.figure import Figure
#import matplotlib.pyplot as plt
#matplotlib.use('wxAgg')
#from matplotlib.animation import FuncAnimation
#from matplotlib import style
#import numpy.oldnumeric as _Numeric

#from wxplot import PlotCanvas, PlotGraphics, PolyLine, PolyMarker, PolySpline
import gc
#from pympler.tracker import SummaryTracker
#tracker = SummaryTracker()
import traceback
import wx
#import pdb
import obd_io  # OBD2 funcs
import os  # os.environ
#import decimal
#import glob
import datetime
import threading
import sys
import serial
#import platform
import time
import configparser  # safe application configuration
import webbrowser  # open browser from python
#from multiprocessing import Process
#from multiprocessing import Queue

from obd2_codes import pcodes
#from obd2_codes import ptest

from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin
import obd
#from obd import OBDStatus

from obd.utils import OBDStatus




ID_ABOUT = 101
ID_EXIT = 110
ID_CONFIG = 500
ID_CLEAR = 501
ID_GETC = 502
ID_RESET = 503
ID_LOOK = 504
ALL_ON = 505
ALL_OFF = 506

ID_DISCONNECT = 507
ID_HELP_ABOUT = 508
ID_HELP_VISIT = 509
ID_HELP_ORDER = 510

# Define notification event for sensor result window
EVT_RESULT_ID = 1000
EVT_GRAPH_VALUE_ID = 1036
EVT_GRAPHS_VALUE_ID = 1048
EVT_GRAPHS8_VALUE_ID = 1051
EVT_GRAPH_ID = 1035
EVT_GRAPHS_ID = 1049
EVT_GRAPHS8_ID = 1050
EVT_COMBOBOX = 1036
EVT_CLOSE_ID = 1037
EVT_BUILD_COMBOBOXGRAPH_ID = 1038
EVT_BUILD_COMBOBOXGRAPHS_ID = 1045
EVT_BUILD_COMBOBOXGRAPHS8_ID = 1102
EVT_DESTROY_COMBOBOX_ID = 1039
EVT_COMBOBOXGRAPH_GETSELECTION_ID = 1040
EVT_COMBOBOXGRAPHS_GETSELECTION_ID = 1046
EVT_COMBOBOXGRAPHS8_GETSELECTION_ID = 1100
EVT_COMBOBOXGRAPH_SETSELECTION_ID = 1044
EVT_COMBOBOXGRAPHS_SETSELECTION_ID = 1047
EVT_COMBOBOXGRAPHS8_SETSELECTION_ID = 1101
EVT_INSERT_SENSOR_ROW_ID = 1041
EVT_INSERT_FREEZEFRAME_ROW_ID = 1042
EVT_FREEZEFRAME_RESULT_ID = 1043

EVT_COMBOBOXGRAPHS8_GETSELECTION_ID =1105
EVT_COMBOBOXGRAPHS8_SETSELECTION_ID =1106

lock = threading.Lock()

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

TESTS = ["MISFIRE_MONITORING",
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
    "PM_FILTER_MONITORING"]

def EVT_RESULT(win, func, id):
    """Define Result Event."""
    win.Connect(-1, -1, id, func)

"""
class MyPanel(wx.Panel):
    def __init__(self, parent):
        super(MyPanel, self).__init__(parent)

        self.label = wx.StaticText(self, label="What Programming Language You Like?", pos=(50, 30))

        languages = ['Java', 'C++', 'C#', 'Python', 'Erlang', 'PHP', 'Ruby']
        self.combobox = wx.ComboBox(self, choices=languages, pos=(50, 50))

        self.label2 = wx.StaticText(self, label="", pos=(50, 80))

        self.Bind(wx.EVT_COMBOBOX, self.OnCombo)

    def OnCombo(self, event):
        self.label2.SetLabel("You Like " + self.combobox.GetValue())
"""
# event pro akutalizaci Trace tabu
class ResultEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""

    def __init__(self, data):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_RESULT_ID)
        self.data = data

class FreezeframeResultEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""

    def __init__(self, data):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_FREEZEFRAME_RESULT_ID)
        self.data = data

class InsertSensorRowEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""

    def __init__(self, data):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_INSERT_SENSOR_ROW_ID)
        self.data = data

class InsertFreezeframeRowEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""

    def __init__(self, data):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_INSERT_FREEZEFRAME_ROW_ID)
        self.data = data

class BuildComboBoxGraphEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""

    def __init__(self, data):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_BUILD_COMBOBOXGRAPH_ID)
        self.data = data

class BuildComboBoxGraphsEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""

    def __init__(self, data):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_BUILD_COMBOBOXGRAPHS_ID)
        self.data = data

class BuildComboBoxGraphs8Event(wx.PyEvent):
    """Simple event to carry arbitrary result data."""

    def __init__(self, data):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_BUILD_COMBOBOXGRAPHS8_ID)
        self.data = data

class DestroyComboBoxEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""

    def __init__(self, data):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_DESTROY_COMBOBOX_ID)
        self.data = data

class GetSelectionComboBoxGraphEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""

    def __init__(self, data):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_COMBOBOXGRAPH_GETSELECTION_ID)
        self.data = data

class GetSelectionComboBoxGraphsEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""

    def __init__(self, data):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_COMBOBOXGRAPHS_GETSELECTION_ID)
        self.data = data

class GetSelectionComboBoxGraphs8Event(wx.PyEvent):
    """Simple event to carry arbitrary result data."""

    def __init__(self, data):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_COMBOBOXGRAPHS8_GETSELECTION_ID)
        self.data = data

class SetSelectionComboBoxGraphEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""

    def __init__(self, data):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_COMBOBOXGRAPH_SETSELECTION_ID)
        self.data = data

class SetSelectionComboBoxGraphsEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""

    def __init__(self, data):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_COMBOBOXGRAPHS_SETSELECTION_ID)
        self.data = data

class SetSelectionComboBoxGraphs8Event(wx.PyEvent):
    """Simple event to carry arbitrary result data."""

    def __init__(self, data):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_COMBOBOXGRAPHS8_SETSELECTION_ID)
        self.data = data



class GraphValueEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""

    def __init__(self, data):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_GRAPH_VALUE_ID)
        self.data = data

class GraphsValueEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""

    def __init__(self, data):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_GRAPHS_VALUE_ID)
        self.data = data

class Graphs8ValueEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""

    def __init__(self, data):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_GRAPHS8_VALUE_ID)
        self.data = data

class GraphEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""

    def __init__(self, data):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_GRAPH_ID)
        self.data = data

class GraphsEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""

    def __init__(self, data):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_GRAPHS_ID)
        self.data = data

class Graphs8Event(wx.PyEvent):
    """Simple event to carry arbitrary result data."""

    def __init__(self, data):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_GRAPHS8_ID)
        self.data = data

# event pro aktualizaci DTC tabu
EVT_DTC_ID = 1001


class DTCEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""

    def __init__(self, data):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_DTC_ID)
        self.data = data


# event pro aktualizaci status tabu
EVT_STATUS_ID = 1002


class StatusEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""

    def __init__(self, data):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_STATUS_ID)
        self.data = data

class CloseEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""

    def __init__(self, data):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_CLOSE_ID)
        self.data = data


# event pro aktualizaci tests tabu
EVT_TESTS_ID = 1003


class TestEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""

    def __init__(self, data):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_TESTS_ID)
        self.data = data


# defines notification event for debug tracewindow
from debugEvent import *


class MyApp(wx.App):
    # A listctrl which auto-resizes the column boxes to fill
    class MyListCtrl(wx.ListCtrl, ListCtrlAutoWidthMixin):
        def __init__(self, parent, id, pos=wx.DefaultPosition,
                     size=wx.DefaultSize, style=0):
            wx.ListCtrl.__init__(self, parent, id, pos, size, style)
            ListCtrlAutoWidthMixin.__init__(self)

    class sensorProducer(threading.Thread):
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
            threading.Thread.__init__(self)
            self.state = "started"

        def initCommunication(self):
            try:
                self.connection.close()
            except:
                pass
            wx.PostEvent(self._notify_window, StatusEvent([0, 1, "Connecting...."]))
            self.connection = obd_io.OBDConnection(self.portName, self._notify_window, self.baudrate, self.SERTIMEOUT,self.RECONNATTEMPTS, self.FAST)
            if self.connection.connection.status() != 'Car Connected':  # Cant open serial port
                print(self.connection.connection.status())
                #wx.PostEvent(self._notify_window, StatusEvent([666]))  # signal apl, that communication was disconnected
                #wx.PostEvent(self._notify_window, StatusEvent([0, 1, "Error cant connect..."]))
                #self.state="finished"
                self.stop()
                return None
            elif self.connection.connection.status() == 'Car Connected':
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
                print (self._notify_window.ThreadControl)
                if self.connection.connection.status() != OBDStatus.CAR_CONNECTED:
                    reconnect()
                    continue
                prevstate = curstate
                curstate = self._nb.GetSelection()  # picking the tab in the GUI




                if not first_time:
                    diff = (time_end - time_start).total_seconds()
                    if (diff < 0.08333) and (diff > 0):
                        sleep_time = 0.08333 - diff
                        time.sleep(sleep_time)
                        print("Slept for "+str(sleep_time)+" seconds.")
                time_start = datetime.datetime.now()



                if curstate != 5 and self.graph_counter != 0:
                    self.graph_x_vals = np.array([])
                    self.graph_y_vals = np.array([])
                    self.graph_counter = 0
                    self.first_time_graph_plot = True
                    if self.first_time_graph_plot:
                        self.unit = 'unit'
                    if self.current_command == None:
                        desc = 'None'
                    else:
                        desc = self.current_command.desc
                    wx.PostEvent(self._notify_window,
                                 GraphEvent(
                                     [(self.graph_x_vals, self.graph_y_vals, self.unit, desc, self.graph_counter),
                                      (self.first_time_graph_plot)
                                      ]))
                    self.first_time_graph_plot = False
                    wx.PostEvent(self._notify_window, GraphValueEvent([0, 0, self.current_command.command]))
                    wx.PostEvent(self._notify_window, GraphValueEvent([0, 1, self.current_command.desc]))



                if curstate != 6 and self.graph_counter1 != 0:
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

                if curstate != 7 and self.graph_counter8_1 != 0:
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
                    s = self.connection.connection.query(obd.commands.RPM)
                    if s.value == None:
                        reconnect()
                        continue

                    r = self.connection.connection.query(obd.commands.ELM_VOLTAGE)
                    self.ELMvoltage = str(r.value)
                    wx.PostEvent(self._notify_window, StatusEvent([5, 1, str(self.ELMvoltage)]))



                elif curstate == 1:  # show tests tab
                    try:
                        s = self.connection.connection.query(obd.commands.RPM)
                        if s.value == None:
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
                    s = self.connection.connection.query(obd.commands.RPM)
                    if s.value == None:
                        reconnect()
                        continue

                    if first_time_sensors:
                        sensor_list = []
                        counter = 0
                        first_time_sensors = False
                        for command in obd.commands[1]:
                            if command:
                                if command.command not in (b"0100" , b"0101", b"0120", b"0140", b"0103", b"0102", b"011C", b"0113", b"0141", b"0151"):
                                    s = self.connection.connection.query(command)
                                    if s.value == None:
                                        continue
                                    else:
                                        sensor_list.append([command, command.desc])

                                        #app.sensors.InsertItem(counter, "")
                                        wx.PostEvent(self._notify_window, InsertSensorRowEvent(counter))
                                        wx.PostEvent(self._notify_window, ResultEvent([counter, 0, str(command.command)]))
                                        wx.PostEvent(self._notify_window, ResultEvent([counter, 1, str(command.desc)]))
                                        wx.PostEvent(self._notify_window, ResultEvent([counter, 2, str(s.value)]))
                                        counter = counter + 1
                        #s = self.connection.connection.query(obd.commands.ELM_VOLTAGE)
                        #sensor_list.append([obd.commands.ELM_VOLTAGE, obd.commands.ELM_VOLTAGE.desc, str(s.value)])
                        #wx.PostEvent(self._notify_window, InsertSensorRowEvent(counter))
                        #wx.PostEvent(self._notify_window, ResultEvent([counter, 0, str(obd.commands.ELM_VOLTAGE.command)]))
                        #wx.PostEvent(self._notify_window, ResultEvent([counter, 1, str(obd.commands.ELM_VOLTAGE.desc)]))
                        #wx.PostEvent(self._notify_window, ResultEvent([counter, 2, str(s.value)]))
                    else:
                        #for i in range(0, app.sensors.GetItemCount()):
                        #    app.sensors.DeleteItem(0)
                        counter = 0
                        for sens in sensor_list:
                            s = self.connection.connection.query(sens[0])
                            if s.value == None:
                                #reconnect()
                                continue
                            wx.PostEvent(self._notify_window, ResultEvent([counter, 0, str(sens[0].command)]))
                            wx.PostEvent(self._notify_window, ResultEvent([counter, 1, str(sens[1])]))
                            wx.PostEvent(self._notify_window, ResultEvent([counter, 2, str(s.value)]))
                            counter = counter + 1

                elif curstate == 3:  # show DTC tab
                    s = self.connection.connection.query(obd.commands.RPM)
                    if s.value == None:
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
                    s = self.connection.connection.query(obd.commands.RPM)
                    if s.value == None:
                        reconnect()
                        continue
                    if first_time_freezeframe:
                        freezeframe_list = []
                        counter = 0
                        first_time_freezeframe = False
                        for command in obd.commands[2]:
                            if command:
                                if command.command not in (b"0200" , b"0201", b"0220", b"0240", b"0203", b"0202", b"021C", b"0213", b"0241", b"0251"):
                                    s = self.connection.connection.query(command)
                                    if s.value == None:
                                        continue
                                    else:
                                        freezeframe_list.append([command.command, command.desc, str(s.value)])
                                        wx.PostEvent(self._notify_window, InsertFreezeframeRowEvent(counter))
                                        wx.PostEvent(self._notify_window, FreezeframeResultEvent([counter, 0, str(command.command)]))
                                        wx.PostEvent(self._notify_window, FreezeframeResultEvent([counter, 1, str(command.desc)]))
                                        wx.PostEvent(self._notify_window, FreezeframeResultEvent([counter, 2, str(s.value)]))
                                        counter = counter + 1
                    else:
                        counter = 0
                        for sens in freezeframe_list:
                            for command in obd.commands[2]:
                                if command.command == sens[0]:
                                    s = self.connection.connection.query(command)
                                    if s.value == None:
                                        #reconnect()
                                        continue
                                    freezeframe_list[counter] = [command.command, command.desc, str(s.value)]
                                    counter = counter + 1
                        counter = 0
                        for sens in freezeframe_list:
                            wx.PostEvent(self._notify_window, FreezeframeResultEvent([counter, 0, str(sens[0])]))
                            wx.PostEvent(self._notify_window, FreezeframeResultEvent([counter, 1, str(sens[1])]))
                            wx.PostEvent(self._notify_window, FreezeframeResultEvent([counter, 2, str(sens[2])]))
                            counter = counter + 1
                            #if sens[2] == "None" and sens[0]!='0203':
                            #    raise AttributeError

                elif curstate == 5:  # show Graph tab
                    if first_time_graph:
                        print("First time graph")
                        #wx.PostEvent(self._notify_window, DestroyComboBoxEvent([]))
                        self.graph_x_vals = np.array([])
                        self.graph_y_vals = np.array([])
                        self.graph_counter = 0
                        self.current_command = None


                        graph_commands = []

                        #wx.PostEvent(self._notify_window, GraphEvent((self.current_command, [], [])))
                        prev_command = None

                        first_time_graph = False
                        for command in obd.commands[1]:
                            if command:
                                if command.command not in (b"0100" , b"0101", b"0120", b"0140", b"0103", b"0102", b"011C", b"0113", b"0141", b"0151"):
                                    s = self.connection.connection.query(command)
                                    if s.value == None:
                                        continue
                                    else:
                                        graph_commands.append(command)
                        graph_commands.append(obd.commands.ELM_VOLTAGE)
                        sensor_descriptions = []
                        #sensor_descriptions.append("None")
                        for command in graph_commands:
                            sensor_descriptions.append(command.desc)
                        app.build_combobox_graph_event_finished = False
                        wx.PostEvent(self._notify_window, BuildComboBoxGraphEvent(sensor_descriptions))
                        while not app.build_combobox_graph_event_finished:
                            time.sleep(0.01)
                        app.combobox_graph_set_sel_finished=False
                        wx.PostEvent(self._notify_window, SetSelectionComboBoxGraphEvent([]))
                        while not app.combobox_graph_set_sel_finished:
                            time.sleep(0.01)
                    else:

                        app.combobox_graph_get_sel_finished = False
                        wx.PostEvent(self._notify_window, GetSelectionComboBoxGraphEvent([]))
                        while not app.combobox_graph_get_sel_finished:
                            time.sleep(0.01)
                        curr_selection = app.combobox_selection

                        if sensor_descriptions[curr_selection] == "None":
                            curr_selection = -1
                        if curr_selection != -1:
                            prev_command = self.current_command
                            self.current_command = graph_commands[curr_selection]
                        else:
                            self.current_command = None

                        if self.current_command != None:
                            if (prev_command == None) or (prev_command != self.current_command):
                                self.graph_x_vals = np.array([])
                                self.graph_y_vals = np.array([])
                                self.graph_counter = 0
                                wx.PostEvent(self._notify_window, GraphValueEvent([0, 0, self.current_command.command]))
                                wx.PostEvent(self._notify_window, GraphValueEvent([0, 1, self.current_command.desc]))
                            else:
                                s = self.connection.connection.query(self.current_command)
                                if s.value == None:
                                    reconnect()
                                    continue
                                self.graph_x_vals = np.append(self.graph_x_vals, self.graph_counter)
                                try:
                                    self.graph_y_vals = np.append(self.graph_y_vals, float(s.value.magnitude))
                                except AttributeError:
                                    self.graph_y_vals = np.append(self.graph_y_vals, float(0))
                                if len(self.graph_x_vals) > 450:
                                    self.graph_x_vals = np.delete(self.graph_x_vals, (0))
                                    self.graph_y_vals = np.delete(self.graph_y_vals, (0))

                                self.graph_counter = self.graph_counter + 1
                                prev_command = self.current_command


                                if s.value == None:
                                    wx.PostEvent(self._notify_window, GraphValueEvent([0, 2, str(0)]))
                                    self.unit = "unit"
                                else:
                                    wx.PostEvent(self._notify_window, GraphValueEvent([0, 2, str(s.value)]))
                                    try:
                                        self.unit = str(s.value).split(' ')[1]
                                    except IndexError:
                                        self.unit = "unit"


                        else:
                            self.graph_x_vals = np.array([])
                            self.graph_y_vals = np.array([])
                            self.graph_counter = 0


                        if self.first_time_graph_plot:
                            self.unit = 'unit'

                        if self.current_command == None:
                            desc = 'None'
                        else:
                            desc = self.current_command.desc

                        wx.PostEvent(self._notify_window, GraphEvent([(self.graph_x_vals,self.graph_y_vals, self.unit, desc, self.graph_counter),
                                                                      (self.first_time_graph_plot)
                                                                      ]))
                        self.first_time_graph_plot = False
                        #time.sleep(0.2)

                elif curstate == 6:  # show 4Graphs tab
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
                                    s = self.connection.connection.query(command)
                                    if s.value == None:
                                        continue
                                    else:
                                        graph_commands.append(command)
                        graph_commands.append(obd.commands.ELM_VOLTAGE)
                        sensor_descriptions = []
                        #sensor_descriptions.append("None")
                        for command in graph_commands:
                            sensor_descriptions.append(command.desc)
                        app.build_combobox_graphs_event_finished = False
                        wx.PostEvent(self._notify_window, BuildComboBoxGraphsEvent(sensor_descriptions))
                        while not app.build_combobox_graphs_event_finished:
                            time.sleep(0.01)
                        app.combobox_graphs_set_sel_finished=False
                        wx.PostEvent(self._notify_window, SetSelectionComboBoxGraphsEvent([]))
                        while not app.combobox_graphs_set_sel_finished:
                            time.sleep(0.01)
                    else:

                        app.combobox_graphs_get_sel_finished = False
                        wx.PostEvent(self._notify_window, GetSelectionComboBoxGraphsEvent([]))
                        while not app.combobox_graphs_get_sel_finished:
                            time.sleep(0.01)
                        curr_selection1 = app.combobox1_selection
                        curr_selection2 = app.combobox2_selection
                        curr_selection3 = app.combobox3_selection
                        curr_selection4 = app.combobox4_selection
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
                                s = self.connection.connection.query(self.current_command1)
                                if s.value == None:
                                    reconnect()
                                    continue
                                #if s.value == None:
                                #    print("s.value is None!")
                                #    raise AttributeError
                                self.graph_x_vals1 = np.append(self.graph_x_vals1, self.graph_counter1)
                                try:
                                    self.graph_y_vals1 = np.append(self.graph_y_vals1, float(s.value.magnitude))
                                except AttributeError:
                                    self.graph_y_vals1 = np.append(self.graph_y_vals1, float(0))
                                #self.graph_x_vals1.append(self.graph_counter1)
                                #self.graph_y_vals1.append(float(s.value.magnitude))
                                if len(self.graph_x_vals1) > 200:
                                    self.graph_x_vals1 = np.delete(self.graph_x_vals1, (0))
                                    self.graph_y_vals1 = np.delete(self.graph_y_vals1, (0))
                                    #self.graph_x_vals1.pop(0)
                                    #self.graph_y_vals1.pop(0)

                                self.graph_counter1 = self.graph_counter1 + 1
                                prev_command1 = self.current_command1
                                self.graph_dirty1 = True
                                #wx.PostEvent(self._notify_window, GraphEvent(self.current_command1))
                                if s.value == None:
                                    wx.PostEvent(self._notify_window, GraphsValueEvent([0, 2, str(0)]))
                                    self.unit1 = "unit"
                                else:
                                    wx.PostEvent(self._notify_window, GraphsValueEvent([0, 2, str(s.value)]))
                                    try:
                                        self.unit1 = str(s.value).split(' ')[1]
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
                                s = self.connection.connection.query(self.current_command2)
                                if s.value == None:
                                    reconnect()
                                    continue
                                #if s.value == None:
                                #    print("s.value is None!")
                                #    raise AttributeError
                                self.graph_x_vals2 = np.append(self.graph_x_vals2, self.graph_counter2)
                                try:
                                    self.graph_y_vals2 = np.append(self.graph_y_vals2, float(s.value.magnitude))
                                except AttributeError:
                                    self.graph_y_vals2 = np.append(self.graph_y_vals2, float(0))
                                #self.graph_x_vals2.append(self.graph_counter2)
                                #self.graph_y_vals2.append(float(s.value.magnitude))
                                if len(self.graph_x_vals2) > 200:
                                    self.graph_x_vals2 = np.delete(self.graph_x_vals2, (0))
                                    self.graph_y_vals2 = np.delete(self.graph_y_vals2, (0))
                                    #self.graph_x_vals2.pop(0)
                                    #self.graph_y_vals2.pop(0)

                                self.graph_counter2 = self.graph_counter2 + 1
                                prev_command2 = self.current_command2
                                self.graph_dirty2 = True
                                #wx.PostEvent(self._notify_window, GraphEvent(self.current_command2))
                                if s.value == None:
                                    wx.PostEvent(self._notify_window, GraphsValueEvent([1, 2, str(0)]))
                                    self.unit2 = "unit"
                                else:
                                    wx.PostEvent(self._notify_window, GraphsValueEvent([1, 2, str(s.value)]))
                                    try:
                                        self.unit2 = str(s.value).split(' ')[1]
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
                                s = self.connection.connection.query(self.current_command3)
                                if s.value == None:
                                    reconnect()
                                    continue
                                #if s.value == None:
                                #    print("s.value is None!")
                                #    raise AttributeError
                                self.graph_x_vals3 = np.append(self.graph_x_vals3, self.graph_counter3)
                                try:
                                    self.graph_y_vals3 = np.append(self.graph_y_vals3, float(s.value.magnitude))
                                except AttributeError:
                                    self.graph_y_vals3 = np.append(self.graph_y_vals3, float(0))
                                #self.graph_x_vals3.append(self.graph_counter3)
                                #self.graph_y_vals3.append(float(s.value.magnitude))
                                if len(self.graph_x_vals3) > 200:
                                    self.graph_x_vals3 = np.delete(self.graph_x_vals3, (0))
                                    self.graph_y_vals3 = np.delete(self.graph_y_vals3, (0))
                                    #self.graph_x_vals3.pop(0)
                                    #self.graph_y_vals3.pop(0)

                                self.graph_counter3 = self.graph_counter3 + 1
                                prev_command3 = self.current_command3
                                self.graph_dirty3 = True
                                #wx.PostEvent(self._notify_window, GraphEvent(self.current_command3))
                                if s.value == None:
                                    wx.PostEvent(self._notify_window, GraphsValueEvent([2, 2, str(0)]))
                                    self.unit3 = "unit"
                                else:
                                    wx.PostEvent(self._notify_window, GraphsValueEvent([2, 2, str(s.value)]))
                                    try:
                                        self.unit3 = str(s.value).split(' ')[1]
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
                                s = self.connection.connection.query(self.current_command4)
                                if s.value == None:
                                    reconnect()
                                    continue
                                #if s.value == None:
                                #    print("s.value is None!")
                                #    raise AttributeError
                                self.graph_x_vals4 = np.append(self.graph_x_vals4, self.graph_counter4)

                                try:
                                    self.graph_y_vals4 = np.append(self.graph_y_vals4, float(s.value.magnitude))
                                except AttributeError:
                                    self.graph_y_vals4 = np.append(self.graph_y_vals4, float(0))

                                #self.graph_x_vals4.append(self.graph_counter4)
                                #self.graph_y_vals4.append(float(s.value.magnitude))
                                if len(self.graph_x_vals4) > 200:
                                    self.graph_x_vals4 = np.delete(self.graph_x_vals4, (0))
                                    self.graph_y_vals4 = np.delete(self.graph_y_vals4, (0))
                                    #self.graph_x_vals4.pop(0)
                                    #self.graph_y_vals4.pop(0)

                                self.graph_counter4 = self.graph_counter4 + 1
                                prev_command4 = self.current_command4
                                self.graph_dirty4 = True
                                #wx.PostEvent(self._notify_window, GraphEvent(self.current_command4))
                                if s.value == None:
                                    wx.PostEvent(self._notify_window, GraphsValueEvent([3, 2, str(0)]))
                                    self.unit4 = "unit"
                                else:
                                    wx.PostEvent(self._notify_window, GraphsValueEvent([3, 2, str(s.value)]))
                                    try:
                                        self.unit4 = str(s.value).split(' ')[1]
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
                elif curstate == 7:  # show 8Graphs tab
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
                                    s = self.connection.connection.query(command)
                                    if s.value == None:
                                        continue
                                    else:
                                        graph_commands.append(command)
                        graph_commands.append(obd.commands.ELM_VOLTAGE)
                        sensor_descriptions = []
                        # sensor_descriptions.append("None")
                        for command in graph_commands:
                            sensor_descriptions.append(command.desc)
                        app.build_combobox_graphs8_event_finished = False
                        wx.PostEvent(self._notify_window, BuildComboBoxGraphs8Event(sensor_descriptions))
                        while not app.build_combobox_graphs8_event_finished:
                            time.sleep(0.01)
                        app.combobox_graphs8_set_sel_finished = False
                        wx.PostEvent(self._notify_window, SetSelectionComboBoxGraphs8Event([]))
                        while not app.combobox_graphs8_set_sel_finished:
                            time.sleep(0.01)
                    else: # second or more times

                        app.combobox_graphs8_get_sel_finished = False
                        wx.PostEvent(self._notify_window, GetSelectionComboBoxGraphs8Event([]))
                        while not app.combobox_graphs8_get_sel_finished:
                            time.sleep(0.01)
                        curr_selection8_1 = app.combobox8_1_selection
                        curr_selection8_2 = app.combobox8_2_selection
                        curr_selection8_3 = app.combobox8_3_selection
                        curr_selection8_4 = app.combobox8_4_selection
                        curr_selection8_5 = app.combobox8_5_selection
                        curr_selection8_6 = app.combobox8_6_selection
                        curr_selection8_7 = app.combobox8_7_selection
                        curr_selection8_8 = app.combobox8_8_selection
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
                                s = self.connection.connection.query(self.current_command8_1)
                                if s.value == None:
                                    reconnect()
                                    continue
                                # if s.value == None:
                                #    print("s.value is None!")
                                #    raise AttributeError
                                self.graph_x_vals8_1 = np.append(self.graph_x_vals8_1, self.graph_counter8_1)
                                try:
                                    self.graph_y_vals8_1 = np.append(self.graph_y_vals8_1, float(s.value.magnitude))
                                except AttributeError:
                                    self.graph_y_vals8_1 = np.append(self.graph_y_vals8_1, float(0))
                                # self.graph_x_vals1.append(self.graph_counter1)
                                # self.graph_y_vals1.append(float(s.value.magnitude))
                                if len(self.graph_x_vals8_1) > 200:
                                    self.graph_x_vals8_1 = np.delete(self.graph_x_vals8_1, (0))
                                    self.graph_y_vals8_1 = np.delete(self.graph_y_vals8_1, (0))
                                    # self.graph_x_vals1.pop(0)
                                    # self.graph_y_vals1.pop(0)

                                self.graph_counter8_1 = self.graph_counter8_1 + 1
                                prev_command8_1 = self.current_command8_1
                                self.graph_dirty8_1 = True
                                # wx.PostEvent(self._notify_window, GraphEvent(self.current_command1))
                                if s.value == None:
                                    wx.PostEvent(self._notify_window, Graphs8ValueEvent([0, 2, str(0)]))
                                    self.unit8_1 = "unit"
                                else:
                                    wx.PostEvent(self._notify_window, Graphs8ValueEvent([0, 2, str(s.value)]))
                                    try:
                                        self.unit8_1 = str(s.value).split(' ')[1]
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
                                s = self.connection.connection.query(self.current_command8_2)
                                if s.value == None:
                                    reconnect()
                                    continue
                                # if s.value == None:
                                #    print("s.value is None!")
                                #    raise AttributeError
                                self.graph_x_vals8_2 = np.append(self.graph_x_vals8_2, self.graph_counter8_2)
                                try:
                                    self.graph_y_vals8_2 = np.append(self.graph_y_vals8_2, float(s.value.magnitude))
                                except AttributeError:
                                    self.graph_y_vals8_2 = np.append(self.graph_y_vals8_2, float(0))
                                # self.graph_x_vals2.append(self.graph_counter2)
                                # self.graph_y_vals2.append(float(s.value.magnitude))
                                if len(self.graph_x_vals8_2) > 200:
                                    self.graph_x_vals8_2 = np.delete(self.graph_x_vals8_2, (0))
                                    self.graph_y_vals8_2 = np.delete(self.graph_y_vals8_2, (0))
                                    # self.graph_x_vals2.pop(0)
                                    # self.graph_y_vals2.pop(0)

                                self.graph_counter8_2 = self.graph_counter8_2 + 1
                                prev_command8_2 = self.current_command8_2
                                self.graph_dirty8_2 = True
                                # wx.PostEvent(self._notify_window, GraphEvent(self.current_command2))
                                if s.value == None:
                                    wx.PostEvent(self._notify_window, Graphs8ValueEvent([1, 2, str(0)]))
                                    self.unit8_2 = "unit"
                                else:
                                    wx.PostEvent(self._notify_window, Graphs8ValueEvent([1, 2, str(s.value)]))
                                    try:
                                        self.unit8_2 = str(s.value).split(' ')[1]
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
                                s = self.connection.connection.query(self.current_command8_3)
                                if s.value == None:
                                    reconnect()
                                    continue
                                # if s.value == None:
                                #    print("s.value is None!")
                                #    raise AttributeError
                                self.graph_x_vals8_3 = np.append(self.graph_x_vals8_3, self.graph_counter8_3)
                                try:
                                    self.graph_y_vals8_3 = np.append(self.graph_y_vals8_3, float(s.value.magnitude))
                                except AttributeError:
                                    self.graph_y_vals8_3 = np.append(self.graph_y_vals8_3, float(0))
                                # self.graph_x_vals3.append(self.graph_counter3)
                                # self.graph_y_vals3.append(float(s.value.magnitude))
                                if len(self.graph_x_vals8_3) > 200:
                                    self.graph_x_vals8_3 = np.delete(self.graph_x_vals8_3, (0))
                                    self.graph_y_vals8_3 = np.delete(self.graph_y_vals8_3, (0))
                                    # self.graph_x_vals3.pop(0)
                                    # self.graph_y_vals3.pop(0)

                                self.graph_counter8_3 = self.graph_counter8_3 + 1
                                prev_command8_3 = self.current_command8_3
                                self.graph_dirty8_3 = True
                                # wx.PostEvent(self._notify_window, GraphEvent(self.current_command3))
                                if s.value == None:
                                    wx.PostEvent(self._notify_window, Graphs8ValueEvent([2, 2, str(0)]))
                                    self.unit8_3 = "unit"
                                else:
                                    wx.PostEvent(self._notify_window, Graphs8ValueEvent([2, 2, str(s.value)]))
                                    try:
                                        self.unit8_3 = str(s.value).split(' ')[1]
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
                                s = self.connection.connection.query(self.current_command8_4)
                                if s.value == None:
                                    reconnect()
                                    continue
                                # if s.value == None:
                                #    print("s.value is None!")
                                #    raise AttributeError
                                self.graph_x_vals8_4 = np.append(self.graph_x_vals8_4, self.graph_counter8_4)

                                try:
                                    self.graph_y_vals8_4 = np.append(self.graph_y_vals8_4, float(s.value.magnitude))
                                except AttributeError:
                                    self.graph_y_vals8_4 = np.append(self.graph_y_vals8_4, float(0))

                                # self.graph_x_vals4.append(self.graph_counter4)
                                # self.graph_y_vals4.append(float(s.value.magnitude))
                                if len(self.graph_x_vals8_4) > 200:
                                    self.graph_x_vals8_4 = np.delete(self.graph_x_vals8_4, (0))
                                    self.graph_y_vals8_4 = np.delete(self.graph_y_vals8_4, (0))
                                    # self.graph_x_vals4.pop(0)
                                    # self.graph_y_vals4.pop(0)

                                self.graph_counter8_4 = self.graph_counter8_4 + 1
                                prev_command8_4 = self.current_command8_4
                                self.graph_dirty8_4 = True
                                # wx.PostEvent(self._notify_window, GraphEvent(self.current_command4))
                                if s.value == None:
                                    wx.PostEvent(self._notify_window, Graphs8ValueEvent([3, 2, str(0)]))
                                    self.unit8_4 = "unit"
                                else:
                                    wx.PostEvent(self._notify_window, Graphs8ValueEvent([3, 2, str(s.value)]))
                                    try:
                                        self.unit8_4 = str(s.value).split(' ')[1]
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
                                s = self.connection.connection.query(self.current_command8_5)
                                if s.value == None:
                                    reconnect()
                                    continue
                                # if s.value == None:
                                #    print("s.value is None!")
                                #    raise AttributeError
                                self.graph_x_vals8_5 = np.append(self.graph_x_vals8_5, self.graph_counter8_5)
                                try:
                                    self.graph_y_vals8_5 = np.append(self.graph_y_vals8_5, float(s.value.magnitude))
                                except AttributeError:
                                    self.graph_y_vals8_5 = np.append(self.graph_y_vals8_5, float(0))
                                # self.graph_x_vals1.append(self.graph_counter1)
                                # self.graph_y_vals1.append(float(s.value.magnitude))
                                if len(self.graph_x_vals8_5) > 200:
                                    self.graph_x_vals8_5 = np.delete(self.graph_x_vals8_5, (0))
                                    self.graph_y_vals8_5 = np.delete(self.graph_y_vals8_5, (0))
                                    # self.graph_x_vals1.pop(0)
                                    # self.graph_y_vals1.pop(0)

                                self.graph_counter8_5 = self.graph_counter8_5 + 1
                                prev_command8_5 = self.current_command8_5
                                self.graph_dirty8_5 = True
                                # wx.PostEvent(self._notify_window, GraphEvent(self.current_command1))
                                if s.value == None:
                                    wx.PostEvent(self._notify_window, Graphs8ValueEvent([4, 2, str(0)]))
                                    self.unit8_5 = "unit"
                                else:
                                    wx.PostEvent(self._notify_window, Graphs8ValueEvent([4, 2, str(s.value)]))
                                    try:
                                        self.unit8_5 = str(s.value).split(' ')[1]
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
                                s = self.connection.connection.query(self.current_command8_6)
                                if s.value == None:
                                    reconnect()
                                    continue
                                # if s.value == None:
                                #    print("s.value is None!")
                                #    raise AttributeError
                                self.graph_x_vals8_6 = np.append(self.graph_x_vals8_6, self.graph_counter8_6)
                                try:
                                    self.graph_y_vals8_6 = np.append(self.graph_y_vals8_6, float(s.value.magnitude))
                                except AttributeError:
                                    self.graph_y_vals8_6 = np.append(self.graph_y_vals8_6, float(0))
                                # self.graph_x_vals2.append(self.graph_counter2)
                                # self.graph_y_vals2.append(float(s.value.magnitude))
                                if len(self.graph_x_vals8_6) > 200:
                                    self.graph_x_vals8_6 = np.delete(self.graph_x_vals8_6, (0))
                                    self.graph_y_vals8_6 = np.delete(self.graph_y_vals8_6, (0))
                                    # self.graph_x_vals2.pop(0)
                                    # self.graph_y_vals2.pop(0)

                                self.graph_counter8_6 = self.graph_counter8_6 + 1
                                prev_command6 = self.current_command8_6
                                self.graph_dirty8_6 = True
                                # wx.PostEvent(self._notify_window, GraphEvent(self.current_command2))
                                if s.value == None:
                                    wx.PostEvent(self._notify_window, Graphs8ValueEvent([5, 2, str(0)]))
                                    self.unit8_6 = "unit"
                                else:
                                    wx.PostEvent(self._notify_window, Graphs8ValueEvent([5, 2, str(s.value)]))
                                    try:
                                        self.unit8_6 = str(s.value).split(' ')[1]
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
                                s = self.connection.connection.query(self.current_command8_7)
                                if s.value == None:
                                    reconnect()
                                    continue
                                # if s.value == None:
                                #    print("s.value is None!")
                                #    raise AttributeError
                                self.graph_x_vals8_7 = np.append(self.graph_x_vals8_7, self.graph_counter8_7)
                                try:
                                    self.graph_y_vals8_7 = np.append(self.graph_y_vals8_7, float(s.value.magnitude))
                                except AttributeError:
                                    self.graph_y_vals8_7 = np.append(self.graph_y_vals8_7, float(0))
                                # self.graph_x_vals3.append(self.graph_counter3)
                                # self.graph_y_vals3.append(float(s.value.magnitude))
                                if len(self.graph_x_vals8_7) > 200:
                                    self.graph_x_vals8_7 = np.delete(self.graph_x_vals8_7, (0))
                                    self.graph_y_vals8_7 = np.delete(self.graph_y_vals8_7, (0))
                                    # self.graph_x_vals3.pop(0)
                                    # self.graph_y_vals3.pop(0)

                                self.graph_counter8_7 = self.graph_counter8_7 + 1
                                prev_command8_7 = self.current_command8_7
                                self.graph_dirty8_7 = True
                                # wx.PostEvent(self._notify_window, GraphEvent(self.current_command3))
                                if s.value == None:
                                    wx.PostEvent(self._notify_window, Graphs8ValueEvent([6, 2, str(0)]))
                                    self.unit8_7 = "unit"
                                else:
                                    wx.PostEvent(self._notify_window, Graphs8ValueEvent([6, 2, str(s.value)]))
                                    try:
                                        self.unit8_7 = str(s.value).split(' ')[1]
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
                                s = self.connection.connection.query(self.current_command8_8)
                                if s.value == None:
                                    reconnect()
                                    continue
                                # if s.value == None:
                                #    print("s.value is None!")
                                #    raise AttributeError
                                self.graph_x_vals8_8 = np.append(self.graph_x_vals8_8, self.graph_counter8_8)

                                try:
                                    self.graph_y_vals8_8 = np.append(self.graph_y_vals8_8, float(s.value.magnitude))
                                except AttributeError:
                                    self.graph_y_vals8_8 = np.append(self.graph_y_vals8_8, float(0))

                                # self.graph_x_vals4.append(self.graph_counter4)
                                # self.graph_y_vals4.append(float(s.value.magnitude))
                                if len(self.graph_x_vals8_8) > 200:
                                    self.graph_x_vals8_8 = np.delete(self.graph_x_vals8_8, (0))
                                    self.graph_y_vals8_8 = np.delete(self.graph_y_vals8_8, (0))
                                    # self.graph_x_vals4.pop(0)
                                    # self.graph_y_vals4.pop(0)

                                self.graph_counter8_8 = self.graph_counter8_8 + 1
                                prev_command8_8 = self.current_command8_8
                                self.graph_dirty8_8 = True
                                # wx.PostEvent(self._notify_window, GraphEvent(self.current_command4))
                                if s.value == None:
                                    wx.PostEvent(self._notify_window, Graphs8ValueEvent([7, 2, str(0)]))
                                    self.unit8_8 = "unit"
                                else:
                                    wx.PostEvent(self._notify_window, Graphs8ValueEvent([7, 2, str(s.value)]))
                                    try:
                                        self.unit8_8 = str(s.value).split(' ')[1]
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
                    s = self.connection.connection.query(obd.commands.RPM)
                    if s.value == None:
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

    def sensor_control_on(self):  # after connection enable few buttons
        self.settingmenu.Enable(ID_CONFIG, False)
        self.settingmenu.Enable(ID_RESET, False)
        self.settingmenu.Enable(ID_DISCONNECT, True)
        self.dtcmenu.Enable(ID_GETC, True)
        self.dtcmenu.Enable(ID_CLEAR, True)
        self.GetDTCButton.Enable(True)
        self.ClearDTCButton.Enable(True)

        def sensor_toggle(e):
            sel = e.m_itemIndex
            state = self.senprod.active[sel]
            print (sel, state)
            if   state == 0:
                self.senprod.on(sel)
                self.sensors.SetItem(sel, 1, "1")
            elif state == 1:
                self.senprod.off(sel)
                self.sensors.SetItem(sel, 1, "0")
            else:
                traceback.print_exc()
                #debug("Incorrect sensor state")

        self.sensors.Bind(wx.EVT_LIST_ITEM_ACTIVATED, sensor_toggle, id=self.sensor_id)


    def sensor_control_off(self):  # after disconnect disable few buttons
        self.dtcmenu.Enable(ID_GETC, False)
        self.dtcmenu.Enable(ID_CLEAR, False)
        self.settingmenu.Enable(ID_DISCONNECT, False)
        self.settingmenu.Enable(ID_CONFIG, True)
        self.settingmenu.Enable(ID_RESET, True)
        self.GetDTCButton.Enable(False)
        self.ClearDTCButton.Enable(False)
        # http://pyserial.sourceforge.net/                                                    empty function
        # EVT_LIST_ITEM_ACTIVATED(self.sensors,self.sensor_id, lambda : None)




    def build_sensor_page(self):
        HOFFSET_LIST = 0
        tID = wx.NewIdRef(count=1)
        self.sensor_id = tID
        self.sensors = self.MyListCtrl(self.nb, tID, pos=wx.Point(0, HOFFSET_LIST), style=
                        wx.LC_REPORT |
                        wx.SUNKEN_BORDER |
                        wx.LC_HRULES |
                        wx.LC_SINGLE_SEL)
        self.sensors.InsertColumn(0, "PID", width=70)
        self.sensors.InsertColumn(1, "Sensor", format=wx.LIST_FORMAT_LEFT, width=320)
        self.sensors.InsertColumn(2, "Value", width=60)
        self.nb.AddPage(self.sensors, "Sensors")

        """
        HOFFSET_LIST = 0
        # tID = wx.NewId()
        tID = wx.NewIdRef(count=1)
        self.sensor_id = tID

        self.sensors_panel = wx.Panel(self.nb, -1)

        self.sensors = self.MyListCtrl(self.sensors_panel, tID, pos=wx.Point(0, HOFFSET_LIST),
                                     style=
                                     wx.LC_REPORT |
                                     wx.SUNKEN_BORDER |
                                     wx.LC_HRULES |
                                     wx.LC_SINGLE_SEL)

        self.sensors.InsertColumn(0, "PID", width=70)
        self.sensors.InsertColumn(1, "Sensor", format=wx.LIST_FORMAT_LEFT, width=320)
        self.sensors.InsertColumn(2, "Value")
        #self.sensors.SetSize(0, 0, 800, 1500)
        """
        """
        ####################################################################
        # This little bit of magic keeps the list the same size as the frame
        def OnPSize(e, win=panel):
            self.sensors_panel.SetSize(e.GetSize())
            self.sensors.SetSize(e.GetSize())

            w, h = self.frame.GetSize()

            self.sensors.SetSize(0, HOFFSET_LIST, w - 10, h - 35)

        self.sensors_panel.Bind(wx.EVT_SIZE, OnPSize)
        ####################################################################
        """
        """
        ####################################################################
        # This little bit of magic keeps the list the same size as the frame
        def OnPSize(e, win=self.sensors_panel):
            self.sensors_panel.SetSize(e.GetSize())
            self.sensors.SetSize(e.GetSize())
            w, h = self.frame.GetSize()
            # I have no idea where 70 comes from
            # self.dtc.SetDimensions(0,HOFFSET_LIST, w-16 , h - 70 )
            self.sensors.SetSize(0, HOFFSET_LIST, w - 16, h - 70)

        self.sensors_panel.Bind(wx.EVT_SIZE, OnPSize)
        ####################################################################


        self.nb.AddPage(self.sensors_panel, "Sensors")
        """
    def build_graph_page(self):
        HOFFSET_LIST = 0
        # tID = wx.NewId()
        tID = wx.NewIdRef(count=1)
        self.graph_id = tID
        self.graph_panel = wx.Panel(self.nb, -1)
        self.graph_list_ctrl = self.MyListCtrl(self.graph_panel, tID, pos=wx.Point(0, HOFFSET_LIST),
                                     style=
                                     wx.LC_REPORT |
                                     wx.SUNKEN_BORDER |
                                     wx.LC_HRULES |
                                     wx.LC_SINGLE_SEL)

        self.graph_list_ctrl.InsertColumn(0, "PID", width=70)
        self.graph_list_ctrl.InsertColumn(1, "Sensor", format=wx.LIST_FORMAT_LEFT, width=320)
        self.graph_list_ctrl.InsertColumn(2, "Value")

        self.graph_list_ctrl.InsertItem(0, "")
        self.nb.AddPage(self.graph_panel, "Graph")
        self.graph_list_ctrl.SetSize(0, 0, 800, 48)
        """
        ####################################################################
        # This little bit of magic keeps the list the same size as the frame
        def OnPSize(e, win=self.graph_panel):
            self.graph_panel.SetSize(e.GetSize())
            self.graph_list_ctrl.SetSize(e.GetSize())

            w, h = self.frame.GetSize()

            self.graph_list_ctrl.SetSize(0, HOFFSET_LIST, w - 10, h - 35)

        self.graph_panel.Bind(wx.EVT_SIZE, OnPSize)
        ####################################################################
        """
    def build_graphs_page(self):
        HOFFSET_LIST = 0
        # tID = wx.NewId()
        tID = wx.NewIdRef(count=1)
        self.graphs_id = tID
        self.graphs_panel = wx.Panel(self.nb, -1)
        self.graphs_list_ctrl = self.MyListCtrl(self.graphs_panel, tID, pos=wx.Point(0, HOFFSET_LIST),
                                     style=
                                     wx.LC_REPORT |
                                     wx.SUNKEN_BORDER |
                                     wx.LC_HRULES |
                                     wx.LC_SINGLE_SEL)

        self.graphs_list_ctrl.InsertColumn(0, "PID", width=70)
        self.graphs_list_ctrl.InsertColumn(1, "Sensor", format=wx.LIST_FORMAT_LEFT, width=320)
        self.graphs_list_ctrl.InsertColumn(2, "Value")

        self.graphs_list_ctrl.InsertItem(0, "")
        self.graphs_list_ctrl.InsertItem(1, "")
        self.graphs_list_ctrl.InsertItem(2, "")
        self.graphs_list_ctrl.InsertItem(3, "")
        self.nb.AddPage(self.graphs_panel, "4-Graphs")
        self.graphs_list_ctrl.SetSize(0, 0, 800, 126)
        """
        ####################################################################
        # This little bit of magic keeps the list the same size as the frame
        def OnPSize(e, win=self.graphs_panel):
            self.graphs_panel.SetSize(e.GetSize())
            self.graphs_list_ctrl.SetSize(e.GetSize())

            w, h = self.frame.GetSize()

            self.graphs_list_ctrl.SetSize(0, HOFFSET_LIST, w - 10, h - 35)

        self.graphs_panel.Bind(wx.EVT_SIZE, OnPSize)
        ####################################################################
        """

    def build_graphs8_page(self):
        HOFFSET_LIST = 0
        # tID = wx.NewId()
        tID = wx.NewIdRef(count=1)
        self.graphs8_id = tID
        self.graphs8_panel = wx.Panel(self.nb, -1)
        self.graphs8_list_ctrl = self.MyListCtrl(self.graphs8_panel, tID, pos=wx.Point(0, HOFFSET_LIST),
                                                style=
                                                wx.LC_REPORT |
                                                wx.SUNKEN_BORDER |
                                                wx.LC_HRULES |
                                                wx.LC_SINGLE_SEL)

        self.graphs8_list_ctrl.InsertColumn(0, "PID", width=70)
        self.graphs8_list_ctrl.InsertColumn(1, "Sensor", format=wx.LIST_FORMAT_LEFT, width=320)
        self.graphs8_list_ctrl.InsertColumn(2, "Value")

        self.graphs8_list_ctrl.InsertItem(0, "")
        self.graphs8_list_ctrl.InsertItem(1, "")
        self.graphs8_list_ctrl.InsertItem(2, "")
        self.graphs8_list_ctrl.InsertItem(3, "")
        self.graphs8_list_ctrl.InsertItem(4, "")
        self.graphs8_list_ctrl.InsertItem(5, "")
        self.graphs8_list_ctrl.InsertItem(6, "")
        self.graphs8_list_ctrl.InsertItem(7, "")
        self.nb.AddPage(self.graphs8_panel, "8-Graphs")
        #self.graphs8_list_ctrl.SetSize(0, 0, 800, 126)
        self.graphs8_list_ctrl.SetSize(0, 0, 800, 226)

    def build_freezeframe_page(self):
        tID = wx.NewIdRef(count=1)
        self.freezeframe_id = tID
        self.freezeframe = self.MyListCtrl(self.nb, tID, style=
                                     wx.LC_REPORT |
                                     wx.SUNKEN_BORDER |
                                     wx.LC_HRULES |
                                     wx.LC_SINGLE_SEL)
        self.freezeframe.InsertColumn(0, "PID", width=70)
        self.freezeframe.InsertColumn(1, "Sensor", format=wx.LIST_FORMAT_LEFT, width=320)
        self.freezeframe.InsertColumn(2, "Value", width=60)
        self.nb.AddPage(self.freezeframe, "Freeze frame")


        """
        """
        """
        HOFFSET_LIST = 0
        # tID = wx.NewId()
        tID = wx.NewIdRef(count=1)
        self.freezeframe_id = tID
        self.freezeframe_panel = wx.Panel(self.nb, -1)

        self.freezeframe = self.MyListCtrl(self.freezeframe_panel, tID, pos=wx.Point(0, HOFFSET_LIST),
                                       style=
                                       wx.LC_REPORT |
                                       wx.SUNKEN_BORDER |
                                       wx.LC_HRULES |
                                       wx.LC_SINGLE_SEL)

        self.freezeframe.InsertColumn(0, "PID", width=70)
        self.freezeframe.InsertColumn(1, "Sensor", format=wx.LIST_FORMAT_LEFT, width=320)
        self.freezeframe.InsertColumn(2, "Value", width=60)
        #self.freezeframe.SetSize(0, 0, 800, 1500)

        ####################################################################
        # This little bit of magic keeps the list the same size as the frame
        def OnPSize(e, win=self.freezeframe_panel):
            self.freezeframe_panel.SetSize(e.GetSize())
            self.freezeframe.SetSize(e.GetSize())

            w, h = self.frame.GetSize()

            self.freezeframe.SetSize(0, HOFFSET_LIST, w - 16, h - 70)

        self.freezeframe_panel.Bind(wx.EVT_SIZE, OnPSize)
        ####################################################################

        self.nb.AddPage(self.freezeframe_panel, "Freeze frame")
        """

    def build_DTC_page(self):
        """
        HOFFSET_LIST = 70
        tID = wx.NewIdRef(count=1)
        self.dtc = self.MyListCtrl(self.nb, tID, pos=wx.Point(0, HOFFSET_LIST), style=
        wx.LC_REPORT |
        wx.SUNKEN_BORDER |
        wx.LC_HRULES |
        wx.LC_SINGLE_SEL)
        self.dtc.InsertColumn(0, "Code", width=100)
        self.dtc.InsertColumn(1, "Status", width=100)
        self.dtc.InsertColumn(2, "Trouble code")
        self.GetDTCButton = wx.Button(self.dtc, -1, "Get DTC", wx.Point(15, 0))
        self.ClearDTCButton = wx.Button(self.dtc, -1, "Clear DTC", wx.Point(100, 0))

        # bind functions to button click action
        self.dtc.Bind(wx.EVT_BUTTON, self.GetDTC, self.GetDTCButton)
        self.dtc.Bind(wx.EVT_BUTTON, self.QueryClear, self.ClearDTCButton)
        self.nb.AddPage(self.dtc, "DTC")


        """
        
        HOFFSET_LIST = 30  # offset from the top of panel (space for buttons)
        # tID = wx.NewId()
        tID = wx.NewIdRef(count=1)
        self.DTCpanel = wx.Panel(self.nb, -1)
        self.GetDTCButton = wx.Button(self.DTCpanel, -1, "Get DTC", wx.Point(15, 0))
        self.ClearDTCButton = wx.Button(self.DTCpanel, -1, "Clear DTC", wx.Point(100, 0))

        # bind functions to button click action
        self.DTCpanel.Bind(wx.EVT_BUTTON, self.GetDTC, self.GetDTCButton)
        self.DTCpanel.Bind(wx.EVT_BUTTON, self.QueryClear, self.ClearDTCButton)

        self.dtc = self.MyListCtrl(self.DTCpanel, tID, pos=wx.Point(0, HOFFSET_LIST),
                                   style=wx.LC_REPORT | wx.SUNKEN_BORDER | wx.LC_HRULES | wx.LC_SINGLE_SEL)

        self.dtc.InsertColumn(0, "Code", width=100)
        self.dtc.InsertColumn(1, "Status", width=100)
        self.dtc.InsertColumn(2, "Trouble code")


        ####################################################################
        # This little bit of magic keeps the list the same size as the frame
        def OnPSize(e, win=self.DTCpanel):
            self.DTCpanel.SetSize(e.GetSize())
            self.dtc.SetSize(e.GetSize())
            w, h = self.frame.GetSize()
            # I have no idea where 70 comes from
            # self.dtc.SetDimensions(0,HOFFSET_LIST, w-16 , h - 70 )
            self.dtc.SetSize(0, HOFFSET_LIST, w - 16, h - 70)

        self.DTCpanel.Bind(wx.EVT_SIZE, OnPSize)
        ####################################################################

        self.nb.AddPage(self.DTCpanel, "DTC")

    def TraceDebug(self, level, msg):
        if self.DEBUGLEVEL <= level:
            self.trace.Append([str(level), msg])

    def OnInit(self):
        self.ThreadControl = 0  # say thread what to do
        self.COMPORT = 0
        self.senprod = None
        self.DEBUGLEVEL = 0  # debug everything

        # tID = wx.NewId()
        tID = wx.NewIdRef(count=1)
        self.tID = tID
        # read settings from file
        self.config = configparser.RawConfigParser()

        # print platform.system()
        # print platform.mac_ver()[]

        if "OS" in os.environ.keys():  # runnig under windows
            self.configfilepath = "pyobd.ini"
        else:
            self.configfilepath = os.environ['HOME'] + '/.pyobdrc'
        if self.config.read(self.configfilepath) == []:
            self.COMPORT = "AUTO"
            self.RECONNATTEMPTS = 5
            self.SERTIMEOUT = 1
            self.BAUDRATE = "AUTO"
            self.FAST = "FAST"
        else:
            try:
                self.COMPORT = self.config.get("pyOBD", "COMPORT")
                self.RECONNATTEMPTS = self.config.getint("pyOBD", "RECONNATTEMPTS")
                self.SERTIMEOUT = self.config.get("pyOBD", "SERTIMEOUT")
                self.BAUDRATE = self.config.get("pyOBD", "BAUDRATE")
                self.FAST = self.config.get("pyOBD", "FAST")
            except Exception as e:
                print(e)
                self.COMPORT = "AUTO"
                self.RECONNATTEMPTS = 5
                self.SERTIMEOUT = 5
                self.BAUDRATE = "AUTO"
                self.FAST = "FAST"

        self.frame = wx.Frame(None, -1, "pyOBD-II ver. 1.19")
        ico = wx.Icon(resource_path('pyobd.ico'), wx.BITMAP_TYPE_ICO)
        self.frame.SetIcon(ico)

        EVT_RESULT(self, self.OnResult, EVT_RESULT_ID)
        EVT_RESULT(self, self.OnDebug, EVT_DEBUG_ID)
        EVT_RESULT(self, self.OnDtc, EVT_DTC_ID)
        EVT_RESULT(self, self.OnStatus, EVT_STATUS_ID)
        EVT_RESULT(self, self.OnTests, EVT_TESTS_ID)
        EVT_RESULT(self, self.OnGraphValue, EVT_GRAPH_VALUE_ID)
        EVT_RESULT(self, self.OnGraphsValue, EVT_GRAPHS_VALUE_ID)
        EVT_RESULT(self, self.OnGraphs8Value, EVT_GRAPHS8_VALUE_ID)
        EVT_RESULT(self, self.OnGraph, EVT_GRAPH_ID)
        EVT_RESULT(self, self.OnGraphs, EVT_GRAPHS_ID)
        EVT_RESULT(self, self.OnGraphs8, EVT_GRAPHS8_ID)
        EVT_RESULT(self, self.OnClose, EVT_CLOSE_ID)
        EVT_RESULT(self, self.BuildComboBoxGraph, EVT_BUILD_COMBOBOXGRAPH_ID)
        EVT_RESULT(self, self.BuildComboBoxGraphs, EVT_BUILD_COMBOBOXGRAPHS_ID)
        EVT_RESULT(self, self.BuildComboBoxGraphs8, EVT_BUILD_COMBOBOXGRAPHS8_ID)
        EVT_RESULT(self, self.DestroyComboBox, EVT_DESTROY_COMBOBOX_ID)
        EVT_RESULT(self, self.GetSelectionGraphComboBox, EVT_COMBOBOXGRAPH_GETSELECTION_ID)
        EVT_RESULT(self, self.GetSelectionGraphsComboBox, EVT_COMBOBOXGRAPHS_GETSELECTION_ID)
        EVT_RESULT(self, self.GetSelectionGraphs8ComboBox, EVT_COMBOBOXGRAPHS8_GETSELECTION_ID)
        EVT_RESULT(self, self.SetSelectionGraphComboBox, EVT_COMBOBOXGRAPH_SETSELECTION_ID)
        EVT_RESULT(self, self.SetSelectionGraphsComboBox, EVT_COMBOBOXGRAPHS_SETSELECTION_ID)
        EVT_RESULT(self, self.SetSelectionGraphs8ComboBox, EVT_COMBOBOXGRAPHS8_SETSELECTION_ID)
        EVT_RESULT(self, self.InsertSensorRow, EVT_INSERT_SENSOR_ROW_ID)
        EVT_RESULT(self, self.InsertFreezeframeRow, EVT_INSERT_FREEZEFRAME_ROW_ID)
        EVT_RESULT(self, self.OnFreezeframeResult, EVT_FREEZEFRAME_RESULT_ID)

        # Main notebook frames
        self.nb = wx.Notebook(self.frame, -1, style=wx.NB_TOP)

        self.status = self.MyListCtrl(self.nb, tID, style=wx.LC_REPORT | wx.SUNKEN_BORDER)
        self.status.InsertColumn(0, "Description", width=200)
        self.status.InsertColumn(1, "Value")
        self.status.Append(["Link State", "Disconnnected"])
        self.status.Append(["Protocol", "----"])
        self.status.Append(["Cable version", "----"])
        self.status.Append(["COM port", "----"])
        self.status.Append(["VIN number", "----"])
        self.status.Append(["ELM voltage", "----"])

        self.nb.AddPage(self.status, "Status")

        self.OBDTests = self.MyListCtrl(self.nb, tID, style=wx.LC_REPORT | wx.SUNKEN_BORDER)
        self.OBDTests.InsertColumn(0, "Description", width=300)
        self.OBDTests.InsertColumn(1, "Available")
        self.OBDTests.InsertColumn(2, "Complete")
        self.nb.AddPage(self.OBDTests, "Tests")


        self.OBDTests.Append(["MISFIRE_MONITORING", "---", "---"])
        self.OBDTests.Append(["FUEL_SYSTEM_MONITORING", "---", "---"])
        self.OBDTests.Append(["COMPONENT_MONITORING", "---", "---"])
        self.OBDTests.Append(["CATALYST_MONITORING", "---", "---"])
        self.OBDTests.Append(["HEATED_CATALYST_MONITORING", "---", "---"])
        self.OBDTests.Append(["EVAPORATIVE_SYSTEM_MONITORING", "---", "---"])
        self.OBDTests.Append(["SECONDARY_AIR_SYSTEM_MONITORING", "---", "---"])
        self.OBDTests.Append(["OXYGEN_SENSOR_MONITORING", "---", "---"])
        self.OBDTests.Append(["OXYGEN_SENSOR_HEATER_MONITORING", "---", "---"])
        self.OBDTests.Append(["EGR_VVT_SYSTEM_MONITORING", "---", "---"])
        self.OBDTests.Append(["NMHC_CATALYST_MONITORING", "---", "---"])
        self.OBDTests.Append(["NOX_SCR_AFTERTREATMENT_MONITORING", "---", "---"])
        self.OBDTests.Append(["BOOST_PRESSURE_MONITORING", "---", "---"])
        self.OBDTests.Append(["EXHAUST_GAS_SENSOR_MONITORING", "---", "---"])
        self.OBDTests.Append(["PM_FILTER_MONITORING", "---", "---"])
        self.OBDTests.Append(["MISFIRE CYLINDER 1", "---", "---"])
        self.OBDTests.Append(["MISFIRE CYLINDER 2", "---", "---"])
        self.OBDTests.Append(["MISFIRE CYLINDER 3", "---", "---"])
        self.OBDTests.Append(["MISFIRE CYLINDER 4", "---", "---"])
        self.OBDTests.Append(["MISFIRE CYLINDER 5", "---", "---"])
        self.OBDTests.Append(["MISFIRE CYLINDER 6", "---", "---"])
        self.OBDTests.Append(["MISFIRE CYLINDER 7", "---", "---"])
        self.OBDTests.Append(["MISFIRE CYLINDER 8", "---", "---"])
        self.OBDTests.Append(["MISFIRE CYLINDER 9", "---", "---"])
        self.OBDTests.Append(["MISFIRE CYLINDER 10", "---", "---"])
        self.OBDTests.Append(["MISFIRE CYLINDER 11", "---", "---"])
        self.OBDTests.Append(["MISFIRE CYLINDER 12", "---", "---"])




        self.build_sensor_page()
        self.build_DTC_page()
        self.build_freezeframe_page()
        #self.trace.Destroy()


        self.build_graph_page()
        self.build_graphs_page()
        self.build_graphs8_page()
        self.trace = self.MyListCtrl(self.nb, tID, style=wx.LC_REPORT | wx.SUNKEN_BORDER)
        self.trace.InsertColumn(0, "Level", width=40)
        self.trace.InsertColumn(1, "Message")
        self.nb.AddPage(self.trace, "Trace")
        self.TraceDebug(1, "Application started")




        # Setting up the menu.
        self.filemenu = wx.Menu()
        self.filemenu.Append(ID_EXIT, "E&xit", " Terminate the program")

        self.settingmenu = wx.Menu()
        self.settingmenu.Append(ID_CONFIG, "Configure", " Configure pyOBD")
        self.settingmenu.Append(ID_RESET, "Connect", " Reopen and connect to device")
        self.settingmenu.Append(ID_DISCONNECT, "Disconnect", "Close connection to device")

        self.dtcmenu = wx.Menu()
        # tady toto nastavi automaticky tab DTC a provede akci
        self.dtcmenu.Append(ID_GETC, "Get DTCs", " Get DTC Codes")
        self.dtcmenu.Append(ID_CLEAR, "Clear DTC", " Clear DTC Codes")
        self.dtcmenu.Append(ID_LOOK, "Code Lookup", " Lookup DTC Codes")

        self.helpmenu = wx.Menu()

        self.helpmenu.Append(ID_HELP_ABOUT, "About this program", " Get DTC Codes")
        self.helpmenu.Append(ID_HELP_VISIT, "Visit program homepage", " Lookup DTC Codes")
        self.helpmenu.Append(ID_HELP_ORDER, "Order OBD-II interface", " Clear DTC Codes")

        # Creating the menubar.
        self.menuBar = wx.MenuBar()
        self.menuBar.Append(self.filemenu, "&File")  # Adding the "filemenu" to the MenuBar
        self.menuBar.Append(self.settingmenu, "&OBD-II")
        self.menuBar.Append(self.dtcmenu, "&Trouble codes")
        self.menuBar.Append(self.helpmenu, "&Help")

        self.frame.SetMenuBar(self.menuBar)  # Adding the MenuBar to the Frame content.

        self.frame.Bind(wx.EVT_MENU, self.OnExit, id=ID_EXIT)  # attach the menu-event ID_EXIT to the
        self.frame.Bind(wx.EVT_MENU, self.QueryClear, id=ID_CLEAR)
        self.frame.Bind(wx.EVT_MENU, self.Configure, id=ID_CONFIG)
        self.frame.Bind(wx.EVT_MENU, self.OpenPort, id=ID_RESET)
        self.frame.Bind(wx.EVT_MENU, self.OnDisconnect, id=ID_DISCONNECT)
        self.frame.Bind(wx.EVT_MENU, self.GetDTC, id=ID_GETC)
        self.frame.Bind(wx.EVT_MENU, self.CodeLookup, id=ID_LOOK)
        self.frame.Bind(wx.EVT_MENU, self.OnHelpAbout, id=ID_HELP_ABOUT)
        self.frame.Bind(wx.EVT_MENU, self.OnHelpVisit, id=ID_HELP_VISIT)
        self.frame.Bind(wx.EVT_MENU, self.OnHelpOrder, id=ID_HELP_ORDER)

        self.SetTopWindow(self.frame)

        self.frame.Show(True)
        self.frame.SetSize((1024, 920))
        self.sensor_control_off() # ??? JURE POLJSAK


        return True

    def OnHelpVisit(self, event):
        webbrowser.open("https://github.com/barracuda-fsh/pyobd")

    def OnHelpOrder(self, event):
        webbrowser.open("https://www.google.com/search?q=elm327+obd2+scanner")

    def OnHelpAbout(self, event):  # todo about box
        Text = """  PyOBD is an automotive OBD2 diagnosting application using ELM237 cable.

(C) 2021 Jure Poljsak
(C) 2008-2009 SeCons Ltd.
(C) 2004 Charles Donour Sizemore

https://github.com/barracuda-fsh/pyobd
http://www.obdtester.com/
http://www.secons.com/

  PyOBD is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by the Free Software Foundation; 
either version 2 of the License, or (at your option) any later version.

  PyOBD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; 
without even the implied warranty of MEHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  
See the GNU General Public License for more details. You should have received a copy of 
the GNU General Public License along with PyOBD; if not, write to 
the Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
"""

        # HelpAboutDlg = wx.Dialog(self.frame, id, title="About")

        # box  = wx.BoxSizer(wx.HORIZONTAL)
        # box.Add(wx.StaticText(reconnectPanel,-1,Text,pos=(0,0),size=(200,200)))
        # box.Add(wx.Button(HelpAboutDlg,wx.ID_OK),0)
        # box.Add(wx.Button(HelpAboutDlg,wx.ID_CANCEL),1)

        # HelpAboutDlg.SetSizer(box)
        # HelpAboutDlg.SetAutoLayout(True)
        # sizer.Fit(HelpAboutDlg)
        # HelpAboutDlg.ShowModal()

        self.HelpAboutDlg = wx.MessageDialog(self.frame, Text, 'About', wx.OK | wx.ICON_INFORMATION)
        self.HelpAboutDlg.ShowModal()
        self.HelpAboutDlg.Destroy()

    def OnResult(self, event):
        self.sensors.SetItem(event.data[0], event.data[1], event.data[2])

    def OnFreezeframeResult(self, event):
        self.freezeframe.SetItem(event.data[0], event.data[1], event.data[2])

    def OnStatus(self, event):
        if event.data[0] == 666:  # signal, that connection falied
            self.sensor_control_off()
        else:
            self.status.SetItem(event.data[0], event.data[1], event.data[2])

    def OnTests(self, event):
        self.OBDTests.SetItem(event.data[0], event.data[1], event.data[2])

    """
    def OnCombo(self, event):
        self.curr_selection1 = self.combobox1.GetSelection()
        self.curr_selection2 = self.combobox2.GetSelection()
        self.curr_selection3 = self.combobox3.GetSelection()
        self.curr_selection4 = self.combobox4.GetSelection()
    """
    def InsertSensorRow(self, event):
        counter = event.data
        self.sensors.InsertItem(counter, "")

    def InsertFreezeframeRow(self, event):
        counter = event.data
        self.freezeframe.InsertItem(counter, "")

    def BuildComboBoxGraph(self, event):
        self.combobox = wx.ComboBox(self.graph_panel, choices=event.data, pos=(0, 65))
        self.build_combobox_graph_event_finished=True

    def BuildComboBoxGraphs(self, event):
        self.combobox1 = wx.ComboBox(self.graphs_panel, choices=event.data, pos=(0, 140))
        self.combobox2 = wx.ComboBox(self.graphs_panel, choices=event.data, pos=(0, 190))
        self.combobox3 = wx.ComboBox(self.graphs_panel, choices=event.data, pos=(330, 140))
        self.combobox4 = wx.ComboBox(self.graphs_panel, choices=event.data, pos=(330, 190))
        self.build_combobox_graphs_event_finished=True

    def BuildComboBoxGraphs8(self, event):
        self.combobox8_1 = wx.ComboBox(self.graphs8_panel, choices=event.data, pos=(0, 240))
        self.combobox8_2 = wx.ComboBox(self.graphs8_panel, choices=event.data, pos=(0, 290))
        self.combobox8_3 = wx.ComboBox(self.graphs8_panel, choices=event.data, pos=(330, 240))
        self.combobox8_4 = wx.ComboBox(self.graphs8_panel, choices=event.data, pos=(330, 290))
        self.combobox8_5 = wx.ComboBox(self.graphs8_panel, choices=event.data, pos=(660, 240))
        self.combobox8_6 = wx.ComboBox(self.graphs8_panel, choices=event.data, pos=(660, 290))
        self.combobox8_7 = wx.ComboBox(self.graphs8_panel, choices=event.data, pos=(990, 240))
        self.combobox8_8 = wx.ComboBox(self.graphs8_panel, choices=event.data, pos=(990, 290))
        self.build_combobox_graphs8_event_finished=True

    def DestroyComboBox(self, event):
        try:
            self.combobox
            self.combobox.Destroy()
        except Exception as e:
            print(e)
        try:
            self.combobox1
            self.combobox1.Destroy()
            self.combobox2
            self.combobox2.Destroy()
            self.combobox3
            self.combobox3.Destroy()
            self.combobox4
            self.combobox4.Destroy()
        except Exception as e:
            print(e)
        try:
            self.combobox8_1
            self.combobox8_1.Destroy()
            self.combobox8_2
            self.combobox8_2.Destroy()
            self.combobox8_3
            self.combobox8_3.Destroy()
            self.combobox8_4
            self.combobox8_4.Destroy()
            self.combobox8_5
            self.combobox8_5.Destroy()
            self.combobox8_6
            self.combobox8_6.Destroy()
            self.combobox8_7
            self.combobox8_7.Destroy()
            self.combobox8_8
            self.combobox8_8.Destroy()

        except Exception as e:
            print(e)

    def GetSelectionGraphComboBox(self, event):
        try:
            self.combobox_selection = self.combobox.GetSelection()
            self.combobox_graph_get_sel_finished = True
        except:
            pass

    def GetSelectionGraphsComboBox(self, event):
        try:
            self.combobox1_selection = self.combobox1.GetSelection()
            self.combobox2_selection = self.combobox2.GetSelection()
            self.combobox3_selection = self.combobox3.GetSelection()
            self.combobox4_selection = self.combobox4.GetSelection()
            self.combobox_graphs_get_sel_finished = True
        except:
            pass

    def GetSelectionGraphs8ComboBox(self, event):
        try:
            self.combobox8_1_selection = self.combobox8_1.GetSelection()
            self.combobox8_2_selection = self.combobox8_2.GetSelection()
            self.combobox8_3_selection = self.combobox8_3.GetSelection()
            self.combobox8_4_selection = self.combobox8_4.GetSelection()
            self.combobox8_5_selection = self.combobox8_5.GetSelection()
            self.combobox8_6_selection = self.combobox8_6.GetSelection()
            self.combobox8_7_selection = self.combobox8_7.GetSelection()
            self.combobox8_8_selection = self.combobox8_8.GetSelection()
            self.combobox_graphs8_get_sel_finished = True
        except:
            pass

    def SetSelectionGraphComboBox(self, event):
        self.combobox_selection = self.combobox.SetSelection(0)
        self.combobox_graph_set_sel_finished = True

    def SetSelectionGraphsComboBox(self, event):
        self.combobox1_selection = self.combobox1.SetSelection(0)
        self.combobox2_selection = self.combobox2.SetSelection(1)
        self.combobox3_selection = self.combobox3.SetSelection(2)
        self.combobox4_selection = self.combobox4.SetSelection(3)
        self.combobox_graphs_set_sel_finished = True

    def SetSelectionGraphs8ComboBox(self, event):
        self.combobox8_1_selection = self.combobox8_1.SetSelection(0)
        self.combobox8_2_selection = self.combobox8_2.SetSelection(1)
        self.combobox8_3_selection = self.combobox8_3.SetSelection(2)
        self.combobox8_4_selection = self.combobox8_4.SetSelection(3)
        self.combobox8_5_selection = self.combobox8_5.SetSelection(5)
        self.combobox8_6_selection = self.combobox8_6.SetSelection(6)
        self.combobox8_7_selection = self.combobox8_7.SetSelection(7)
        self.combobox8_8_selection = self.combobox8_8.SetSelection(8)
        self.combobox_graphs8_set_sel_finished = True
    def OnClose(self, event):

        #while self.senprod.state != "finished":
        #    time.sleep(0.1)
        print("on close!")
        self.sensors.DeleteAllItems()
        self.freezeframe.DeleteAllItems()
        self.OBDTests.DeleteAllItems()
        self.OBDTests.Append(["MISFIRE_MONITORING", "---", "---"])
        self.OBDTests.Append(["FUEL_SYSTEM_MONITORING", "---", "---"])
        self.OBDTests.Append(["COMPONENT_MONITORING", "---", "---"])
        self.OBDTests.Append(["CATALYST_MONITORING", "---", "---"])
        self.OBDTests.Append(["HEATED_CATALYST_MONITORING", "---", "---"])
        self.OBDTests.Append(["EVAPORATIVE_SYSTEM_MONITORING", "---", "---"])
        self.OBDTests.Append(["SECONDARY_AIR_SYSTEM_MONITORING", "---", "---"])
        self.OBDTests.Append(["OXYGEN_SENSOR_MONITORING", "---", "---"])
        self.OBDTests.Append(["OXYGEN_SENSOR_HEATER_MONITORING", "---", "---"])
        self.OBDTests.Append(["EGR_VVT_SYSTEM_MONITORING", "---", "---"])
        self.OBDTests.Append(["NMHC_CATALYST_MONITORING", "---", "---"])
        self.OBDTests.Append(["NOX_SCR_AFTERTREATMENT_MONITORING", "---", "---"])
        self.OBDTests.Append(["BOOST_PRESSURE_MONITORING", "---", "---"])
        self.OBDTests.Append(["EXHAUST_GAS_SENSOR_MONITORING", "---", "---"])
        self.OBDTests.Append(["PM_FILTER_MONITORING", "---", "---"])
        self.OBDTests.Append(["MISFIRE CYLINDER 1", "---", "---"])
        self.OBDTests.Append(["MISFIRE CYLINDER 2", "---", "---"])
        self.OBDTests.Append(["MISFIRE CYLINDER 3", "---", "---"])
        self.OBDTests.Append(["MISFIRE CYLINDER 4", "---", "---"])
        self.OBDTests.Append(["MISFIRE CYLINDER 5", "---", "---"])
        self.OBDTests.Append(["MISFIRE CYLINDER 6", "---", "---"])
        self.OBDTests.Append(["MISFIRE CYLINDER 7", "---", "---"])
        self.OBDTests.Append(["MISFIRE CYLINDER 8", "---", "---"])
        self.OBDTests.Append(["MISFIRE CYLINDER 9", "---", "---"])
        self.OBDTests.Append(["MISFIRE CYLINDER 10", "---", "---"])
        self.OBDTests.Append(["MISFIRE CYLINDER 11", "---", "---"])
        self.OBDTests.Append(["MISFIRE CYLINDER 12", "---", "---"])
        self.dtc.DeleteAllItems()


        self.graphs_list_ctrl.DeleteAllItems()
        self.graphs_list_ctrl.InsertItem(0, "")
        self.graphs_list_ctrl.InsertItem(1, "")
        self.graphs_list_ctrl.InsertItem(2, "")
        self.graphs_list_ctrl.InsertItem(3, "")
        self.graphs8_list_ctrl.DeleteAllItems()
        self.graphs8_list_ctrl.InsertItem(0, "")
        self.graphs8_list_ctrl.InsertItem(1, "")
        self.graphs8_list_ctrl.InsertItem(2, "")
        self.graphs8_list_ctrl.InsertItem(3, "")
        self.graphs8_list_ctrl.InsertItem(4, "")
        self.graphs8_list_ctrl.InsertItem(5, "")
        self.graphs8_list_ctrl.InsertItem(6, "")
        self.graphs8_list_ctrl.InsertItem(7, "")

        try:
            self.combobox.Destroy()
        except:
            pass
        try:
            self.combobox1.Destroy()
            self.combobox2.Destroy()
            self.combobox3.Destroy()
            self.combobox4.Destroy()
        except:
            pass
        try:
            self.combobox8_1.Destroy()
            self.combobox8_2.Destroy()
            self.combobox8_3.Destroy()
            self.combobox8_4.Destroy()
            self.combobox8_5.Destroy()
            self.combobox8_6.Destroy()
            self.combobox8_7.Destroy()
            self.combobox8_8.Destroy()
        except:
            pass


        try:
            self.panel.Destroy()
        except:
            traceback.print_exc()
        try:
            self.graph_list_ctrl.DeleteAllItems()
            self.graph_list_ctrl.InsertItem(0, "")
        except:
            traceback.print_exc()
        try:
            self.panel1.Destroy()
            self.panel2.Destroy()
            self.panel3.Destroy()
            self.panel4.Destroy()

        except:
            traceback.print_exc()
        try:
            self.panel8_1.Destroy()
            self.panel8_2.Destroy()
            self.panel8_3.Destroy()
            self.panel8_4.Destroy()
            self.panel8_5.Destroy()
            self.panel8_6.Destroy()
            self.panel8_7.Destroy()
            self.panel8_8.Destroy()
        except:
            pass
        try:
            self.ThreadControl = 666

            self.sensor_control_off()
            time.sleep(0.1)

        except:
            traceback.print_exc()

    def OnGraph(self, event):
        xy_data = list(zip(event.data[0][0],event.data[0][1]))
        unit = event.data[0][2]
        command_desc = event.data[0][3]
        graph_counter = event.data[0][4]
        first_time_graph_plot = event.data[1]

        def animate():
            if not first_time_graph_plot:
                self.line = wxplot.PolySpline(xy_data, colour = 'blue', width = 1, style=wx.PENSTYLE_SOLID)
                self.graphics = wxplot.PlotGraphics([self.line], command_desc, 'frame', unit)
                if sys.platform.startswith("linux"):
                    if os.environ.get("DESKTOP_SESSION") == "gnome" or os.environ.get("DESKTOP_SESSION") == "ubuntu":
                        self.panel.Destroy()
                        self.panel = wxplot.PlotCanvas(self.graph_panel, pos=(0, 100))
                        self.panel.SetInitialSize(size=wx.Size(900, 400))
                self.panel.Draw(self.graphics, xAxis=(graph_counter - 450, graph_counter))

        if first_time_graph_plot:
            try:
                self.panel.Destroy()
            except:
                pass
            self.panel = wxplot.PlotCanvas(self.graph_panel, pos=(0, 100))
            self.panel.SetInitialSize(size=wx.Size(900, 400))
        else:
            animate()

    def OnGraphs(self, event):
        xy_data1 = list(zip(event.data[0][0],event.data[0][1]))
        unit1 = event.data[0][2]
        command_desc1 = event.data[0][3]
        graph_counter1 = event.data[0][4]
        xy_data2 = list(zip(event.data[1][0],event.data[1][1]))
        unit2 = event.data[1][2]
        command_desc2 = event.data[1][3]
        graph_counter2 = event.data[1][4]
        xy_data3 = list(zip(event.data[2][0],event.data[2][1]))
        unit3 = event.data[2][2]
        command_desc3 = event.data[2][3]
        graph_counter3 = event.data[2][4]
        xy_data4 = list(zip(event.data[3][0],event.data[3][1]))
        unit4 = event.data[3][2]
        command_desc4 = event.data[3][3]
        graph_counter4 = event.data[3][4]
        first_time_graphs_plot = event.data[4]

        def animate():
            if not first_time_graphs_plot:

                self.line1 = wxplot.PolySpline(xy_data1, colour = 'blue', width = 1, style=wx.PENSTYLE_SOLID)
                self.graphics1 = wxplot.PlotGraphics([self.line1], command_desc1, 'frame', unit1)
                if sys.platform.startswith("linux"):
                    if os.environ.get("DESKTOP_SESSION") == "gnome" or os.environ.get("DESKTOP_SESSION") == "ubuntu":
                        self.panel1.Destroy()
                        self.panel1 = wxplot.PlotCanvas(self.graphs_panel, pos=(0, 250))
                        self.panel1.SetInitialSize(size=wx.Size(400, 220))
                self.panel1.Draw(self.graphics1, xAxis=(graph_counter1 - 200, graph_counter1))

                self.line2 = wxplot.PolySpline(xy_data2, colour = 'blue', width = 1, style=wx.PENSTYLE_SOLID)
                self.graphics2 = wxplot.PlotGraphics([self.line2], command_desc2, 'frame', unit2)
                if sys.platform.startswith("linux"):
                    if os.environ.get("DESKTOP_SESSION") == "gnome" or os.environ.get("DESKTOP_SESSION") == "ubuntu":
                        self.panel2.Destroy()
                        self.panel2 = wxplot.PlotCanvas(self.graphs_panel, pos=(0, 480))
                        self.panel2.SetInitialSize(size=wx.Size(400, 220))
                self.panel2.Draw(self.graphics2, xAxis=(graph_counter2 -200, graph_counter2))

                self.line3 = wxplot.PolySpline(xy_data3, colour = 'blue', width = 1, style=wx.PENSTYLE_SOLID)
                self.graphics3 = wxplot.PlotGraphics([self.line3], command_desc3, 'frame', unit3)
                if sys.platform.startswith("linux"):
                    if os.environ.get("DESKTOP_SESSION") == "gnome" or os.environ.get("DESKTOP_SESSION") == "ubuntu":
                        self.panel3.Destroy()
                        self.panel3 = wxplot.PlotCanvas(self.graphs_panel, pos=(410, 250))
                        self.panel3.SetInitialSize(size=wx.Size(400, 220))
                self.panel3.Draw(self.graphics3, xAxis=(graph_counter3 - 200, graph_counter3))

                self.line4 = wxplot.PolySpline(xy_data4, colour = 'blue', width = 1, style=wx.PENSTYLE_SOLID)
                self.graphics4 = wxplot.PlotGraphics([self.line4], command_desc4, 'frame', unit4)
                if sys.platform.startswith("linux"):
                    if os.environ.get("DESKTOP_SESSION") == "gnome" or os.environ.get("DESKTOP_SESSION") == "ubuntu":
                        self.panel4.Destroy()
                        self.panel4 = wxplot.PlotCanvas(self.graphs_panel, pos=(410, 480))
                        self.panel4.SetInitialSize(size=wx.Size(400, 220))
                self.panel4.Draw(self.graphics4, xAxis=(graph_counter4 - 200, graph_counter4))


        if first_time_graphs_plot:
            try:
                self.panel1.Destroy()
            except:
                pass
            try:
                self.panel2.Destroy()
            except:
                pass
            try:
                self.panel3.Destroy()
            except:
                pass
            try:
                self.panel4.Destroy()
            except:
                pass
            self.panel1 = wxplot.PlotCanvas(self.graphs_panel, pos=(0, 250))
            self.panel1.SetInitialSize(size=wx.Size(400, 220))

            self.panel2 = wxplot.PlotCanvas(self.graphs_panel, pos=(0, 480))
            self.panel2.SetInitialSize(size=wx.Size(400, 220))

            self.panel3 = wxplot.PlotCanvas(self.graphs_panel, pos=(410, 250))
            self.panel3.SetInitialSize(size=wx.Size(400, 220))

            self.panel4 = wxplot.PlotCanvas(self.graphs_panel, pos=(410, 480))
            self.panel4.SetInitialSize(size=wx.Size(400, 220))

        else:
            animate()

    def OnGraphs8(self, event):
        xy_data8_1 = list(zip(event.data[0][0],event.data[0][1]))
        unit8_1 = event.data[0][2]
        command_desc8_1 = event.data[0][3]
        graph_counter8_1 = event.data[0][4]
        xy_data8_2 = list(zip(event.data[1][0],event.data[1][1]))
        unit8_2 = event.data[1][2]
        command_desc8_2 = event.data[1][3]
        graph_counter8_2 = event.data[1][4]
        xy_data8_3 = list(zip(event.data[2][0],event.data[2][1]))
        unit8_3 = event.data[2][2]
        command_desc8_3 = event.data[2][3]
        graph_counter8_3 = event.data[2][4]
        xy_data8_4 = list(zip(event.data[3][0],event.data[3][1]))
        unit8_4 = event.data[3][2]
        command_desc8_4 = event.data[3][3]
        graph_counter8_4 = event.data[3][4]
        xy_data8_5 = list(zip(event.data[4][0], event.data[4][1]))
        unit8_5 = event.data[4][2]
        command_desc8_5 = event.data[4][3]
        graph_counter8_5 = event.data[4][4]
        xy_data8_6 = list(zip(event.data[5][0], event.data[5][1]))
        unit8_6 = event.data[5][2]
        command_desc8_6 = event.data[5][3]
        graph_counter8_6 = event.data[5][4]
        xy_data8_7 = list(zip(event.data[6][0], event.data[6][1]))
        unit8_7 = event.data[6][2]
        command_desc8_7 = event.data[6][3]
        graph_counter8_7 = event.data[6][4]
        xy_data8_8 = list(zip(event.data[7][0], event.data[7][1]))
        unit8_8 = event.data[7][2]
        command_desc8_8 = event.data[7][3]
        graph_counter8_8 = event.data[7][4]
        first_time_graphs8_plot = event.data[8]


        def animate():
            if not first_time_graphs8_plot:

                self.line8_1 = wxplot.PolySpline(xy_data8_1, colour = 'blue', width = 1, style=wx.PENSTYLE_SOLID)
                self.graphics8_1 = wxplot.PlotGraphics([self.line8_1], command_desc8_1, 'frame', unit8_1)
                if sys.platform.startswith("linux"):
                    if os.environ.get("DESKTOP_SESSION") == "gnome" or os.environ.get("DESKTOP_SESSION") == "ubuntu":
                        self.panel8_1.Destroy()
                        self.panel8_1 = wxplot.PlotCanvas(self.graphs8_panel, pos=(0, 350))
                        self.panel8_1.SetInitialSize(size=wx.Size(400, 220))
                self.panel8_1.Draw(self.graphics8_1, xAxis=(graph_counter8_1 - 200, graph_counter8_1))

                self.line8_2 = wxplot.PolySpline(xy_data8_2, colour = 'blue', width = 1, style=wx.PENSTYLE_SOLID)
                self.graphics8_2 = wxplot.PlotGraphics([self.line8_2], command_desc8_2, 'frame', unit8_2)
                if sys.platform.startswith("linux"):
                    if os.environ.get("DESKTOP_SESSION") == "gnome" or os.environ.get("DESKTOP_SESSION") == "ubuntu":
                        self.panel8_2.Destroy()
                        self.panel8_2 = wxplot.PlotCanvas(self.graphs8_panel, pos=(0, 580))
                        self.panel8_2.SetInitialSize(size=wx.Size(400, 220))
                self.panel8_2.Draw(self.graphics8_2, xAxis=(graph_counter8_2 -200, graph_counter8_2))

                self.line8_3 = wxplot.PolySpline(xy_data8_3, colour = 'blue', width = 1, style=wx.PENSTYLE_SOLID)
                self.graphics8_3 = wxplot.PlotGraphics([self.line8_3], command_desc8_3, 'frame', unit8_3)
                if sys.platform.startswith("linux"):
                    if os.environ.get("DESKTOP_SESSION") == "gnome" or os.environ.get("DESKTOP_SESSION") == "ubuntu":
                        self.panel8_3.Destroy()
                        self.panel8_3 = wxplot.PlotCanvas(self.graphs8_panel, pos=(410, 350))
                        self.panel8_3.SetInitialSize(size=wx.Size(400, 220))
                self.panel8_3.Draw(self.graphics8_3, xAxis=(graph_counter8_3 - 200, graph_counter8_3))

                self.line8_4 = wxplot.PolySpline(xy_data8_4, colour = 'blue', width = 1, style=wx.PENSTYLE_SOLID)
                self.graphics8_4 = wxplot.PlotGraphics([self.line8_4], command_desc8_4, 'frame', unit8_4)
                if sys.platform.startswith("linux"):
                    if os.environ.get("DESKTOP_SESSION") == "gnome" or os.environ.get("DESKTOP_SESSION") == "ubuntu":
                        self.panel8_4.Destroy()
                        self.panel8_4 = wxplot.PlotCanvas(self.graphs8_panel, pos=(410, 580))
                        self.panel8_4.SetInitialSize(size=wx.Size(400, 220))
                self.panel8_4.Draw(self.graphics8_4, xAxis=(graph_counter8_4 - 200, graph_counter8_4))

                self.line8_5 = wxplot.PolySpline(xy_data8_5, colour='blue', width=1, style=wx.PENSTYLE_SOLID)
                self.graphics8_5 = wxplot.PlotGraphics([self.line8_5], command_desc8_5, 'frame', unit8_5)
                if sys.platform.startswith("linux"):
                    if os.environ.get("DESKTOP_SESSION") == "gnome" or os.environ.get("DESKTOP_SESSION") == "ubuntu":
                        self.panel8_5.Destroy()
                        self.panel8_5 = wxplot.PlotCanvas(self.graphs8_panel, pos=(820, 350))
                        self.panel8_5.SetInitialSize(size=wx.Size(400, 220))
                self.panel8_5.Draw(self.graphics8_5, xAxis=(graph_counter8_5 - 200, graph_counter8_5))

                self.line8_6 = wxplot.PolySpline(xy_data8_6, colour='blue', width=1, style=wx.PENSTYLE_SOLID)
                self.graphics8_6 = wxplot.PlotGraphics([self.line8_6], command_desc8_6, 'frame', unit8_6)
                if sys.platform.startswith("linux"):
                    if os.environ.get("DESKTOP_SESSION") == "gnome" or os.environ.get("DESKTOP_SESSION") == "ubuntu":
                        self.panel8_6.Destroy()
                        self.panel8_6 = wxplot.PlotCanvas(self.graphs8_panel, pos=(820, 580))
                        self.panel8_6.SetInitialSize(size=wx.Size(400, 220))
                self.panel8_6.Draw(self.graphics8_6, xAxis=(graph_counter8_6 - 200, graph_counter8_6))

                self.line8_7 = wxplot.PolySpline(xy_data8_7, colour='blue', width=1, style=wx.PENSTYLE_SOLID)
                self.graphics8_7 = wxplot.PlotGraphics([self.line8_7], command_desc8_7, 'frame', unit8_7)
                if sys.platform.startswith("linux"):
                    if os.environ.get("DESKTOP_SESSION") == "gnome" or os.environ.get("DESKTOP_SESSION") == "ubuntu":
                        self.panel8_7.Destroy()
                        self.panel8_7 = wxplot.PlotCanvas(self.graphs8_panel, pos=(1240, 350))
                        self.panel8_7.SetInitialSize(size=wx.Size(400, 220))
                self.panel8_7.Draw(self.graphics8_7, xAxis=(graph_counter8_7 - 200, graph_counter8_7))

                self.line8_8 = wxplot.PolySpline(xy_data8_8, colour='blue', width=1, style=wx.PENSTYLE_SOLID)
                self.graphics8_8 = wxplot.PlotGraphics([self.line8_8], command_desc8_8, 'frame', unit8_8)
                if sys.platform.startswith("linux"):
                    if os.environ.get("DESKTOP_SESSION") == "gnome" or os.environ.get("DESKTOP_SESSION") == "ubuntu":
                        self.panel8_8.Destroy()
                        self.panel8_8 = wxplot.PlotCanvas(self.graphs8_panel, pos=(1240, 580))
                        self.panel8_8.SetInitialSize(size=wx.Size(400, 220))
                self.panel8_8.Draw(self.graphics8_8, xAxis=(graph_counter8_8 - 200, graph_counter8_8))


        if first_time_graphs8_plot:
            try:
                self.panel8_1.Destroy()
            except:
                pass
            try:
                self.panel8_2.Destroy()
            except:
                pass
            try:
                self.panel8_3.Destroy()
            except:
                pass
            try:
                self.panel8_4.Destroy()
            except:
                pass
            try:
                self.panel8_5.Destroy()
            except:
                pass
            try:
                self.panel8_6.Destroy()
            except:
                pass
            try:
                self.panel8_7.Destroy()
            except:
                pass
            try:
                self.panel8_8.Destroy()
            except:
                pass
            self.panel8_1 = wxplot.PlotCanvas(self.graphs8_panel, pos=(0, 350))
            self.panel8_1.SetInitialSize(size=wx.Size(400, 220))

            self.panel8_2 = wxplot.PlotCanvas(self.graphs8_panel, pos=(0, 580))
            self.panel8_2.SetInitialSize(size=wx.Size(400, 220))

            self.panel8_3 = wxplot.PlotCanvas(self.graphs8_panel, pos=(410, 350))
            self.panel8_3.SetInitialSize(size=wx.Size(400, 220))

            self.panel8_4 = wxplot.PlotCanvas(self.graphs8_panel, pos=(410, 580))
            self.panel8_4.SetInitialSize(size=wx.Size(400, 220))

            self.panel8_5 = wxplot.PlotCanvas(self.graphs8_panel, pos=(820, 350))
            self.panel8_5.SetInitialSize(size=wx.Size(400, 220))

            self.panel8_6 = wxplot.PlotCanvas(self.graphs8_panel, pos=(820, 580))
            self.panel8_6.SetInitialSize(size=wx.Size(400, 220))

            self.panel8_7 = wxplot.PlotCanvas(self.graphs8_panel, pos=(1240, 350))
            self.panel8_7.SetInitialSize(size=wx.Size(400, 220))

            self.panel8_8 = wxplot.PlotCanvas(self.graphs8_panel, pos=(1240, 580))
            self.panel8_8.SetInitialSize(size=wx.Size(400, 220))

        else:
            animate()

    def OnGraphValue(self, event):
        self.graph_list_ctrl.SetItem(event.data[0], event.data[1], event.data[2])

    def OnGraphsValue(self, event):
        self.graphs_list_ctrl.SetItem(event.data[0], event.data[1], event.data[2])

    def OnGraphs8Value(self, event):
        self.graphs8_list_ctrl.SetItem(event.data[0], event.data[1], event.data[2])

    def OnDebug(self, event):
        self.TraceDebug(event.data[0], event.data[1])

    def OnDtc(self, event):
        if event.data == 0:  # signal, that DTC was cleared
            self.dtc.DeleteAllItems()
        else:
            self.dtc.Append(event.data)

    def OnDisconnect(self, event):  # disconnect connection to ECU
        try:
            self.ThreadControl = 666
            time.sleep(0.1)

        except:
            traceback.print_exc()




    def OpenPort(self, e):
        print("Open port event.")
        if self.senprod:
            if self.senprod.is_alive():  # signal current producers to finish
                self.senprod.stop()
        self.ThreadControl = 0

        self.senprod = self.sensorProducer(self, self.COMPORT, self.SERTIMEOUT, self.RECONNATTEMPTS, self.BAUDRATE, self.FAST, self.nb)
        self.senprod.start()

        self.sensor_control_on()

    def GetDTC(self, e):
        self.nb.SetSelection(3)
        self.ThreadControl = 2

    def AddDTC(self, code):
        self.dtc.InsertStringItem(0, "")
        self.dtc.SetItem(0, 0, code[0])
        self.dtc.SetItem(0, 1, code[1])

    def CodeLookup(self, e=None):
        id = 0
        diag = wx.Frame(None, id, title="Diagnostic Trouble Codes")
        ico = wx.Icon(resource_path('pyobd.ico'), wx.BITMAP_TYPE_ICO)
        diag.SetIcon(ico)
        tree = wx.TreeCtrl(diag, id, style=wx.TR_HAS_BUTTONS)

        root = tree.AddRoot("Code Reference")
        proot = root;  # tree.AppendItem(root,"Powertrain (P) Codes")
        codes = pcodes.keys()
        codes = sorted(codes)
        group = ""
        for c in codes:
            if c[:3] != group:
                group_root = tree.AppendItem(proot, c[:3] + "XX")
                group = c[:3]
            leaf = tree.AppendItem(group_root, c)
            tree.AppendItem(leaf, pcodes[c])

        diag.SetSize((400, 500))
        diag.Show(True)

    def QueryClear(self, e):
        id = 0
        diag = wx.Dialog(self.frame, id, title="Clear DTC?")

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(wx.StaticText(diag, -1, "Are you sure you wish to"), 0)
        sizer.Add(wx.StaticText(diag, -1, "clear all DTC codes and "), 0)
        sizer.Add(wx.StaticText(diag, -1, "freeze frame data?      "), 0)
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(wx.Button(diag, wx.ID_OK, "Ok"), 0)
        box.Add(wx.Button(diag, wx.ID_CANCEL, "Cancel"), 0)

        sizer.Add(box, 0)
        diag.SetSizer(sizer)
        diag.SetAutoLayout(True)
        sizer.Fit(diag)
        r = diag.ShowModal()
        if r == wx.ID_OK:
            self.ClearDTC()

    def ClearDTC(self):
        self.ThreadControl = 1
        self.nb.SetSelection(3)

    def try_port(self, portStr):
        """returns boolean for port availability"""
        try:
            s = serial.Serial(portStr)
            s.close()  # explicit close 'cause of delayed GC in java
            return True

        except serial.SerialException:
            pass
        except:
            traceback.print_exc()

        return False

    def scanSerial(self):  # NEW

        """scan for available ports. return a list of serial names"""
        available = []
        available = obd.scan_serial()

        return available

    def Configure(self, e=None):
        id = 0
        diag = wx.Dialog(self.frame, id, title="Configure")
        sizer = wx.BoxSizer(wx.VERTICAL)

        ports = obd.scan_serial()
        if ports == []:
            ports = ["AUTO"]
        else:
            ports.append("AUTO")

        # web open link button
        self.OpenLinkButton = wx.Button(diag, -1, "Click here to order ELM-USB interface", size=(260, 30))
        diag.Bind(wx.EVT_BUTTON, self.OnHelpOrder, self.OpenLinkButton)
        sizer.Add(self.OpenLinkButton)
        rb = wx.RadioBox(diag, id, "Choose Serial Port",
                         choices=ports, style=wx.RA_SPECIFY_COLS,
                         majorDimension=2)

        sizer.Add(rb, 0)
        baudrates = ['AUTO', "38400", "9600",  "115200", "57600", "19200", "14400", "3000000", "2000000", "1000000", "250000", "230400", "128000", "500000", "460800", "500000", "576000", "921600", "1000000", "1152000", "1500000", "2000000", "2500000", "3000000", "3500000", "4000000"]
        brb = wx.RadioBox(diag, id, "Choose Baud Rate",
                         choices=baudrates, style=wx.RA_SPECIFY_COLS,
                         majorDimension=2)

        sizer.Add(brb, 0)
        fb = wx.RadioBox(diag, id, "FAST or NORMAL:",
                         choices=["FAST","NORMAL"], style=wx.RA_SPECIFY_COLS,
                         majorDimension=2)

        sizer.Add(fb, 0)
        # timeOut input control
        timeoutPanel = wx.Panel(diag, -1)
        timeoutCtrl = wx.TextCtrl(timeoutPanel, -1, '', pos=(140, 0), size=(40, 25))
        timeoutStatic = wx.StaticText(timeoutPanel, -1, 'Timeout:', pos=(3, 5), size=(140, 20))
        timeoutCtrl.SetValue(str(self.SERTIMEOUT))

        # reconnect attempt input control
        reconnectPanel = wx.Panel(diag, -1)
        reconnectCtrl = wx.TextCtrl(reconnectPanel, -1, '', pos=(140, 0), size=(40, 25))
        reconnectStatic = wx.StaticText(reconnectPanel, -1, 'Reconnect attempts:', pos=(3, 5), size=(140, 20))
        reconnectCtrl.SetValue(str(self.RECONNATTEMPTS))



        # set actual serial port choice
        if (self.COMPORT != 0) and (self.COMPORT in ports):
            rb.SetSelection(ports.index(self.COMPORT))
        baudrates = ['AUTO', "38400", "9600",  "115200", "57600", "19200", "14400", "3000000", "2000000", "1000000", "250000", "230400", "128000", "500000", "460800", "500000", "576000", "921600", "1000000", "1152000", "1500000", "2000000", "2500000", "3000000", "3500000", "4000000"]
        if (self.BAUDRATE != 0) and (self.BAUDRATE in baudrates):
            brb.SetSelection(baudrates.index(self.BAUDRATE))
        if (self.FAST == "FAST") or (self.FAST == "NORMAL"):
            fb.SetSelection(["FAST","NORMAL"].index(self.FAST))


        sizer.Add(timeoutPanel, 0)
        sizer.Add(reconnectPanel, 0)

        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(wx.Button(diag, wx.ID_OK), 0)
        box.Add(wx.Button(diag, wx.ID_CANCEL), 1)

        sizer.Add(box, 0)
        diag.SetSizer(sizer)
        diag.SetAutoLayout(True)
        sizer.Fit(diag)
        r = diag.ShowModal()
        if r == wx.ID_OK:

            # create section
            if self.config.sections() == []:
                self.config.add_section("pyOBD")
            # set and save COMPORT

            self.COMPORT = ports[rb.GetSelection()]
            COMPORT = self.COMPORT
            self.config.set("pyOBD", "COMPORT", self.COMPORT)

            self.BAUDRATE = baudrates[brb.GetSelection()]
            BAUDRATE = self.BAUDRATE
            self.config.set("pyOBD", "BAUDRATE", self.BAUDRATE)

            self.FAST = ["FAST","NORMAL"][fb.GetSelection()]
            self.config.set("pyOBD", "FAST", self.FAST)

            # set and save SERTIMEOUT
            self.SERTIMEOUT = timeoutCtrl.GetValue()
            self.config.set("pyOBD", "SERTIMEOUT", self.SERTIMEOUT)


            # set and save RECONNATTEMPTS
            self.RECONNATTEMPTS = int(reconnectCtrl.GetValue())
            self.config.set("pyOBD", "RECONNATTEMPTS", self.RECONNATTEMPTS)

            # write configuration to cfg file
            self.config.write(open(self.configfilepath, 'w'))

    def OnExit(self, e=None):
        self.ThreadControl = 666
        time.sleep(0.1)
        os._exit(0)


app = MyApp(0)
app.MainLoop()
