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
from typing import Callable, override

from wx.lib import plot as wxplot

import traceback
import wx
import os  # os.environ
import threading
import sys
import serial
import time
import configparser  # safe application configuration
import webbrowser  # open browser from python

from pyobd.gui import about_text
from pyobd.gui.custom_widgets import CustomListCtrl
from pyobd.gui.gui_events import (
    GUIEvent,
    ID_DISCONNECT,
    ID_CONFIG,
    ID_RESET,
    ID_GETC,
    ID_CLEAR,
    ID_EXIT,
    ID_LOOK,
    ID_HELP_ABOUT,
    ID_HELP_VISIT,
    ID_HELP_ORDER,
)
from pyobd.gui.sensor_producer import SensorProducer
from pyobd.gui.utils import resource_path
from pyobd.obd2_codes import pcodes

from pyobd import obd

# import pint
# from mem_top import mem_top
# import logging
# import multiprocessing
# from multiprocessing import Queue, Process
# import wxversion
# wxversion.select("2.6")
# import matplotlib
# from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
# from matplotlib.figure import Figure
# import matplotlib.pyplot as plt
# matplotlib.use('wxAgg')
# from matplotlib.animation import FuncAnimation
# from matplotlib import style
# import numpy.oldnumeric as _Numeric
# from wxplot import PlotCanvas, PlotGraphics, PolyLine, PolyMarker, PolySpline
# from pympler.tracker import SummaryTracker
# tracker = SummaryTracker()
# import pdb
# import decimal
# import glob
# import platform
# from multiprocessing import Queue
# from multiprocessing import Process
# from obd2_codes import ptest
# from obd import OBDStatus


lock = threading.Lock()


class PyOBDApp(wx.App):
    # A listctrl which auto-resizes the column boxes to fill

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
            print(sel, state)
            if state == 0:
                self.senprod.on(sel)
                self.sensors.SetItem(sel, 1, "1")
            elif state == 1:
                self.senprod.off(sel)
                self.sensors.SetItem(sel, 1, "0")
            else:
                traceback.print_exc()
                # debug("Incorrect sensor state")

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
        # tID = wx.NewId()
        tID = wx.NewIdRef(count=1)
        self.sensor_id = tID

        self.sensors_panel = wx.Panel(self.nb, -1)
        self.sensors = CustomListCtrl(
            self.sensors_panel,
            tID,
            pos=wx.Point(0, HOFFSET_LIST),
            style=wx.LC_REPORT | wx.SUNKEN_BORDER | wx.LC_HRULES | wx.LC_SINGLE_SEL,
        )

        self.sensors.InsertColumn(0, "PID", width=70)
        self.sensors.InsertColumn(1, "Sensor", format=wx.LIST_FORMAT_LEFT, width=320)
        self.sensors.InsertColumn(2, "Value")
        self.sensors.SetSize(0, 0, 800, 1500)

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
        self.nb.AddPage(self.sensors_panel, "Sensors")

    def build_graph_page(self):
        HOFFSET_LIST = 0
        # tID = wx.NewId()
        tID = wx.NewIdRef(count=1)
        self.graph_id = tID
        self.graph_panel = wx.Panel(self.nb, -1)
        self.graph_list_ctrl = CustomListCtrl(
            self.graph_panel,
            tID,
            pos=wx.Point(0, HOFFSET_LIST),
            style=wx.LC_REPORT | wx.SUNKEN_BORDER | wx.LC_HRULES | wx.LC_SINGLE_SEL,
        )

        self.graph_list_ctrl.InsertColumn(0, "PID", width=70)
        self.graph_list_ctrl.InsertColumn(
            1, "Sensor", format=wx.LIST_FORMAT_LEFT, width=320
        )
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
        self.graphs_list_ctrl = CustomListCtrl(
            self.graphs_panel,
            tID,
            pos=wx.Point(0, HOFFSET_LIST),
            style=wx.LC_REPORT | wx.SUNKEN_BORDER | wx.LC_HRULES | wx.LC_SINGLE_SEL,
        )

        self.graphs_list_ctrl.InsertColumn(0, "PID", width=70)
        self.graphs_list_ctrl.InsertColumn(
            1, "Sensor", format=wx.LIST_FORMAT_LEFT, width=320
        )
        self.graphs_list_ctrl.InsertColumn(2, "Value")

        self.graphs_list_ctrl.InsertItem(0, "")
        self.graphs_list_ctrl.InsertItem(1, "")
        self.graphs_list_ctrl.InsertItem(2, "")
        self.graphs_list_ctrl.InsertItem(3, "")
        self.nb.AddPage(self.graphs_panel, "Graphs")
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

    def build_freezeframe_page(self):
        HOFFSET_LIST = 0
        # tID = wx.NewId()
        tID = wx.NewIdRef(count=1)
        self.freezeframe_id = tID
        self.freezeframe_panel = wx.Panel(self.nb, -1)

        self.freezeframe = CustomListCtrl(
            self.freezeframe_panel,
            tID,
            pos=wx.Point(0, HOFFSET_LIST),
            style=wx.LC_REPORT | wx.SUNKEN_BORDER | wx.LC_HRULES | wx.LC_SINGLE_SEL,
        )

        self.freezeframe.InsertColumn(0, "PID", width=70)
        self.freezeframe.InsertColumn(
            1, "Sensor", format=wx.LIST_FORMAT_LEFT, width=320
        )
        self.freezeframe.InsertColumn(2, "Value")
        self.freezeframe.SetSize(0, 0, 800, 1500)
        """
        ####################################################################
        # This little bit of magic keeps the list the same size as the frame
        def OnPSize(e, win=panel):
            self.freezeframe_panel.SetSize(e.GetSize())
            self.freezeframe.SetSize(e.GetSize())

            w, h = self.frame.GetSize()

            self.freezeframe.SetSize(0, HOFFSET_LIST, w - 10, h - 35)

        self.freezeframe_panel.Bind(wx.EVT_SIZE, OnPSize)
        ####################################################################
        """
        self.nb.AddPage(self.freezeframe_panel, "Freeze frame")

    def build_dtc_page(self):
        HOFFSET_LIST = 30  # offset from the top of panel (space for buttons)
        # tID = wx.NewId()
        tID = wx.NewIdRef(count=1)
        self.DTCpanel = wx.Panel(self.nb, -1)
        self.GetDTCButton = wx.Button(self.DTCpanel, -1, "Get DTC", wx.Point(15, 0))
        self.ClearDTCButton = wx.Button(
            self.DTCpanel, -1, "Clear DTC", wx.Point(100, 0)
        )

        # bind functions to button click action
        self.DTCpanel.Bind(wx.EVT_BUTTON, self.get_dtc, self.GetDTCButton)
        self.DTCpanel.Bind(wx.EVT_BUTTON, self.query_clear, self.ClearDTCButton)

        self.dtc = CustomListCtrl(
            self.DTCpanel,
            tID,
            pos=wx.Point(0, HOFFSET_LIST),
            style=wx.LC_REPORT | wx.SUNKEN_BORDER | wx.LC_HRULES | wx.LC_SINGLE_SEL,
        )

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

    def trace_debug(self, level, msg):
        if self.DEBUGLEVEL <= level:
            self.trace.Append([str(level), msg])

    def handle_event(self, event: GUIEvent, func: Callable):
        """Define Result Event."""
        self.Connect(-1, -1, event, func)

    @override
    def OnInit(self):
        self.ThreadControl = 0  # say thread what to do
        self.COMPORT = 0
        self.senprod = None
        self.DEBUGLEVEL = 0  # debug everything

        # tID = wx.NewId()
        tID = wx.NewIdRef(count=1)
        # read settings from file
        self.config = configparser.RawConfigParser()

        # print platform.system()
        # print platform.mac_ver()[]

        if "OS" in os.environ.keys():  # runnig under windows
            self.configfilepath = "pyobd.ini"
        else:
            self.configfilepath = os.environ["HOME"] + "/.pyobdrc"
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

        self.frame = wx.Frame(None, -1, "pyOBD-II ver. 1.17-2")
        ico = wx.Icon(str(resource_path("assets/pyobd.ico")), wx.BITMAP_TYPE_ICO)
        self.frame.SetIcon(ico)

        self.handle_event(GUIEvent.RESULT, self.on_result)
        self.handle_event(GUIEvent.DEBUG, self.on_debug)
        self.handle_event(GUIEvent.DTC, self.on_dtc)
        self.handle_event(GUIEvent.STATUS, self.on_status)
        self.handle_event(GUIEvent.TESTS, self.on_tests)
        self.handle_event(GUIEvent.GRAPH_VALUE, self.on_graph_value)
        self.handle_event(GUIEvent.GRAPHS_VALUE, self.on_graphs_value)
        self.handle_event(GUIEvent.GRAPH, self.on_graph)
        self.handle_event(GUIEvent.GRAPHS, self.on_graphs)
        self.handle_event(GUIEvent.CLOSE, self.on_close)
        self.handle_event(GUIEvent.BUILD_COMBOBOXGRAPH, self.build_combo_box_graph)
        self.handle_event(GUIEvent.BUILD_COMBOBOXGRAPHS, self.build_combo_box_graphs)
        self.handle_event(GUIEvent.DESTROY_COMBOBOX, self.destroy_combo_box)
        self.handle_event(
            GUIEvent.COMBOBOXGRAPH_GETSELECTION, self.get_selection_graph_combo_box
        )
        self.handle_event(
            GUIEvent.COMBOBOXGRAPHS_GETSELECTION, self.get_selection_graphs_combo_box
        )
        self.handle_event(
            GUIEvent.COMBOBOXGRAPH_SETSELECTION, self.set_selection_graph_combo_box
        )
        self.handle_event(
            GUIEvent.COMBOBOXGRAPHS_SETSELECTION, self.set_selection_graphs_combo_box
        )
        self.handle_event(GUIEvent.INSERT_SENSOR_ROW, self.insert_sensor_row)
        self.handle_event(GUIEvent.INSERT_FREEZEFRAME_ROW, self.insert_freezeframe_row)
        self.handle_event(GUIEvent.FREEZEFRAME_RESULT, self.on_freezeframe_result)

        # Main notebook frames
        self.nb = wx.Notebook(self.frame, -1, style=wx.NB_TOP)

        self.status = CustomListCtrl(
            self.nb, tID, style=wx.LC_REPORT | wx.SUNKEN_BORDER
        )
        self.status.InsertColumn(0, "Description", width=200)
        self.status.InsertColumn(1, "Value")
        self.status.Append(["Link State", "Disconnnected"])
        self.status.Append(["Protocol", "----"])
        self.status.Append(["Cable version", "----"])
        self.status.Append(["COM port", "----"])
        self.status.Append(["VIN number", "----"])
        self.status.Append(["ELM voltage", "----"])

        self.nb.AddPage(self.status, "Status")

        self.OBDTests = CustomListCtrl(
            self.nb, tID, style=wx.LC_REPORT | wx.SUNKEN_BORDER
        )
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
        self.build_dtc_page()
        self.build_freezeframe_page()
        self.build_graph_page()
        self.build_graphs_page()

        self.trace = CustomListCtrl(
            self.nb, tID, style=wx.LC_REPORT | wx.SUNKEN_BORDER
        )
        self.trace.InsertColumn(0, "Level", width=40)
        self.trace.InsertColumn(1, "Message")
        self.nb.AddPage(self.trace, "Trace")
        self.trace_debug(1, "Application started")

        # Setting up the menu.
        self.filemenu = wx.Menu()
        self.filemenu.Append(ID_EXIT, "E&xit", " Terminate the program")

        self.settingmenu = wx.Menu()
        self.settingmenu.Append(ID_CONFIG, "Configure", " Configure pyOBD")
        self.settingmenu.Append(ID_RESET, "Connect", " Reopen and connect to device")
        self.settingmenu.Append(
            ID_DISCONNECT, "Disconnect", "Close connection to device"
        )

        self.dtcmenu = wx.Menu()
        # tady toto nastavi automaticky tab DTC a provede akci
        self.dtcmenu.Append(ID_GETC, "Get DTCs", " Get DTC Codes")
        self.dtcmenu.Append(ID_CLEAR, "Clear DTC", " Clear DTC Codes")
        self.dtcmenu.Append(ID_LOOK, "Code Lookup", " Lookup DTC Codes")

        self.helpmenu = wx.Menu()

        self.helpmenu.Append(ID_HELP_ABOUT, "About this program", " Get DTC Codes")
        self.helpmenu.Append(
            ID_HELP_VISIT, "Visit program homepage", " Lookup DTC Codes"
        )
        self.helpmenu.Append(
            ID_HELP_ORDER, "Order OBD-II interface", " Clear DTC Codes"
        )

        # Creating the menubar.
        self.menuBar = wx.MenuBar()
        self.menuBar.Append(
            self.filemenu, "&File"
        )  # Adding the "filemenu" to the MenuBar
        self.menuBar.Append(self.settingmenu, "&OBD-II")
        self.menuBar.Append(self.dtcmenu, "&Trouble codes")
        self.menuBar.Append(self.helpmenu, "&Help")

        self.frame.SetMenuBar(self.menuBar)  # Adding the MenuBar to the Frame content.

        self.frame.Bind(
            wx.EVT_MENU, self.OnExit, id=ID_EXIT
        )  # attach the menu-event ID_EXIT to the
        self.frame.Bind(wx.EVT_MENU, self.query_clear, id=ID_CLEAR)
        self.frame.Bind(wx.EVT_MENU, self.configure, id=ID_CONFIG)
        self.frame.Bind(wx.EVT_MENU, self.open_port, id=ID_RESET)
        self.frame.Bind(wx.EVT_MENU, self.on_disconnect, id=ID_DISCONNECT)
        self.frame.Bind(wx.EVT_MENU, self.get_dtc, id=ID_GETC)
        self.frame.Bind(wx.EVT_MENU, self.code_lookup, id=ID_LOOK)
        self.frame.Bind(wx.EVT_MENU, self.on_help_about, id=ID_HELP_ABOUT)
        self.frame.Bind(wx.EVT_MENU, self.on_help_visit, id=ID_HELP_VISIT)
        self.frame.Bind(wx.EVT_MENU, self.on_help_order, id=ID_HELP_ORDER)

        self.SetTopWindow(self.frame)

        self.frame.Show(True)
        self.frame.SetSize((1024, 920))
        self.sensor_control_off()  # ??? JURE POLJSAK

        return True

    def on_help_visit(self, event):
        webbrowser.open("https://github.com/barracuda-fsh/pyobd")

    def on_help_order(self, event):
        webbrowser.open("https://www.google.com/search?q=elm327+obd2+scanner")

    def on_help_about(self, event):  # todo about box

        # HelpAboutDlg = wx.Dialog(self.frame, id, title="About")

        # box  = wx.BoxSizer(wx.HORIZONTAL)
        # box.Add(wx.StaticText(reconnectPanel,-1,Text,pos=(0,0),size=(200,200)))
        # box.Add(wx.Button(HelpAboutDlg,wx.ID_OK),0)
        # box.Add(wx.Button(HelpAboutDlg,wx.ID_CANCEL),1)

        # HelpAboutDlg.SetSizer(box)
        # HelpAboutDlg.SetAutoLayout(True)
        # sizer.Fit(HelpAboutDlg)
        # HelpAboutDlg.ShowModal()

        self.HelpAboutDlg = wx.MessageDialog(
            self.frame, about_text.ABOUT_TEXT, "About", wx.OK | wx.ICON_INFORMATION
        )
        self.HelpAboutDlg.ShowModal()
        self.HelpAboutDlg.Destroy()

    def on_result(self, event):
        self.sensors.SetItem(event.data[0], event.data[1], event.data[2])

    def on_freezeframe_result(self, event):
        self.freezeframe.SetItem(event.data[0], event.data[1], event.data[2])

    def on_status(self, event):
        if event.data[0] == 666:  # signal, that connection falied
            self.sensor_control_off()
        else:
            self.status.SetItem(event.data[0], event.data[1], event.data[2])

    def on_tests(self, event):
        self.OBDTests.SetItem(event.data[0], event.data[1], event.data[2])

    """
    def OnCombo(self, event):
        self.curr_selection1 = self.combobox1.GetSelection()
        self.curr_selection2 = self.combobox2.GetSelection()
        self.curr_selection3 = self.combobox3.GetSelection()
        self.curr_selection4 = self.combobox4.GetSelection()
    """

    def on_close(self, event):
        self.ThreadControl = 666
        time.sleep(0.1)
        # while self.senprod.state != "finished":
        #    time.sleep(0.1)

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

        self.graph_list_ctrl.DeleteAllItems()
        self.graph_list_ctrl.InsertItem(0, "")
        self.graphs_list_ctrl.DeleteAllItems()
        self.graphs_list_ctrl.InsertItem(0, "")
        self.graphs_list_ctrl.InsertItem(1, "")
        self.graphs_list_ctrl.InsertItem(2, "")
        self.graphs_list_ctrl.InsertItem(3, "")

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

        self.sensor_control_off()
        try:
            self.panel.Destroy()
        except:
            pass
        try:
            self.panel1.Destroy()
            self.panel2.Destroy()
            self.panel3.Destroy()
            self.panel4.Destroy()
        except:
            pass

    def on_graph(self, event):
        xy_data = list(zip(event.data[0][0], event.data[0][1]))
        unit = event.data[0][2]
        command_desc = event.data[0][3]
        graph_counter = event.data[0][4]
        first_time_graph_plot = event.data[1]

        def animate():
            if not first_time_graph_plot:
                self.line = wxplot.PolySpline(
                    xy_data, colour="blue", width=1, style=wx.PENSTYLE_SOLID
                )
                self.graphics = wxplot.PlotGraphics(
                    [self.line], command_desc, "frame", unit
                )
                if sys.platform.startswith("linux"):
                    if (
                            os.environ.get("DESKTOP_SESSION") == "gnome"
                            or os.environ.get("DESKTOP_SESSION") == "ubuntu"
                    ):
                        self.panel.Destroy()
                        self.panel = wxplot.PlotCanvas(self.graph_panel, pos=(0, 100))
                        self.panel.SetInitialSize(size=wx.Size(900, 400))
                self.panel.Draw(
                    self.graphics, xAxis=(graph_counter - 450, graph_counter)
                )

        if first_time_graph_plot:
            self.panel = wxplot.PlotCanvas(self.graph_panel, pos=(0, 100))
            self.panel.SetInitialSize(size=wx.Size(900, 400))
        else:
            animate()

    def on_graphs(self, event):
        xy_data1 = list(zip(event.data[0][0], event.data[0][1]))
        unit1 = event.data[0][2]
        command_desc1 = event.data[0][3]
        graph_counter1 = event.data[0][4]
        xy_data2 = list(zip(event.data[1][0], event.data[1][1]))
        unit2 = event.data[1][2]
        command_desc2 = event.data[1][3]
        graph_counter2 = event.data[1][4]
        xy_data3 = list(zip(event.data[2][0], event.data[2][1]))
        unit3 = event.data[2][2]
        command_desc3 = event.data[2][3]
        graph_counter3 = event.data[2][4]
        xy_data4 = list(zip(event.data[3][0], event.data[3][1]))
        unit4 = event.data[3][2]
        command_desc4 = event.data[3][3]
        graph_counter4 = event.data[3][4]
        first_time_graphs_plot = event.data[4]

        def animate():
            if not first_time_graphs_plot:
                self.line1 = wxplot.PolySpline(
                    xy_data1, colour="blue", width=1, style=wx.PENSTYLE_SOLID
                )
                self.graphics1 = wxplot.PlotGraphics(
                    [self.line1], command_desc1, "frame", unit1
                )
                if sys.platform.startswith("linux"):
                    if (
                            os.environ.get("DESKTOP_SESSION") == "gnome"
                            or os.environ.get("DESKTOP_SESSION") == "ubuntu"
                    ):
                        self.panel1.Destroy()
                        self.panel1 = wxplot.PlotCanvas(self.graphs_panel, pos=(0, 250))
                        self.panel1.SetInitialSize(size=wx.Size(400, 220))
                self.panel1.Draw(
                    self.graphics1, xAxis=(graph_counter1 - 200, graph_counter1)
                )

                self.line2 = wxplot.PolySpline(
                    xy_data2, colour="blue", width=1, style=wx.PENSTYLE_SOLID
                )
                self.graphics2 = wxplot.PlotGraphics(
                    [self.line2], command_desc2, "frame", unit2
                )
                if sys.platform.startswith("linux"):
                    if (
                            os.environ.get("DESKTOP_SESSION") == "gnome"
                            or os.environ.get("DESKTOP_SESSION") == "ubuntu"
                    ):
                        self.panel2.Destroy()
                        self.panel2 = wxplot.PlotCanvas(self.graphs_panel, pos=(0, 480))
                        self.panel2.SetInitialSize(size=wx.Size(400, 220))
                self.panel2.Draw(
                    self.graphics2, xAxis=(graph_counter2 - 200, graph_counter2)
                )

                self.line3 = wxplot.PolySpline(
                    xy_data3, colour="blue", width=1, style=wx.PENSTYLE_SOLID
                )
                self.graphics3 = wxplot.PlotGraphics(
                    [self.line3], command_desc3, "frame", unit3
                )
                if sys.platform.startswith("linux"):
                    if (
                            os.environ.get("DESKTOP_SESSION") == "gnome"
                            or os.environ.get("DESKTOP_SESSION") == "ubuntu"
                    ):
                        self.panel3.Destroy()
                        self.panel3 = wxplot.PlotCanvas(
                            self.graphs_panel, pos=(410, 250)
                        )
                        self.panel3.SetInitialSize(size=wx.Size(400, 220))
                self.panel3.Draw(
                    self.graphics3, xAxis=(graph_counter3 - 200, graph_counter3)
                )

                self.line4 = wxplot.PolySpline(
                    xy_data4, colour="blue", width=1, style=wx.PENSTYLE_SOLID
                )
                self.graphics4 = wxplot.PlotGraphics(
                    [self.line4], command_desc4, "frame", unit4
                )
                if sys.platform.startswith("linux"):
                    if (
                            os.environ.get("DESKTOP_SESSION") == "gnome"
                            or os.environ.get("DESKTOP_SESSION") == "ubuntu"
                    ):
                        self.panel4.Destroy()
                        self.panel4 = wxplot.PlotCanvas(
                            self.graphs_panel, pos=(410, 480)
                        )
                        self.panel4.SetInitialSize(size=wx.Size(400, 220))
                self.panel4.Draw(
                    self.graphics4, xAxis=(graph_counter4 - 200, graph_counter4)
                )

        if first_time_graphs_plot:
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

    def on_graph_value(self, event):
        self.graph_list_ctrl.SetItem(event.data[0], event.data[1], event.data[2])

    def on_graphs_value(self, event):
        self.graphs_list_ctrl.SetItem(event.data[0], event.data[1], event.data[2])

    def on_debug(self, event):
        self.trace_debug(event.data[0], event.data[1])

    def on_dtc(self, event):
        if event.data == 0:  # signal, that DTC was cleared
            self.dtc.DeleteAllItems()
        else:
            self.dtc.Append(event.data)

    def on_disconnect(self, event):  # disconnect connection to ECU
        try:
            self.ThreadControl = 666
            time.sleep(0.1)
        except:
            traceback.print_exc()

    @override
    def OnExit(self, e=None):
        self.ThreadControl = 666
        time.sleep(0.1)
        os._exit(0)

    def insert_sensor_row(self, event):
        counter = event.data
        self.sensors.InsertItem(counter, "")

    def insert_freezeframe_row(self, event):
        counter = event.data
        self.freezeframe.InsertItem(counter, "")

    def build_combo_box_graph(self, event):
        self.combobox = wx.ComboBox(self.graph_panel, choices=event.data, pos=(0, 65))
        self.build_combobox_graph_event_finished = True

    def build_combo_box_graphs(self, event):
        self.combobox1 = wx.ComboBox(
            self.graphs_panel, choices=event.data, pos=(0, 140)
        )
        self.combobox2 = wx.ComboBox(
            self.graphs_panel, choices=event.data, pos=(0, 190)
        )
        self.combobox3 = wx.ComboBox(
            self.graphs_panel, choices=event.data, pos=(330, 140)
        )
        self.combobox4 = wx.ComboBox(
            self.graphs_panel, choices=event.data, pos=(330, 190)
        )
        self.build_combobox_graphs_event_finished = True

    def destroy_combo_box(self, event):
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

    def get_selection_graph_combo_box(self, event):
        try:
            self.combobox_selection = self.combobox.GetSelection()
            self.combobox_graph_get_sel_finished = True
        except:
            pass

    def get_selection_graphs_combo_box(self, event):
        try:
            self.combobox1_selection = self.combobox1.GetSelection()
            self.combobox2_selection = self.combobox2.GetSelection()
            self.combobox3_selection = self.combobox3.GetSelection()
            self.combobox4_selection = self.combobox4.GetSelection()
            self.combobox_graphs_get_sel_finished = True
        except:
            pass

    def set_selection_graph_combo_box(self, event):
        self.combobox_selection = self.combobox.SetSelection(0)
        self.combobox_graph_set_sel_finished = True

    def set_selection_graphs_combo_box(self, event):
        self.combobox1_selection = self.combobox1.SetSelection(0)
        self.combobox2_selection = self.combobox2.SetSelection(1)
        self.combobox3_selection = self.combobox3.SetSelection(2)
        self.combobox4_selection = self.combobox4.SetSelection(3)
        self.combobox_graphs_set_sel_finished = True

    def open_port(self, e):
        print("Open port event.")
        if self.senprod:
            if self.senprod.is_alive():  # signal current producers to finish
                self.senprod.stop()
        self.ThreadControl = 0

        self.senprod = SensorProducer(
            self,
            self.COMPORT,
            self.SERTIMEOUT,
            self.RECONNATTEMPTS,
            self.BAUDRATE,
            self.FAST,
            self.nb,
        )
        self.senprod.start()

        self.sensor_control_on()

    def get_dtc(self, e):
        self.nb.SetSelection(3)
        self.ThreadControl = 2

    def add_dtc(self, code):
        self.dtc.InsertStringItem(0, "")
        self.dtc.SetItem(0, 0, code[0])
        self.dtc.SetItem(0, 1, code[1])

    def code_lookup(self, e=None):
        id = 0
        diag = wx.Frame(None, id, title="Diagnostic Trouble Codes")
        ico = wx.Icon(str(resource_path("assets/pyobd.ico")), wx.BITMAP_TYPE_ICO)
        diag.SetIcon(ico)
        tree = wx.TreeCtrl(diag, id, style=wx.TR_HAS_BUTTONS)

        root = tree.AddRoot("Code Reference")
        proot = root  # tree.AppendItem(root,"Powertrain (P) Codes")
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

    def query_clear(self, e):
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
            self.clear_dtc()

    def clear_dtc(self):
        self.ThreadControl = 1
        self.nb.SetSelection(3)

    def try_port(self, port: str):
        """returns boolean for port availability"""
        try:
            s = serial.Serial(port)
            s.close()  # explicit close 'cause of delayed GC in java
            return True

        except serial.SerialException:
            pass
        except:
            traceback.print_exc()

        return False

    def scan_serial(self):  # NEW
        """scan for available ports. return a list of serial names"""
        available = []
        available = obd.scan_serial()

        return available

    def configure(self, e=None):
        id = 0
        diag = wx.Dialog(self.frame, id, title="Configure")
        sizer = wx.BoxSizer(wx.VERTICAL)

        ports = obd.scan_serial()
        if len(ports) == 0:
            ports = ["AUTO"]
        else:
            ports.append("AUTO")

        # web open link button
        self.OpenLinkButton = wx.Button(
            diag, -1, "Click here to order ELM-USB interface", size=(260, 30)
        )
        diag.Bind(wx.EVT_BUTTON, self.on_help_order, self.OpenLinkButton)
        sizer.Add(self.OpenLinkButton)
        rb = wx.RadioBox(
            diag,
            id,
            "Choose Serial Port",
            choices=ports,
            style=wx.RA_SPECIFY_COLS,
            majorDimension=2,
        )

        sizer.Add(rb, 0)
        baudrates = [
            "AUTO",
            "38400",
            "9600",
            "115200",
            "57600",
            "19200",
            "14400",
            "3000000",
            "2000000",
            "1000000",
            "250000",
            "230400",
            "128000",
            "500000",
            "460800",
            "500000",
            "576000",
            "921600",
            "1000000",
            "1152000",
            "1500000",
            "2000000",
            "2500000",
            "3000000",
            "3500000",
            "4000000",
        ]
        brb = wx.RadioBox(
            diag,
            id,
            "Choose Baud Rate",
            choices=baudrates,
            style=wx.RA_SPECIFY_COLS,
            majorDimension=2,
        )

        sizer.Add(brb, 0)
        fb = wx.RadioBox(
            diag,
            id,
            "FAST or NORMAL:",
            choices=["FAST", "NORMAL"],
            style=wx.RA_SPECIFY_COLS,
            majorDimension=2,
        )

        sizer.Add(fb, 0)
        # timeOut input control
        timeoutPanel = wx.Panel(diag, -1)
        timeoutCtrl = wx.TextCtrl(timeoutPanel, -1, "", pos=(140, 0), size=(40, 25))
        timeoutStatic = wx.StaticText(
            timeoutPanel, -1, "Timeout:", pos=(3, 5), size=(140, 20)
        )
        timeoutCtrl.SetValue(str(self.SERTIMEOUT))

        # reconnect attempt input control
        reconnectPanel = wx.Panel(diag, -1)
        reconnectCtrl = wx.TextCtrl(reconnectPanel, -1, "", pos=(140, 0), size=(40, 25))
        reconnectStatic = wx.StaticText(
            reconnectPanel, -1, "Reconnect attempts:", pos=(3, 5), size=(140, 20)
        )
        reconnectCtrl.SetValue(str(self.RECONNATTEMPTS))

        # set actual serial port choice
        if (self.COMPORT != 0) and (self.COMPORT in ports):
            rb.SetSelection(ports.index(self.COMPORT))
        baudrates = [
            "AUTO",
            "38400",
            "9600",
            "115200",
            "57600",
            "19200",
            "14400",
            "3000000",
            "2000000",
            "1000000",
            "250000",
            "230400",
            "128000",
            "500000",
            "460800",
            "500000",
            "576000",
            "921600",
            "1000000",
            "1152000",
            "1500000",
            "2000000",
            "2500000",
            "3000000",
            "3500000",
            "4000000",
        ]
        if (self.BAUDRATE != 0) and (self.BAUDRATE in baudrates):
            brb.SetSelection(baudrates.index(self.BAUDRATE))
        if (self.FAST == "FAST") or (self.FAST == "NORMAL"):
            fb.SetSelection(["FAST", "NORMAL"].index(self.FAST))

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

            self.FAST = ["FAST", "NORMAL"][fb.GetSelection()]
            self.config.set("pyOBD", "FAST", self.FAST)

            # set and save SERTIMEOUT
            self.SERTIMEOUT = timeoutCtrl.GetValue()
            self.config.set("pyOBD", "SERTIMEOUT", self.SERTIMEOUT)

            # set and save RECONNATTEMPTS
            self.RECONNATTEMPTS = int(reconnectCtrl.GetValue())
            self.config.set("pyOBD", "RECONNATTEMPTS", self.RECONNATTEMPTS)

            # write configuration to cfg file
            self.config.write(open(self.configfilepath, "w"))


def run():
    app = PyOBDApp(0)
    app.MainLoop()


if __name__ == '__main__':
    run()
