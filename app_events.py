"""wx event types shared by the pyOBD UI and background worker."""

import wx


EVT_RESULT_ID = 1000
EVT_DTC_ID = 1001
EVT_STATUS_ID = 1002
EVT_TESTS_ID = 1003
EVT_GRAPH_ID = 1035
EVT_GRAPH_VALUE_ID = 1036
EVT_CLOSE_ID = 1037
EVT_BUILD_COMBOBOXGRAPH_ID = 1038
EVT_DESTROY_COMBOBOX_ID = 1039
EVT_COMBOBOXGRAPH_GETSELECTION_ID = 1040
EVT_INSERT_SENSOR_ROW_ID = 1041
EVT_INSERT_FREEZEFRAME_ROW_ID = 1042
EVT_FREEZEFRAME_RESULT_ID = 1043
EVT_COMBOBOXGRAPH_SETSELECTION_ID = 1044
EVT_BUILD_COMBOBOXGRAPHS_ID = 1045
EVT_COMBOBOXGRAPHS_GETSELECTION_ID = 1046
EVT_COMBOBOXGRAPHS_SETSELECTION_ID = 1047
EVT_GRAPHS_VALUE_ID = 1048
EVT_GRAPHS_ID = 1049
EVT_GRAPHS8_ID = 1050
EVT_GRAPHS8_VALUE_ID = 1051
EVT_BUILD_COMBOBOXGRAPHS8_ID = 1102
EVT_COMBOBOXGRAPHS8_GETSELECTION_ID = 1105
EVT_COMBOBOXGRAPHS8_SETSELECTION_ID = 1106


def EVT_RESULT(window, handler, event_id):
    window.Connect(-1, -1, event_id, handler)


class DataEvent(wx.PyEvent):
    event_type = None

    def __init__(self, data):
        super().__init__()
        self.SetEventType(self.event_type)
        self.data = data


def _event_class(name, event_type):
    return type(name, (DataEvent,), {"event_type": event_type})


ResultEvent = _event_class("ResultEvent", EVT_RESULT_ID)
FreezeframeResultEvent = _event_class("FreezeframeResultEvent", EVT_FREEZEFRAME_RESULT_ID)
InsertSensorRowEvent = _event_class("InsertSensorRowEvent", EVT_INSERT_SENSOR_ROW_ID)
InsertFreezeframeRowEvent = _event_class("InsertFreezeframeRowEvent", EVT_INSERT_FREEZEFRAME_ROW_ID)
BuildComboBoxGraphEvent = _event_class("BuildComboBoxGraphEvent", EVT_BUILD_COMBOBOXGRAPH_ID)
BuildComboBoxGraphsEvent = _event_class("BuildComboBoxGraphsEvent", EVT_BUILD_COMBOBOXGRAPHS_ID)
BuildComboBoxGraphs8Event = _event_class("BuildComboBoxGraphs8Event", EVT_BUILD_COMBOBOXGRAPHS8_ID)
DestroyComboBoxEvent = _event_class("DestroyComboBoxEvent", EVT_DESTROY_COMBOBOX_ID)
GetSelectionComboBoxGraphEvent = _event_class(
    "GetSelectionComboBoxGraphEvent", EVT_COMBOBOXGRAPH_GETSELECTION_ID
)
GetSelectionComboBoxGraphsEvent = _event_class(
    "GetSelectionComboBoxGraphsEvent", EVT_COMBOBOXGRAPHS_GETSELECTION_ID
)
GetSelectionComboBoxGraphs8Event = _event_class(
    "GetSelectionComboBoxGraphs8Event", EVT_COMBOBOXGRAPHS8_GETSELECTION_ID
)
SetSelectionComboBoxGraphEvent = _event_class(
    "SetSelectionComboBoxGraphEvent", EVT_COMBOBOXGRAPH_SETSELECTION_ID
)
SetSelectionComboBoxGraphsEvent = _event_class(
    "SetSelectionComboBoxGraphsEvent", EVT_COMBOBOXGRAPHS_SETSELECTION_ID
)
SetSelectionComboBoxGraphs8Event = _event_class(
    "SetSelectionComboBoxGraphs8Event", EVT_COMBOBOXGRAPHS8_SETSELECTION_ID
)
GraphValueEvent = _event_class("GraphValueEvent", EVT_GRAPH_VALUE_ID)
GraphsValueEvent = _event_class("GraphsValueEvent", EVT_GRAPHS_VALUE_ID)
Graphs8ValueEvent = _event_class("Graphs8ValueEvent", EVT_GRAPHS8_VALUE_ID)
GraphEvent = _event_class("GraphEvent", EVT_GRAPH_ID)
GraphsEvent = _event_class("GraphsEvent", EVT_GRAPHS_ID)
Graphs8Event = _event_class("Graphs8Event", EVT_GRAPHS8_ID)
DTCEvent = _event_class("DTCEvent", EVT_DTC_ID)
StatusEvent = _event_class("StatusEvent", EVT_STATUS_ID)
CloseEvent = _event_class("CloseEvent", EVT_CLOSE_ID)
TestEvent = _event_class("TestEvent", EVT_TESTS_ID)

