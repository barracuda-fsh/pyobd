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

import numpy as np
from wx.lib import plot as wxplot
import gc
import traceback
import wx
import obd_io  # OBD2 funcs
import os  # os.environ
import datetime
import threading
import sys
import serial
import re
import json
import subprocess
from serial.tools import list_ports
import time
import configparser  # safe application configuration
import webbrowser  # open browser from python

from about_ui import ABOUT_DIALOG_TEXT, build_about_page
from app_events import *
from debugEvent import *
from graph_ui import GraphUIMixin
from sensor_worker import SensorProducer
from obd2_codes import pcodes

from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin
import obd

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



class MyApp(GraphUIMixin, wx.App):
    # A listctrl which auto-resizes the column boxes to fill
    class MyListCtrl(wx.ListCtrl, ListCtrlAutoWidthMixin):
        def __init__(self, parent, id, pos=wx.DefaultPosition,
                     size=wx.DefaultSize, style=0):
            wx.ListCtrl.__init__(self, parent, id, pos, size, style)
            ListCtrlAutoWidthMixin.__init__(self)

    STATUS_TOOLBAR_MAP = {
        0: "link",
        1: "protocol",
        2: "adapter",
        3: "port",
        4: "vin",
        5: "voltage",
    }

    def _build_bottom_status_toolbar(self):
        self.bottom_toolbar = wx.Panel(self.frame, -1)
        self.bottom_toolbar.SetBackgroundColour(wx.Colour(24, 31, 42))
        self.bottom_toolbar_values = {}

        toolbar_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.bottom_toolbar.SetSizer(toolbar_sizer)
        self.bottom_toolbar.SetMinSize((-1, 82))

        toolbar_fields = [
            ("link", "Link", "Disconnected"),
            ("protocol", "Protocol", "----"),
            ("adapter", "Adapter", "----"),
            ("port", "Port", "----"),
            ("vin", "VIN", "----"),
            ("voltage", "Voltage", "----"),
        ]

        for index, (key, label, value) in enumerate(toolbar_fields):
            field_sizer = wx.BoxSizer(wx.VERTICAL)

            title = wx.StaticText(self.bottom_toolbar, -1, label.upper())
            title.SetForegroundColour(wx.Colour(155, 168, 186))
            title.SetFont(wx.Font(8, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))

            value_widget = wx.StaticText(self.bottom_toolbar, -1, value)
            value_widget.SetForegroundColour(wx.Colour(236, 242, 255))
            value_widget.SetFont(wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))

            self.bottom_toolbar_values[key] = value_widget

            field_sizer.Add(title, 0, wx.BOTTOM, 2)
            field_sizer.Add(value_widget, 0)
            toolbar_sizer.Add(field_sizer, 1, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 10)

            if index < len(toolbar_fields) - 1:
                toolbar_sizer.Add(wx.StaticLine(self.bottom_toolbar, style=wx.LI_VERTICAL), 0, wx.EXPAND | wx.TOP | wx.BOTTOM, 10)

    def _set_bottom_status_defaults(self):
        defaults = {
            "link": "Disconnected",
            "protocol": "----",
            "adapter": "----",
            "port": "----",
            "vin": "----",
            "voltage": "----",
        }
        for key, value in defaults.items():
            if key in self.bottom_toolbar_values:
                self.bottom_toolbar_values[key].SetLabel(value)
        self.bottom_toolbar.Layout()

    def _update_bottom_status(self, status_index, value):
        status_key = self.STATUS_TOOLBAR_MAP.get(status_index)
        if status_key and status_key in self.bottom_toolbar_values:
            self.bottom_toolbar_values[status_key].SetLabel(str(value))
            self.bottom_toolbar.Layout()

    def _apply_touch_friendly_style(self):
        self.touch_font = wx.Font(11, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.touch_font_bold = wx.Font(11, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.home_title_font = wx.Font(17, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.home_tile_font = wx.Font(14, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        # Keep native tabs and their labels on the same system theme, including
        # dark themes where a fixed light background hides the tab text.
        tab_background = wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNFACE)
        tab_foreground = wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNTEXT)
        self.frame.SetBackgroundColour(tab_background)
        self.nb.SetBackgroundColour(tab_background)
        self.nb.SetForegroundColour(tab_foreground)
        self.frame.SetFont(self.touch_font)

        try:
            self.nb.SetPadding(wx.Size(20, 10))
        except Exception:
            pass
        self.nb.SetFont(self.touch_font_bold)

        controls = [
            self.status,
            self.OBDTests,
            self.sensors,
            self.freezeframe,
            self.dtc,
            self.trace,
            self.graph_list_ctrl,
        ]
        if hasattr(self, "graphs_list_ctrl"):
            controls.append(self.graphs_list_ctrl)
        if hasattr(self, "graphs8_list_ctrl"):
            controls.append(self.graphs8_list_ctrl)
        for control in controls:
            control.SetFont(self.touch_font)

        self.GetDTCButton.SetMinSize((140, 40))
        self.GetDTCButton.SetFont(self.touch_font_bold)
        self.ClearDTCButton.SetMinSize((140, 40))
        self.ClearDTCButton.SetFont(self.touch_font_bold)

        if hasattr(self, "add_graph_pid_button"):
            self.add_graph_pid_button.SetFont(self.touch_font_bold)
            self.remove_graph_pid_button.SetFont(self.touch_font_bold)
            self.graph_play_button.SetFont(self.touch_font_bold)
            self.graph_list_ctrl.SetFont(self.touch_font)

        if hasattr(self, "home_title"):
            self.home_title.SetFont(self.home_title_font)

        if hasattr(self, "home_scan_button"):
            self.home_scan_button.SetFont(self.home_tile_font)
            self.home_services_button.SetFont(self.home_tile_font)
            self.home_graphs_button.SetFont(self.home_tile_font)

    def _go_to_page(self, page):
        page_index = wx.NOT_FOUND
        for i in range(self.nb.GetPageCount()):
            if self.nb.GetPage(i) is page:
                page_index = i
                break

        if page_index != wx.NOT_FOUND:
            self.nb.SetSelection(page_index)

    def _swap_notebook_pages(self, title_a, title_b):
        idx_a = wx.NOT_FOUND
        idx_b = wx.NOT_FOUND
        for i in range(self.nb.GetPageCount()):
            page_title = self.nb.GetPageText(i)
            if page_title == title_a:
                idx_a = i
            elif page_title == title_b:
                idx_b = i

        if idx_a == wx.NOT_FOUND or idx_b == wx.NOT_FOUND or idx_a == idx_b:
            return

        if idx_a > idx_b:
            idx_a, idx_b = idx_b, idx_a
            title_a, title_b = title_b, title_a

        page_a = self.nb.GetPage(idx_a)
        page_b = self.nb.GetPage(idx_b)

        self.nb.RemovePage(idx_b)
        self.nb.RemovePage(idx_a)
        self.nb.InsertPage(idx_a, page_b, title_b)
        self.nb.InsertPage(idx_b, page_a, title_a)

    def _create_home_tile(self, parent, label, bg_colour, fg_colour, handler):
        button = wx.Button(parent, -1, label)
        button.SetMinSize((260, 130))
        button.SetBackgroundColour(bg_colour)
        button.SetForegroundColour(fg_colour)
        button.Bind(wx.EVT_BUTTON, handler)
        return button

    def build_home_page(self):
        self.home_panel = wx.Panel(self.nb, -1)
        self.home_panel.SetBackgroundColour(wx.Colour(236, 240, 245))
        self.home_panel.SetForegroundColour(wx.Colour(24, 31, 42))

        root_sizer = wx.BoxSizer(wx.VERTICAL)
        header_sizer = wx.BoxSizer(wx.VERTICAL)
        grid = wx.GridBagSizer(16, 16)

        self.home_title = wx.StaticText(self.home_panel, -1, "pyOBD Home — Modified by FareBrothers")
        self.home_title.SetForegroundColour(wx.Colour(24, 31, 42))

        self.home_scan_button = self._create_home_tile(
            self.home_panel,
            "SCAN\nDTC",
            wx.Colour(25, 118, 210),
            wx.Colour(255, 255, 255),
            self.OnHomeScan,
        )
        self.home_services_button = self._create_home_tile(
            self.home_panel,
            "SERVICES",
            wx.Colour(46, 125, 50),
            wx.Colour(255, 255, 255),
            self.OnHomeServices,
        )
        self.home_graphs_button = self._create_home_tile(
            self.home_panel,
            "GRAPHS",
            wx.Colour(2, 136, 209),
            wx.Colour(255, 255, 255),
            self.OnHomeGraphs,
        )

        header_sizer.Add(self.home_title, 0, wx.BOTTOM, 4)

        grid.Add(self.home_scan_button, (0, 0), span=(1, 1), flag=wx.EXPAND)
        grid.Add(self.home_services_button, (0, 1), span=(1, 1), flag=wx.EXPAND)
        grid.Add(self.home_graphs_button, (1, 0), span=(1, 2), flag=wx.EXPAND)
        grid.AddGrowableCol(0, 1)
        grid.AddGrowableCol(1, 1)
        grid.AddGrowableRow(0, 1)
        grid.AddGrowableRow(1, 1)

        root_sizer.Add(header_sizer, 0, wx.ALL, 18)
        root_sizer.Add(grid, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 18)
        self.home_panel.SetSizer(root_sizer)

        self.nb.AddPage(self.home_panel, "Home")

    def OnHomeScan(self, event):
        self.GetDTC(None)

    def OnHomeServices(self, event):
        self._go_to_page(self.status)

    def OnHomeGraphs(self, event):
        self._go_to_page(self.graph_panel)


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
            self.CONNECTION_TYPE = "AUTO"
            self.CONNECTION_TARGET = ""
            self.RECONNATTEMPTS = 5
            self.SERTIMEOUT = 1
            self.BAUDRATE = "AUTO"
            self.FAST = "NORMAL"
            self.MEASUREMENT_SYSTEM = "IMPERIAL"
        else:
            try:
                self.COMPORT = self.config.get("pyOBD", "COMPORT")
                self.CONNECTION_TYPE = self.config.get("pyOBD", "CONNECTION_TYPE", fallback="")
                self.CONNECTION_TARGET = self.config.get("pyOBD", "CONNECTION_TARGET", fallback="")
                self.RECONNATTEMPTS = self.config.getint("pyOBD", "RECONNATTEMPTS")
                self.SERTIMEOUT = self.config.get("pyOBD", "SERTIMEOUT")
                self.BAUDRATE = self.config.get("pyOBD", "BAUDRATE")
                self.FAST = self.config.get("pyOBD", "FAST")
                self.MEASUREMENT_SYSTEM = self.config.get("pyOBD", "MEASUREMENT_SYSTEM", fallback="IMPERIAL").upper()
            except Exception as e:
                print(e)
                self.COMPORT = "AUTO"
                self.CONNECTION_TYPE = "AUTO"
                self.CONNECTION_TARGET = ""
                self.RECONNATTEMPTS = 5
                self.SERTIMEOUT = 5
                self.BAUDRATE = "AUTO"
                self.FAST = "FAST"
                self.MEASUREMENT_SYSTEM = "IMPERIAL"

        if self.MEASUREMENT_SYSTEM not in ["IMPERIAL", "METRIC"]:
            self.MEASUREMENT_SYSTEM = "IMPERIAL"

        self.CONNECTION_TYPE, self.CONNECTION_TARGET = self._infer_connection_from_comport(
            self.CONNECTION_TYPE,
            self.CONNECTION_TARGET,
            self.COMPORT,
        )

        self.frame = wx.Frame(None, -1, "pyOBD-II v2.0")
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
        # Legacy 4-Graphs and 8-Graphs pages removed.
        self.trace = self.MyListCtrl(self.nb, tID, style=wx.LC_REPORT | wx.SUNKEN_BORDER)
        self.trace.InsertColumn(0, "Level", width=40)
        self.trace.InsertColumn(1, "Message")
        self.nb.AddPage(self.trace, "Trace")
        self.TraceDebug(1, "Application started")
        self.about_panel = build_about_page(self.nb)
        self.build_home_page()
        self._swap_notebook_pages("Home", "Status")

        self._build_bottom_status_toolbar()
        self._set_bottom_status_defaults()

        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.main_sizer.Add(self.nb, 1, wx.EXPAND | wx.ALL, 8)
        self.main_sizer.Add(self.bottom_toolbar, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        self.frame.SetSizer(self.main_sizer)

        self._apply_touch_friendly_style()




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

        self.frame.SetSize((1180, 900))
        self.frame.SetMinSize((960, 700))
        self.frame.Centre()
        self._go_to_page(self.home_panel)
        self.frame.Show(True)
        self.sensor_control_off() # ??? JURE POLJSAK


        return True

    def OnHelpVisit(self, event):
        webbrowser.open("https://github.com/alexfare/pyobd")

    def OnHelpOrder(self, event):
        webbrowser.open("https://www.google.com/search?q=elm327+obd2+scanner")

    def OnHelpAbout(self, event):
        Text = ABOUT_DIALOG_TEXT

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
            self._set_bottom_status_defaults()
        else:
            self.status.SetItem(event.data[0], event.data[1], event.data[2])
            self._update_bottom_status(event.data[0], event.data[2])
            # Drive UI control state from actual connection state notifications.
            if event.data[0] == 0:
                state_text = str(event.data[2])
                if state_text == "Car connected!":
                    self.sensor_control_on()
                elif state_text == "Disconnected":
                    self.sensor_control_off()
                    self._set_graph_streaming(False)

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
        self.combobox = wx.ComboBox(self.graph_panel, choices=event.data, pos=(0, 65), size=(360, 42))
        self.combobox.SetFont(self.touch_font)
        self.build_combobox_graph_event_finished=True

    def BuildComboBoxGraphs(self, event):
        self.combobox1 = wx.ComboBox(self.graphs_panel, choices=event.data, pos=(0, 140), size=(310, 42))
        self.combobox2 = wx.ComboBox(self.graphs_panel, choices=event.data, pos=(0, 190), size=(310, 42))
        self.combobox3 = wx.ComboBox(self.graphs_panel, choices=event.data, pos=(330, 140), size=(310, 42))
        self.combobox4 = wx.ComboBox(self.graphs_panel, choices=event.data, pos=(330, 190), size=(310, 42))
        self.combobox1.SetFont(self.touch_font)
        self.combobox2.SetFont(self.touch_font)
        self.combobox3.SetFont(self.touch_font)
        self.combobox4.SetFont(self.touch_font)
        self.build_combobox_graphs_event_finished=True

    def BuildComboBoxGraphs8(self, event):
        self.combobox8_1 = wx.ComboBox(self.graphs8_panel, choices=event.data, pos=(0, 240), size=(300, 42))
        self.combobox8_2 = wx.ComboBox(self.graphs8_panel, choices=event.data, pos=(0, 290), size=(300, 42))
        self.combobox8_3 = wx.ComboBox(self.graphs8_panel, choices=event.data, pos=(330, 240), size=(300, 42))
        self.combobox8_4 = wx.ComboBox(self.graphs8_panel, choices=event.data, pos=(330, 290), size=(300, 42))
        self.combobox8_5 = wx.ComboBox(self.graphs8_panel, choices=event.data, pos=(660, 240), size=(300, 42))
        self.combobox8_6 = wx.ComboBox(self.graphs8_panel, choices=event.data, pos=(660, 290), size=(300, 42))
        self.combobox8_7 = wx.ComboBox(self.graphs8_panel, choices=event.data, pos=(990, 240), size=(300, 42))
        self.combobox8_8 = wx.ComboBox(self.graphs8_panel, choices=event.data, pos=(990, 290), size=(300, 42))
        self.combobox8_1.SetFont(self.touch_font)
        self.combobox8_2.SetFont(self.touch_font)
        self.combobox8_3.SetFont(self.touch_font)
        self.combobox8_4.SetFont(self.touch_font)
        self.combobox8_5.SetFont(self.touch_font)
        self.combobox8_6.SetFont(self.touch_font)
        self.combobox8_7.SetFont(self.touch_font)
        self.combobox8_8.SetFont(self.touch_font)
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

        def reset_list_if_present(name, row_count):
            list_ctrl = getattr(self, name, None)
            if list_ctrl is None:
                return
            try:
                list_ctrl.DeleteAllItems()
                for idx in range(row_count):
                    list_ctrl.InsertItem(idx, "")
            except Exception:
                pass

        def destroy_if_present(*names):
            for name in names:
                control = getattr(self, name, None)
                if control is None:
                    continue
                try:
                    control.Destroy()
                except Exception:
                    pass

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

        reset_list_if_present("graphs_list_ctrl", 4)
        reset_list_if_present("graphs8_list_ctrl", 8)
        self._set_graph_streaming(False)
        self._refresh_graph_selection_ui()

        destroy_if_present("combobox")
        destroy_if_present("combobox1", "combobox2", "combobox3", "combobox4")
        destroy_if_present(
            "combobox8_1", "combobox8_2", "combobox8_3", "combobox8_4",
            "combobox8_5", "combobox8_6", "combobox8_7", "combobox8_8"
        )

        destroy_if_present("panel1", "panel2", "panel3", "panel4")
        destroy_if_present(
            "panel8_1", "panel8_2", "panel8_3", "panel8_4",
            "panel8_5", "panel8_6", "panel8_7", "panel8_8"
        )
        try:
            self.ThreadControl = 666

            self.sensor_control_off()
            time.sleep(0.1)

        except:
            traceback.print_exc()

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

        # Prevent reconfigure/reconnect clicks while connection attempt is in progress.
        self.settingmenu.Enable(ID_CONFIG, False)
        self.settingmenu.Enable(ID_RESET, False)
        self.settingmenu.Enable(ID_DISCONNECT, False)

        self.senprod = SensorProducer(self, self.COMPORT, self.SERTIMEOUT, self.RECONNATTEMPTS, self.BAUDRATE, self.FAST, self.nb)
        self.senprod.start()

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
        available = self._get_connected_port_names()

        return available

    def _get_connected_port_infos(self):
        try:
            return sorted(list(list_ports.comports()), key=lambda p: p.device or "")
        except Exception:
            traceback.print_exc()
            return []

    def _get_connected_port_names(self):
        names = [p.device for p in self._get_connected_port_infos() if p.device]
        if "AUTO" not in names:
            names.append("AUTO")
        if not names:
            names = ["AUTO"]
        return names

    def _get_bluetooth_adapter_choices(self):
        def _windows_bt_name_by_mac():
            if os.name != "nt":
                return {}

            command = (
                "Get-PnpDevice -Class Bluetooth | "
                "Select-Object FriendlyName,InstanceId | ConvertTo-Json -Compress"
            )
            try:
                result = subprocess.run(
                    ["powershell", "-NoProfile", "-Command", command],
                    capture_output=True,
                    text=True,
                    timeout=4,
                )
            except Exception:
                return {}

            if result.returncode != 0 or result.stdout.strip() == "":
                return {}

            try:
                parsed = json.loads(result.stdout)
            except Exception:
                return {}

            entries = parsed if isinstance(parsed, list) else [parsed]
            name_by_mac = {}
            for entry in entries:
                if not isinstance(entry, dict):
                    continue

                friendly_name = str(entry.get("FriendlyName") or "").strip()
                instance_id = str(entry.get("InstanceId") or "")

                if friendly_name == "" or friendly_name.lower().startswith("standard serial over bluetooth"):
                    continue

                matches = re.findall(r"(?<![0-9A-Fa-f])[0-9A-Fa-f]{12}(?![0-9A-Fa-f])", instance_id)
                for mac12 in matches:
                    mac = ":".join(mac12[i:i + 2] for i in range(0, 12, 2)).upper()
                    name_by_mac[mac] = friendly_name

            return name_by_mac

        def _first_mac_like(text):
            if not text:
                return ""
            match = re.search(r"(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}", text)
            return match.group(0).upper() if match else ""

        def _compact_name(text):
            name = (text or "Bluetooth Adapter").strip()
            name = re.sub(r"\s*\(COM\d+\)\s*$", "", name, flags=re.IGNORECASE)
            return name or "Bluetooth Adapter"

        def _compact_label(name, adapter_id, max_len=44):
            label = f"{name} ({adapter_id})"
            if len(label) <= max_len:
                return label
            reserve = len(adapter_id) + 5
            short_name_len = max(10, max_len - reserve)
            return f"{name[:short_name_len].rstrip()}... ({adapter_id})"

        bt_name_by_mac = _windows_bt_name_by_mac()
        choices = []
        fallback_choices = []

        for port_info in self._get_connected_port_infos():
            device = (port_info.device or "").strip()
            if device == "":
                continue

            description = _compact_name(port_info.description or port_info.product or "")
            candidates = [
                getattr(port_info, "serial_number", "") or "",
                port_info.description or "",
                port_info.hwid or "",
                getattr(port_info, "location", "") or "",
                getattr(port_info, "manufacturer", "") or "",
            ]

            adapter_id = ""
            for candidate in candidates:
                adapter_id = _first_mac_like(candidate)
                if adapter_id:
                    break

            if adapter_id == "":
                adapter_id = device

            if adapter_id in bt_name_by_mac:
                description = _compact_name(bt_name_by_mac[adapter_id])

            label = _compact_label(description, adapter_id)
            lower = label.lower()

            if "bluetooth" in lower or " bt" in lower or lower.startswith("bt"):
                choices.append((label, device))
            fallback_choices.append((label, device))

        if not choices:
            choices = fallback_choices

        choices.insert(0, ("AUTO", "AUTO"))
        return choices

    def _infer_connection_from_comport(self, connection_type, connection_target, comport):
        if connection_type in ["AUTO", "SERIAL", "WIFI", "BLUETOOTH", "CUSTOM", "DEMO"]:
            return connection_type, connection_target

        if comport == "AUTO":
            return "AUTO", ""
        if comport == "DEMO":
            return "DEMO", ""

        if isinstance(comport, str):
            upper = comport.upper()
            if upper.startswith("WIFI:"):
                return "WIFI", comport[5:]
            if upper.startswith("BT:"):
                return "BLUETOOTH", comport[3:]
            if comport.startswith("socket://"):
                return "WIFI", comport[len("socket://"):]
            if comport.startswith("rfcomm://"):
                return "BLUETOOTH", comport[len("rfcomm://"):]
            if "://" in comport:
                return "CUSTOM", comport

        return "SERIAL", comport

    def _compose_comport(self, connection_type, serial_port, target):
        target = (target or "").strip()

        if connection_type == "AUTO":
            return "AUTO"
        if connection_type == "DEMO":
            return "DEMO"
        if connection_type == "SERIAL":
            return serial_port
        if connection_type == "WIFI":
            if target == "":
                target = "192.168.0.10:35000"
            return "WIFI:" + target
        if connection_type == "BLUETOOTH":
            return "BT:" + target
        return target

    @staticmethod
    def _normalize_unit_label(unit_label):
        return str(unit_label or "").strip().lower().replace(" ", "")

    @staticmethod
    def _canonical_unit_label(unit_label):
        normalized = MyApp._normalize_unit_label(unit_label)
        aliases = {
            "mph": "mph",
            "mi/h": "mph",
            "mile/hour": "mph",
            "miles/hour": "mph",
            "kph": "kph",
            "km/h": "kph",
            "kilometer/hour": "kph",
            "kilometers/hour": "kph",
            "psi": "psi",
            "kpa": "kPa",
            "kilopascal": "kPa",
            "kilopascals": "kPa",
            "c": "C",
            "degc": "C",
            "celsius": "C",
            "f": "F",
            "degf": "F",
            "fahrenheit": "F",
            "lb/min": "lb/min",
            "lbs/min": "lb/min",
            "g/s": "g/s",
            "gram/second": "g/s",
            "grams/second": "g/s",
        }
        return aliases.get(normalized, str(unit_label or "").strip())

    def _target_unit_for_measurement_system(self, unit_label):
        normalized = self._normalize_unit_label(unit_label)
        if self.MEASUREMENT_SYSTEM == "METRIC":
            metric_map = {
                "mph": "kph",
                "mi/h": "kph",
                "mile/hour": "kph",
                "miles/hour": "kph",
                "psi": "kPa",
                "f": "degC",
                "degf": "degC",
                "fahrenheit": "degC",
                "lb/min": "g/s",
                "lbs/min": "g/s",
            }
            return metric_map.get(normalized)

        imperial_map = {
            "kph": "mph",
            "km/h": "mph",
            "kilometer/hour": "mph",
            "kilometers/hour": "mph",
            "kpa": "psi",
            "kilopascal": "psi",
            "kilopascals": "psi",
            "c": "degF",
            "degc": "degF",
            "celsius": "degF",
            "g/s": "lb/min",
            "gram/second": "lb/min",
            "grams/second": "lb/min",
        }
        return imperial_map.get(normalized)

    def _manual_convert_quantity(self, magnitude, unit_label):
        normalized = self._normalize_unit_label(unit_label)
        if self.MEASUREMENT_SYSTEM == "METRIC":
            if normalized in ("mph", "mi/h", "mile/hour", "miles/hour"):
                return magnitude * 1.609344, "kph"
            if normalized == "psi":
                return magnitude * 6.894757293168361, "kPa"
            if normalized in ("f", "degf", "fahrenheit"):
                return ((magnitude - 32.0) * 5.0 / 9.0), "C"
            if normalized in ("lb/min", "lbs/min"):
                return magnitude * 7.559872833333334, "g/s"
            return magnitude, self._canonical_unit_label(unit_label)

        if normalized in ("kph", "km/h", "kilometer/hour", "kilometers/hour"):
            return magnitude * 0.621371192237334, "mph"
        if normalized in ("kpa", "kilopascal", "kilopascals"):
            return magnitude * 0.14503773773020923, "psi"
        if normalized in ("c", "degc", "celsius"):
            return ((magnitude * 9.0 / 5.0) + 32.0), "F"
        if normalized in ("g/s", "gram/second", "grams/second"):
            return magnitude * 0.13227735731092652, "lb/min"
        return magnitude, self._canonical_unit_label(unit_label)

    @staticmethod
    def _format_quantity_text(magnitude, unit_label):
        if unit_label:
            return f"{magnitude:.2f} {unit_label}"
        return f"{magnitude:.2f}"

    def get_measurement_components(self, value):
        if value is None:
            return None, "value", "No data"

        if hasattr(value, "magnitude"):
            try:
                magnitude = float(value.magnitude)
            except Exception:
                return None, "value", str(value)

            unit_obj = getattr(value, "units", None)
            unit_label = str(unit_obj) if unit_obj is not None else str(getattr(value, "unit", ""))
            target_unit = self._target_unit_for_measurement_system(unit_label)

            if target_unit and hasattr(value, "to"):
                try:
                    converted = value.to(target_unit)
                    magnitude = float(converted.magnitude)
                    unit_label = str(getattr(converted, "units", target_unit))
                except Exception:
                    magnitude, unit_label = self._manual_convert_quantity(magnitude, unit_label)
            else:
                magnitude, unit_label = self._manual_convert_quantity(magnitude, unit_label)

            display_unit = self._canonical_unit_label(unit_label)
            return magnitude, display_unit or "value", self._format_quantity_text(magnitude, display_unit)

        return None, "value", str(value)

    def format_measurement_value(self, value):
        return self.get_measurement_components(value)[2]

    def Configure(self, e=None):
        id = 0
        diag = wx.Dialog(self.frame, id, title="Configure")
        sizer = wx.BoxSizer(wx.VERTICAL)

        ports = self._get_connected_port_names()
        bt_choices = self._get_bluetooth_adapter_choices()
        bt_labels = [label for (label, _value) in bt_choices]
        bt_value_by_label = dict(bt_choices)

        connection_types = ["AUTO", "DEMO", "SERIAL", "WIFI", "BLUETOOTH", "CUSTOM"]
        baudrates = [
            "AUTO", "38400", "9600", "115200", "57600", "19200", "14400", "3000000", "2000000",
            "1000000", "250000", "230400", "128000", "500000", "460800", "576000", "921600",
            "1152000", "1500000", "2500000", "3500000", "4000000",
        ]

        connection_type, connection_target = self._infer_connection_from_comport(
            self.CONNECTION_TYPE,
            self.CONNECTION_TARGET,
            self.COMPORT,
        )

        header_box = wx.StaticBoxSizer(wx.VERTICAL, diag, "Connection")
        top_row = wx.BoxSizer(wx.HORIZONTAL)

        type_label = wx.StaticText(diag, -1, "Connection type:")
        connection_type_choice = wx.Choice(diag, -1, choices=connection_types)
        connection_type_choice.SetSelection(connection_types.index(connection_type))
        auto_connect_check = wx.CheckBox(diag, -1, "Auto-connect")
        auto_connect_check.Disable()

        top_row.Add(type_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
        top_row.Add(connection_type_choice, 0, wx.RIGHT, 10)
        top_row.Add(auto_connect_check, 0, wx.ALIGN_CENTER_VERTICAL)
        header_box.Add(top_row, 0, wx.ALL, 6)
        sizer.Add(header_box, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 6)

        transport_row = wx.BoxSizer(wx.HORIZONTAL)

        bt_box = wx.StaticBoxSizer(wx.VERTICAL, diag, "Bluetooth Adapter")
        bluetooth_combo = wx.ComboBox(diag, -1, choices=bt_labels, style=wx.CB_DROPDOWN)
        bt_box.Add(bluetooth_combo, 0, wx.EXPAND | wx.ALL, 6)

        wifi_box = wx.StaticBoxSizer(wx.VERTICAL, diag, "WiFi settings")
        wifi_grid = wx.FlexGridSizer(rows=3, cols=2, vgap=4, hgap=6)
        wifi_grid.Add(wx.StaticText(diag, -1, "IP:"), 0, wx.ALIGN_CENTER_VERTICAL)
        wifi_ip_ctrl = wx.TextCtrl(diag, -1, "192.168.0.10", size=(130, -1))
        wifi_grid.Add(wifi_ip_ctrl, 0, wx.EXPAND)
        wifi_grid.Add(wx.StaticText(diag, -1, "Port:"), 0, wx.ALIGN_CENTER_VERTICAL)
        wifi_port_ctrl = wx.TextCtrl(diag, -1, "35000", size=(130, -1))
        wifi_grid.Add(wifi_port_ctrl, 0, wx.EXPAND)
        wifi_grid.Add(wx.StaticText(diag, -1, "Timeout:"), 0, wx.ALIGN_CENTER_VERTICAL)
        timeoutCtrl = wx.TextCtrl(diag, -1, "5", size=(80, -1))
        wifi_grid.Add(timeoutCtrl, 0, wx.EXPAND)
        wifi_box.Add(wifi_grid, 0, wx.ALL, 6)

        com_box = wx.StaticBoxSizer(wx.VERTICAL, diag, "COM settings")
        com_grid = wx.FlexGridSizer(rows=3, cols=2, vgap=4, hgap=6)
        com_grid.Add(wx.StaticText(diag, -1, "COM port:"), 0, wx.ALIGN_CENTER_VERTICAL)
        com_choice = wx.Choice(diag, -1, choices=ports)
        com_grid.Add(com_choice, 0, wx.EXPAND)
        com_grid.Add(wx.StaticText(diag, -1, "Baud rate:"), 0, wx.ALIGN_CENTER_VERTICAL)
        baud_choice = wx.Choice(diag, -1, choices=baudrates)
        com_grid.Add(baud_choice, 0, wx.EXPAND)
        auto_increase_check = wx.CheckBox(diag, -1, "Auto-increase")
        auto_increase_check.Disable()
        com_grid.Add(auto_increase_check, 0, wx.ALIGN_CENTER_VERTICAL)
        com_grid.Add((1, 1), 0)
        com_grid.AddGrowableCol(1, 1)
        com_box.Add(com_grid, 1, wx.EXPAND | wx.ALL, 6)

        transport_row.Add(bt_box, 1, wx.EXPAND | wx.ALL, 3)
        transport_row.Add(wifi_box, 0, wx.EXPAND | wx.ALL, 3)
        transport_row.Add(com_box, 0, wx.EXPAND | wx.ALL, 3)
        sizer.Add(transport_row, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 4)

        advanced_row = wx.BoxSizer(wx.HORIZONTAL)

        custom_box = wx.StaticBoxSizer(wx.VERTICAL, diag, "Custom target")
        custom_target_ctrl = wx.TextCtrl(diag, -1, "", size=(280, -1))
        custom_help = wx.StaticText(diag, -1, "Examples: socket://192.168.0.10:35000 or rfc2217://host:port")
        custom_box.Add(custom_target_ctrl, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 6)
        custom_box.Add(custom_help, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 6)

        protocol_box = wx.StaticBoxSizer(wx.VERTICAL, diag, "Protocol")
        mode_choice = wx.Choice(diag, -1, choices=["FAST", "NORMAL"])
        measurement_choice = wx.Choice(diag, -1, choices=["IMPERIAL", "METRIC"])
        reconnect_row = wx.BoxSizer(wx.HORIZONTAL)
        reconnect_row.Add(wx.StaticText(diag, -1, "Reconnect attempts:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
        reconnectCtrl = wx.TextCtrl(diag, -1, str(self.RECONNATTEMPTS), size=(70, -1))
        reconnect_row.Add(reconnectCtrl, 0)
        protocol_box.Add(wx.StaticText(diag, -1, "Send mode:"), 0, wx.LEFT | wx.RIGHT | wx.TOP, 6)
        protocol_box.Add(mode_choice, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 6)
        protocol_box.Add(wx.StaticText(diag, -1, "Measurements:"), 0, wx.LEFT | wx.RIGHT | wx.TOP, 6)
        protocol_box.Add(measurement_choice, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 6)
        protocol_box.Add(reconnect_row, 0, wx.LEFT | wx.RIGHT | wx.TOP | wx.BOTTOM, 6)

        advanced_row.Add(custom_box, 1, wx.EXPAND | wx.ALL, 3)
        advanced_row.Add(protocol_box, 0, wx.EXPAND | wx.ALL, 3)
        sizer.Add(advanced_row, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 4)

        note_text = wx.StaticText(diag, -1, "Note: these changes will be applied on the next connect to vehicle")
        sizer.Add(note_text, 0, wx.LEFT | wx.RIGHT | wx.TOP, 8)

        link_and_buttons = wx.BoxSizer(wx.HORIZONTAL)
        self.OpenLinkButton = wx.Button(diag, -1, "Order OBD adapter", size=(160, 30))
        diag.Bind(wx.EVT_BUTTON, self.OnHelpOrder, self.OpenLinkButton)
        link_and_buttons.Add(self.OpenLinkButton, 0, wx.RIGHT, 10)
        link_and_buttons.AddStretchSpacer(1)
        link_and_buttons.Add(wx.Button(diag, wx.ID_OK), 0, wx.RIGHT, 6)
        link_and_buttons.Add(wx.Button(diag, wx.ID_CANCEL), 0)
        sizer.Add(link_and_buttons, 0, wx.EXPAND | wx.ALL, 8)

        if (self.COMPORT != 0) and (self.COMPORT in ports):
            com_choice.SetSelection(ports.index(self.COMPORT))
        else:
            com_choice.SetSelection(ports.index("AUTO") if "AUTO" in ports else 0)

        if (self.BAUDRATE != 0) and (self.BAUDRATE in baudrates):
            baud_choice.SetSelection(baudrates.index(self.BAUDRATE))
        else:
            baud_choice.SetSelection(baudrates.index("AUTO"))

        if (self.FAST == "FAST") or (self.FAST == "NORMAL"):
            mode_choice.SetSelection(["FAST", "NORMAL"].index(self.FAST))
        else:
            mode_choice.SetSelection(0)

        if self.MEASUREMENT_SYSTEM in ["IMPERIAL", "METRIC"]:
            measurement_choice.SetSelection(["IMPERIAL", "METRIC"].index(self.MEASUREMENT_SYSTEM))
        else:
            measurement_choice.SetSelection(0)

        timeoutCtrl.SetValue(str(self.SERTIMEOUT or "5"))

        wifi_target = str(connection_target or "")
        if connection_type == "WIFI":
            if wifi_target.startswith("socket://"):
                wifi_target = wifi_target[len("socket://"):]
            if ":" in wifi_target:
                wifi_host, wifi_port = wifi_target.rsplit(":", 1)
            else:
                wifi_host, wifi_port = wifi_target, "35000"
            if wifi_host.strip() != "":
                wifi_ip_ctrl.SetValue(wifi_host.strip())
            if wifi_port.strip() != "":
                wifi_port_ctrl.SetValue(wifi_port.strip())

        bt_target = str(connection_target or "").strip()
        if connection_type == "BLUETOOTH" and bt_target != "":
            selected_label = None
            for label, value in bt_choices:
                if value == bt_target:
                    selected_label = label
                    break
            if selected_label is not None:
                bluetooth_combo.SetValue(selected_label)
            else:
                bluetooth_combo.SetValue(bt_target)
        else:
            bluetooth_combo.SetValue(bt_labels[0] if bt_labels else "AUTO")

        if connection_type == "CUSTOM":
            custom_target_ctrl.SetValue(str(connection_target or ""))

        # Keep all sections editable; selected connection type only determines which target is used on save.
        com_choice.Enable(True)
        baud_choice.Enable(True)
        bluetooth_combo.Enable(True)
        wifi_ip_ctrl.Enable(True)
        wifi_port_ctrl.Enable(True)
        custom_target_ctrl.Enable(True)

        diag.SetSizer(sizer)
        diag.SetAutoLayout(True)
        sizer.Fit(diag)
        diag.SetMinSize((840, 500))
        r = diag.ShowModal()
        if r == wx.ID_OK:

            # create section
            if self.config.sections() == []:
                self.config.add_section("pyOBD")
            # set and save COMPORT

            self.CONNECTION_TYPE = connection_types[connection_type_choice.GetSelection()]

            selected_port = ports[com_choice.GetSelection()]
            if self.CONNECTION_TYPE == "WIFI":
                wifi_host = wifi_ip_ctrl.GetValue().strip() or "192.168.0.10"
                wifi_port = wifi_port_ctrl.GetValue().strip() or "35000"
                self.CONNECTION_TARGET = wifi_host + ":" + wifi_port
            elif self.CONNECTION_TYPE == "BLUETOOTH":
                bt_value = bluetooth_combo.GetValue().strip() or "AUTO"
                self.CONNECTION_TARGET = bt_value_by_label.get(bt_value, bt_value)
            elif self.CONNECTION_TYPE == "CUSTOM":
                self.CONNECTION_TARGET = custom_target_ctrl.GetValue().strip()
            else:
                self.CONNECTION_TARGET = ""

            self.COMPORT = self._compose_comport(
                self.CONNECTION_TYPE,
                selected_port,
                self.CONNECTION_TARGET,
            )
            COMPORT = self.COMPORT
            self.config.set("pyOBD", "COMPORT", self.COMPORT)
            self.config.set("pyOBD", "CONNECTION_TYPE", self.CONNECTION_TYPE)
            self.config.set("pyOBD", "CONNECTION_TARGET", self.CONNECTION_TARGET)

            self.BAUDRATE = baudrates[baud_choice.GetSelection()]
            BAUDRATE = self.BAUDRATE
            self.config.set("pyOBD", "BAUDRATE", self.BAUDRATE)

            self.FAST = ["FAST", "NORMAL"][mode_choice.GetSelection()]
            self.config.set("pyOBD", "FAST", self.FAST)

            self.MEASUREMENT_SYSTEM = ["IMPERIAL", "METRIC"][measurement_choice.GetSelection()]
            self.config.set("pyOBD", "MEASUREMENT_SYSTEM", self.MEASUREMENT_SYSTEM)

            # set and save SERTIMEOUT
            self.SERTIMEOUT = timeoutCtrl.GetValue()
            self.config.set("pyOBD", "SERTIMEOUT", self.SERTIMEOUT)


            # set and save RECONNATTEMPTS
            try:
                self.RECONNATTEMPTS = max(1, int(reconnectCtrl.GetValue()))
            except ValueError:
                self.RECONNATTEMPTS = 5
            self.config.set("pyOBD", "RECONNATTEMPTS", self.RECONNATTEMPTS)

            # write configuration to cfg file
            self.config.write(open(self.configfilepath, 'w'))

    def OnExit(self, e=None):
        self.ThreadControl = 666
        time.sleep(0.1)
        os._exit(0)


def main():
    app = MyApp(False)
    app.MainLoop()


if __name__ == "__main__":
    main()
