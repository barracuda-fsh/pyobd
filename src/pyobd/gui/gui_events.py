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
from enum import IntEnum

import wx

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
ID_ABOUT = 101
ID_EXIT = 110


class GUIEvent(IntEnum):
    RESULT = 1000
    DTC = 1001
    STATUS = 1002
    TESTS = 1003
    DEBUG = 1004
    GRAPH = 1005
    GRAPH_VALUE = 1006
    COMBOBOX = 1007
    CLOSE = 1008
    BUILD_COMBOBOXGRAPH = 1009
    DESTROY_COMBOBOX = 1010
    COMBOBOXGRAPH_GETSELECTION = 1011
    INSERT_SENSOR_ROW = 1012
    INSERT_FREEZEFRAME_ROW = 1013
    FREEZEFRAME_RESULT = 1014
    COMBOBOXGRAPH_SETSELECTION = 1015
    BUILD_COMBOBOXGRAPHS = 1016
    COMBOBOXGRAPHS_GETSELECTION = 1017
    COMBOBOXGRAPHS_SETSELECTION = 1018
    GRAPHS_VALUE = 1019
    GRAPHS = 1020


class DebugEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""

    def __init__(self, data: list):
        """Init Result Event."""
        super().__init__()
        self.SetEventType(GUIEvent.DEBUG)
        self.data = data


class ResultEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""

    def __init__(self, data):
        """Init Result Event."""
        super().__init__()
        self.SetEventType(GUIEvent.RESULT)
        self.data = data


class FreezeframeResultEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""

    def __init__(self, data):
        """Init Result Event."""
        super().__init__()
        self.SetEventType(GUIEvent.FREEZEFRAME_RESULT)
        self.data = data


class InsertSensorRowEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""

    def __init__(self, data):
        """Init Result Event."""
        super().__init__()
        self.SetEventType(GUIEvent.INSERT_SENSOR_ROW)
        self.data = data


class InsertFreezeframeRowEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""

    def __init__(self, data):
        """Init Result Event."""
        super().__init__()
        self.SetEventType(GUIEvent.INSERT_FREEZEFRAME_ROW)
        self.data = data


class BuildComboBoxGraphEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""

    def __init__(self, data):
        """Init Result Event."""
        super().__init__()
        self.SetEventType(GUIEvent.BUILD_COMBOBOXGRAPH)
        self.data = data


class BuildComboBoxGraphsEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""

    def __init__(self, data):
        """Init Result Event."""
        super().__init__()
        self.SetEventType(GUIEvent.BUILD_COMBOBOXGRAPHS)
        self.data = data


class DestroyComboBoxEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""

    def __init__(self, data):
        """Init Result Event."""
        super().__init__()
        self.SetEventType(GUIEvent.DESTROY_COMBOBOX)
        self.data = data


class GetSelectionComboBoxGraphEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""

    def __init__(self, data):
        """Init Result Event."""
        super().__init__()
        self.SetEventType(GUIEvent.COMBOBOXGRAPH_GETSELECTION)
        self.data = data


class GetSelectionComboBoxGraphsEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""

    def __init__(self, data):
        """Init Result Event."""
        super().__init__()
        self.SetEventType(GUIEvent.COMBOBOXGRAPHS_GETSELECTION)
        self.data = data


class SetSelectionComboBoxGraphEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""

    def __init__(self, data):
        """Init Result Event."""
        super().__init__()
        self.SetEventType(GUIEvent.COMBOBOXGRAPH_SETSELECTION)
        self.data = data


class SetSelectionComboBoxGraphsEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""

    def __init__(self, data):
        """Init Result Event."""
        super().__init__()
        self.SetEventType(GUIEvent.COMBOBOXGRAPHS_SETSELECTION)
        self.data = data


class GraphValueEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""

    def __init__(self, data):
        """Init Result Event."""
        super().__init__()
        self.SetEventType(GUIEvent.GRAPH_VALUE)
        self.data = data


class GraphsValueEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""

    def __init__(self, data):
        """Init Result Event."""
        super().__init__()
        self.SetEventType(GUIEvent.GRAPHS_VALUE)
        self.data = data


class GraphEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""

    def __init__(self, data):
        """Init Result Event."""
        super().__init__()
        self.SetEventType(GUIEvent.GRAPH)
        self.data = data


class GraphsEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""

    def __init__(self, data):
        """Init Result Event."""
        super().__init__()
        self.SetEventType(GUIEvent.GRAPHS)
        self.data = data


class DTCEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""

    def __init__(self, data):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(GUIEvent.DTC)
        self.data = data


class StatusEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""

    def __init__(self, data: list):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(GUIEvent.STATUS)
        self.data = data


class CloseEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""

    def __init__(self, data):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(GUIEvent.CLOSE)
        self.data = data


class TestEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""

    def __init__(self, data):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(GUIEvent.TESTS)
        self.data = data
