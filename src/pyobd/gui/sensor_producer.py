import datetime
import threading
import time
import traceback

import numpy as np
import wx

from pyobd import obd_io, obd
from pyobd.gui.gui_events import StatusEvent, DebugEvent, GraphEvent, GraphValueEvent, GraphsEvent, GraphsValueEvent, \
    TestEvent, InsertSensorRowEvent, ResultEvent, DTCEvent, InsertFreezeframeRowEvent, FreezeframeResultEvent, \
    BuildComboBoxGraphEvent, SetSelectionComboBoxGraphEvent, GetSelectionComboBoxGraphEvent, BuildComboBoxGraphsEvent, \
    SetSelectionComboBoxGraphsEvent, GetSelectionComboBoxGraphsEvent, CloseEvent
from pyobd.gui.utils import AppTab
from pyobd.obd import OBDStatus
from pyobd.obd_io import OBDConnection


class SensorProducer(threading.Thread):
    def __init__(
            self,
            _notify_window: wx.App,
            port_name: str,
            timeout: int,
            reconnection_attempts: int,
            baudrate: int,
            fast: bool,
            _nb,
    ):
        # from queue import Queue
        self.port_name = port_name
        self.reconnection_attempts = reconnection_attempts
        self.timeout = timeout
        self.port = None
        self._notify_window = _notify_window
        self.baudrate = baudrate
        self.fast = fast
        self._nb = _nb
        super().__init__()
        self.state = "started"
        self.obd: OBDConnection | None = None
        self.elm_version: str | None = None
        self.elm_voltage: str | None = None
        self.protocol: str | None = None
        self.vin: str | None = None

    def init_communication(self) -> bool:
        if self.obd:
            self.obd.close()
            self.obd = None

        wx.PostEvent(self._notify_window, StatusEvent([0, 1, "Connecting...."]))
        self.obd = OBDConnection(
            self.port_name,
            self._notify_window,
            self.baudrate,
            self.timeout,
            self.reconnection_attempts,
            self.fast,
        )
        if self.obd.connection.status != OBDStatus.CAR_CONNECTED:  # Cant open serial port
            print(f'Gbenga status is {self.obd.connection.status}')
            # wx.PostEvent(self._notify_window, StatusEvent([666]))  # signal apl, that communication was disconnected
            # wx.PostEvent(self._notify_window, StatusEvent([0, 1, "Error cant connect..."]))
            # self.state="finished"
            self.stop()
            return False
        elif self.obd.connection.status == OBDStatus.CAR_CONNECTED:
            wx.PostEvent(
                self._notify_window, DebugEvent([1, "Communication initialized..."])
            )
            wx.PostEvent(self._notify_window, StatusEvent([0, 1, "Car connected!"]))

            response = self.obd.connection.query(obd.commands.ELM_VERSION)
            self.elm_version = str(response.value)
            response = self.obd.connection.query(obd.commands.ELM_VOLTAGE)
            self.elm_voltage = str(response.value)
            wx.PostEvent(
                self._notify_window, StatusEvent([5, 1, str(self.elm_voltage)])
            )
            self.protocol = self.obd.connection.protocol_name()

            wx.PostEvent(self._notify_window, StatusEvent([2, 1, str(self.elm_version)]))
            wx.PostEvent(
                self._notify_window, StatusEvent([1, 1, self.protocol])
            )
            wx.PostEvent(
                self._notify_window,
                StatusEvent([3, 1, str(self.obd.connection.port_name())]),
            )
            response = self.obd.connection.query(obd.commands.VIN)
            if response.value:
                self.vin = response.value.decode()
                wx.PostEvent(
                    self._notify_window, StatusEvent([4, 1, self.vin])
                )
            return True

    def run(self):
        if not self.init_communication():
            self._notify_window.ThreadControl = 666
            self.state = "finished"
            return None

        self.baudrate = self.obd.connection.interface.baudrate
        self.port_name = self.obd.connection.port_name()

        last_active_tab = AppTab.UNKNOWN
        active_tab = AppTab.UNKNOWN
        first_time_sensors = True
        first_time_freezeframe = True
        first_time = True

        first_time_graph = True
        first_time_graphs = True
        self.first_time_graph_plot = True
        self.first_time_graphs_plot = True
        self.graph_counter = 0
        self.graph_counter1 = 0
        self.graph_dirty1 = False
        self.graph_dirty2 = False
        self.graph_dirty3 = False
        self.graph_dirty4 = False
        sensors = []
        freeze_frames = []
        graph_commands = []
        sensor_descriptions = []
        # misfire_cylinder_supported = True

        # pimp_counter = 0
        # time_prev = datetime.datetime.now()
        # time_now = datetime.datetime.now()

        self._init_all_graphs()

        while self._notify_window.ThreadControl != 666:
            print(self._notify_window.ThreadControl)
            if self.obd.connection.status != OBDStatus.CAR_CONNECTED:
                self._reconnect()
                continue
            last_active_tab = active_tab
            active_tab = self._nb.GetSelection()  # picking the tab in the GUI

            if not first_time:
                diff = (time_end - time_start).total_seconds()
                if (diff < 0.08333) and (diff > 0):
                    sleep_time = 0.08333 - diff
                    time.sleep(sleep_time)
                    print("Slept for " + str(sleep_time) + " seconds.")
            time_start = datetime.datetime.now()

            if active_tab != AppTab.SINGLE_GRAPH and self.graph_counter != 0:
                self.graph_x_vals = np.array([])
                self.graph_y_vals = np.array([])
                self.graph_counter = 0
                self.first_time_graph_plot = True
                if self.first_time_graph_plot:
                    self.unit = "unit"
                desc = self.current_command.desc or "None"
                wx.PostEvent(
                    self._notify_window,
                    GraphEvent(
                        [
                            (
                                self.graph_x_vals,
                                self.graph_y_vals,
                                self.unit,
                                desc,
                                self.graph_counter,
                            ),
                            self.first_time_graph_plot,
                        ]
                    ),
                )
                self.first_time_graph_plot = False
                wx.PostEvent(
                    self._notify_window,
                    GraphValueEvent([0, 0, self.current_command.command]),
                )
                wx.PostEvent(
                    self._notify_window,
                    GraphValueEvent([0, 1, self.current_command.desc]),
                )

            if active_tab != AppTab.MULTIPLE_GRAPHS and self.graph_counter1 != 0:
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
                wx.PostEvent(
                    self._notify_window,
                    GraphsEvent(
                        [
                            (
                                self.graph_x_vals1,
                                self.graph_y_vals1,
                                self.unit1,
                                desc1,
                                self.graph_counter1,
                            ),
                            (
                                self.graph_x_vals2,
                                self.graph_y_vals2,
                                self.unit2,
                                desc2,
                                self.graph_counter2,
                            ),
                            (
                                self.graph_x_vals3,
                                self.graph_y_vals3,
                                self.unit3,
                                desc3,
                                self.graph_counter3,
                            ),
                            (
                                self.graph_x_vals4,
                                self.graph_y_vals4,
                                self.unit4,
                                desc4,
                                self.graph_counter4,
                            ),
                            (self.first_time_graphs_plot),
                        ]
                    ),
                )
                wx.PostEvent(
                    self._notify_window,
                    GraphsValueEvent([0, 0, self.current_command1.command]),
                )
                wx.PostEvent(
                    self._notify_window,
                    GraphsValueEvent([0, 1, self.current_command1.desc]),
                )

                wx.PostEvent(
                    self._notify_window,
                    GraphsValueEvent([1, 0, self.current_command2.command]),
                )
                wx.PostEvent(
                    self._notify_window,
                    GraphsValueEvent([1, 1, self.current_command2.desc]),
                )

                wx.PostEvent(
                    self._notify_window,
                    GraphsValueEvent([2, 0, self.current_command3.command]),
                )
                wx.PostEvent(
                    self._notify_window,
                    GraphsValueEvent([2, 1, self.current_command3.desc]),
                )

                wx.PostEvent(
                    self._notify_window,
                    GraphsValueEvent([3, 0, self.current_command4.command]),
                )
                wx.PostEvent(
                    self._notify_window,
                    GraphsValueEvent([3, 1, self.current_command4.desc]),
                )

            if active_tab == AppTab.STATUS:  # show status tab
                response = self.obd.connection.query(obd.commands.RPM)
                if response.value is None:
                    self._reconnect()
                    continue

                response = self.obd.connection.query(obd.commands.ELM_VOLTAGE)
                self.elm_voltage = str(response.value)
                wx.PostEvent(
                    self._notify_window, StatusEvent([5, 1, str(self.elm_voltage)])
                )

            elif active_tab == AppTab.TESTS:  # show tests tab
                self._emit_test_events()
            elif active_tab == AppTab.SENSORS:  # show sensor tab
                if first_time_sensors:
                    sensors = []
                    counter = 0
                    first_time_sensors = False
                    for command in obd.commands[1]:
                        if command and command.command not in {
                            b"0100",
                            b"0101",
                            b"0120",
                            b"0140",
                            b"0103",
                            b"0102",
                            b"011C",
                            b"0113",
                            b"0141",
                            b"0151",
                        }:
                            response = self.obd.connection.query(command)
                            if response.value is None:
                                continue
                            else:
                                sensors.append([command, command.desc])

                                # app.sensors.InsertItem(counter, "")
                                wx.PostEvent(
                                    self._notify_window,
                                    InsertSensorRowEvent(counter),
                                )
                                wx.PostEvent(
                                    self._notify_window,
                                    ResultEvent(
                                        [
                                            counter,
                                            0,
                                            command.command.decode("utf-8"),
                                        ]
                                    ),
                                )
                                wx.PostEvent(
                                    self._notify_window,
                                    ResultEvent(
                                        [counter, 1, str(command.desc)]
                                    ),
                                )
                                wx.PostEvent(
                                    self._notify_window,
                                    ResultEvent([counter, 2, str(response.value)]),
                                )
                                counter = counter + 1
                    # s = self.connection.connection.query(obd.commands.ELM_VOLTAGE)
                    # sensor_list.append([obd.commands.ELM_VOLTAGE, obd.commands.ELM_VOLTAGE.desc, str(s.value)])
                    # wx.PostEvent(self._notify_window, InsertSensorRowEvent(counter))
                    # wx.PostEvent(self._notify_window, ResultEvent([counter, 0, str(obd.commands.ELM_VOLTAGE.command)]))
                    # wx.PostEvent(self._notify_window, ResultEvent([counter, 1, str(obd.commands.ELM_VOLTAGE.desc)]))
                    # wx.PostEvent(self._notify_window, ResultEvent([counter, 2, str(s.value)]))
                else:
                    # for i in range(0, app.sensors.GetItemCount()):
                    #    app.sensors.DeleteItem(0)
                    counter = 0
                    for sensor in sensors:
                        response = self.obd.connection.query(sensor[0])
                        if response.value is None:
                            self._reconnect()
                            continue
                        wx.PostEvent(
                            self._notify_window,
                            ResultEvent(
                                [counter, 0, sensor[0].command.decode("utf-8")]
                            ),
                        )
                        wx.PostEvent(
                            self._notify_window,
                            ResultEvent([counter, 1, str(sensor[1])]),
                        )
                        wx.PostEvent(
                            self._notify_window,
                            ResultEvent([counter, 2, str(response.value)]),
                        )
                        counter = counter + 1

            elif active_tab == AppTab.DTC:  # show DTC tab
                response = self.obd.connection.query(obd.commands.RPM)
                if response.value is None:
                    self._reconnect()
                    continue

                if self._notify_window.ThreadControl == 1:  # clear DTC
                    response = self.obd.connection.query(obd.commands["CLEAR_DTC"])

                    if (
                            self._notify_window.ThreadControl == 666
                    ):  # before reset ThreadControl we must check if main thread did not want us to finish
                        break

                    self._notify_window.ThreadControl = 0
                    last_active_tab = AppTab.UNKNOWN  # to reread DTC
                if self._notify_window.ThreadControl == 2:  # reread DTC
                    last_active_tab = AppTab.UNKNOWN

                    if self._notify_window.ThreadControl == 666:
                        break

                    self._notify_window.ThreadControl = 0

                    pass
                if last_active_tab != AppTab.DTC:
                    wx.PostEvent(self._notify_window, DTCEvent(0))  # clear list
                    response = self.obd.connection.query(obd.commands.GET_DTC)
                    dtc_codes = []
                    print("DTCCODES:", response.value)
                    if response.value:
                        for dtc_code in response.value:
                            dtc_codes.append((dtc_code[0], "Active", dtc_code[1]))
                    response = self.obd.connection.query(obd.commands.FREEZE_DTC)
                    print("FREEZECODES:", response.value)
                    if response.value:
                        dtc_code = response.value
                        if "P0000" not in dtc_code:
                            dtc_codes.append((dtc_code[0], "Passive", dtc_code[1]))

                    print("DTCcodes and FREEZEcodes:", dtc_codes)
                    if len(dtc_codes) > 0:
                        for dtc_code in dtc_codes:
                            wx.PostEvent(self._notify_window, DTCEvent(dtc_code))
                    elif len(dtc_codes) == 0:
                        wx.PostEvent(
                            self._notify_window,
                            DTCEvent(["", "", "No DTC codes (codes cleared)"]),
                        )

            elif active_tab == AppTab.FREEZE_FRAME:  # show freezeframe tab
                if first_time_freezeframe:
                    freeze_frames = []
                    counter = 0
                    first_time_freezeframe = False
                    for command in obd.commands[2]:
                        if command and command.command not in {
                            b"0200",
                            b"0201",
                            b"0220",
                            b"0240",
                            b"0203",
                            b"0202",
                            b"021C",
                            b"0213",
                            b"0241",
                            b"0251",
                        }:
                            response = self.obd.connection.query(command)
                            if response.value is None:
                                continue
                            else:
                                freeze_frames.append(
                                    [
                                        command.command,
                                        command.desc,
                                        str(response.value),
                                    ]
                                )
                                wx.PostEvent(
                                    self._notify_window,
                                    InsertFreezeframeRowEvent(counter),
                                )
                                wx.PostEvent(
                                    self._notify_window,
                                    FreezeframeResultEvent(
                                        [
                                            counter,
                                            0,
                                            command.command.decode("utf-8"),
                                        ]
                                    ),
                                )
                                wx.PostEvent(
                                    self._notify_window,
                                    FreezeframeResultEvent(
                                        [counter, 1, str(command.desc)]
                                    ),
                                )
                                wx.PostEvent(
                                    self._notify_window,
                                    FreezeframeResultEvent(
                                        [counter, 2, str(response.value)]
                                    ),
                                )
                                counter = counter + 1
                else:
                    counter = 0
                    for sensor in freeze_frames:
                        for command in obd.commands[2]:
                            if command.command == sensor[0]:
                                response = self.obd.connection.query(command)
                                if response.value is None:
                                    self._reconnect()
                                    continue
                                freeze_frames[counter] = [
                                    command.command,
                                    command.desc,
                                    str(response.value),
                                ]
                                counter = counter + 1
                    counter = 0
                    for sensor in freeze_frames:
                        wx.PostEvent(
                            self._notify_window,
                            FreezeframeResultEvent(
                                [counter, 0, sensor[0].decode("utf-8")]
                            ),
                        )
                        wx.PostEvent(
                            self._notify_window,
                            FreezeframeResultEvent([counter, 1, str(sensor[1])]),
                        )
                        wx.PostEvent(
                            self._notify_window,
                            FreezeframeResultEvent([counter, 2, str(sensor[2])]),
                        )
                        counter = counter + 1
                        # if sens[2] == "None" and sens[0]!='0203':
                        #    raise AttributeError

            elif active_tab == AppTab.SINGLE_GRAPH:  # show Graph tab
                if first_time_graph:
                    print("First time graph")
                    # wx.PostEvent(self._notify_window, DestroyComboBoxEvent([]))
                    self.graph_x_vals = np.array([])
                    self.graph_y_vals = np.array([])
                    self.graph_counter = 0
                    self.current_command = None

                    graph_commands = []
                    sensor_descriptions = []

                    # wx.PostEvent(self._notify_window, GraphEvent((self.current_command, [], [])))
                    prev_command = None

                    first_time_graph = False
                    for command in obd.commands[1]:
                        if command and command.command not in {
                            b"0100",
                            b"0101",
                            b"0120",
                            b"0140",
                            b"0103",
                            b"0102",
                            b"011C",
                            b"0113",
                            b"0141",
                            b"0151",
                        }:
                            response = self.obd.connection.query(command)
                            if response.value is None:
                                continue
                            else:
                                graph_commands.append(command)
                    graph_commands.append(obd.commands.ELM_VOLTAGE)
                    # sensor_descriptions.append("None")
                    for command in graph_commands:
                        sensor_descriptions.append(command.desc)
                    self._notify_window.build_combobox_graph_event_finished = False
                    wx.PostEvent(
                        self._notify_window,
                        BuildComboBoxGraphEvent(sensor_descriptions),
                    )
                    while not self._notify_window.build_combobox_graph_event_finished:
                        time.sleep(0.01)
                    self._notify_window.combobox_graph_set_sel_finished = False
                    wx.PostEvent(
                        self._notify_window, SetSelectionComboBoxGraphEvent([])
                    )
                    while not self._notify_window.combobox_graph_set_sel_finished:
                        time.sleep(0.01)
                else:
                    self._notify_window.combobox_graph_get_sel_finished = False
                    wx.PostEvent(
                        self._notify_window, GetSelectionComboBoxGraphEvent([])
                    )
                    while not self._notify_window.combobox_graph_get_sel_finished:
                        time.sleep(0.01)
                    curr_selection = self._notify_window.combobox_selection

                    if sensor_descriptions[curr_selection] == "None":
                        curr_selection = -1
                    if curr_selection != -1:
                        prev_command = self.current_command
                        self.current_command = graph_commands[curr_selection]
                    else:
                        self.current_command = None

                    if self.current_command:
                        if not prev_command or (
                                prev_command != self.current_command
                        ):
                            self.graph_x_vals = np.array([])
                            self.graph_y_vals = np.array([])
                            self.graph_counter = 0
                            wx.PostEvent(
                                self._notify_window,
                                GraphValueEvent(
                                    [0, 0, self.current_command.command]
                                ),
                            )
                            wx.PostEvent(
                                self._notify_window,
                                GraphValueEvent([0, 1, self.current_command.desc]),
                            )
                        else:
                            response = self.obd.connection.query(
                                self.current_command
                            )
                            if response.value is None:
                                self._reconnect()
                                continue
                            self.graph_x_vals = np.append(
                                self.graph_x_vals, self.graph_counter
                            )
                            try:
                                self.graph_y_vals = np.append(
                                    self.graph_y_vals, float(response.value.magnitude)
                                )
                            except AttributeError:
                                self.graph_y_vals = np.append(
                                    self.graph_y_vals, float(0)
                                )
                            if len(self.graph_x_vals) > 450:
                                self.graph_x_vals = np.delete(
                                    self.graph_x_vals, (0)
                                )
                                self.graph_y_vals = np.delete(
                                    self.graph_y_vals, (0)
                                )

                            self.graph_counter = self.graph_counter + 1
                            prev_command = self.current_command

                            if response.value is None:
                                wx.PostEvent(
                                    self._notify_window,
                                    GraphValueEvent([0, 2, str(0)]),
                                )
                                self.unit = "unit"
                            else:
                                wx.PostEvent(
                                    self._notify_window,
                                    GraphValueEvent([0, 2, str(response.value)]),
                                )
                                try:
                                    self.unit = str(response.value).split(" ")[1]
                                except IndexError:
                                    self.unit = "unit"

                    else:
                        self.graph_x_vals = np.array([])
                        self.graph_y_vals = np.array([])
                        self.graph_counter = 0

                    if self.first_time_graph_plot:
                        self.unit = "unit"

                    if self.current_command == None:
                        desc = "None"
                    else:
                        desc = self.current_command.desc

                    wx.PostEvent(
                        self._notify_window,
                        GraphEvent(
                            [
                                (
                                    self.graph_x_vals,
                                    self.graph_y_vals,
                                    self.unit,
                                    desc,
                                    self.graph_counter,
                                ),
                                (self.first_time_graph_plot),
                            ]
                        ),
                    )
                    self.first_time_graph_plot = False
                    # time.sleep(0.2)

            elif active_tab == AppTab.MULTIPLE_GRAPHS:  # show Graphs tab
                if first_time_graphs:
                    print("First time graph")
                    # wx.PostEvent(self._notify_window, DestroyComboBoxEvent([]))
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
                    # wx.PostEvent(self._notify_window, GraphEvent((self.current_command, [], [])))
                    prev_command1 = None
                    prev_command2 = None
                    prev_command3 = None
                    prev_command4 = None
                    first_time_graphs = False
                    for command in obd.commands[1]:
                        if command and command.command not in {
                                    b"0100",
                                    b"0101",
                                    b"0120",
                                    b"0140",
                                    b"0103",
                                    b"0102",
                                    b"011C",
                                    b"0113",
                                    b"0141",
                                    b"0151",
                                    }:
                            response = self.obd.connection.query(command)
                            if response.value is None:
                                continue
                            else:
                                graph_commands.append(command)
                    graph_commands.append(obd.commands.ELM_VOLTAGE)
                    sensor_descriptions = []
                    # sensor_descriptions.append("None")
                    for command in graph_commands:
                        sensor_descriptions.append(command.desc)
                    self._notify_window.build_combobox_graphs_event_finished = False
                    wx.PostEvent(
                        self._notify_window,
                        BuildComboBoxGraphsEvent(sensor_descriptions),
                    )
                    while not self._notify_window.build_combobox_graphs_event_finished:
                        time.sleep(0.01)
                    self._notify_window.combobox_graphs_set_sel_finished = False
                    wx.PostEvent(
                        self._notify_window, SetSelectionComboBoxGraphsEvent([])
                    )
                    while not self._notify_window.combobox_graphs_set_sel_finished:
                        time.sleep(0.01)
                else:
                    self._notify_window.combobox_graphs_get_sel_finished = False
                    wx.PostEvent(
                        self._notify_window, GetSelectionComboBoxGraphsEvent([])
                    )
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
                        if (prev_command1 == None) or (
                                prev_command1 != self.current_command1
                        ):
                            self.graph_x_vals1 = np.array([])
                            self.graph_y_vals1 = np.array([])
                            # self.graph_x_vals1 = []
                            # self.graph_y_vals1 = []
                            self.graph_counter1 = 0
                            wx.PostEvent(
                                self._notify_window,
                                GraphsValueEvent(
                                    [0, 0, self.current_command1.command]
                                ),
                            )
                            wx.PostEvent(
                                self._notify_window,
                                GraphsValueEvent(
                                    [0, 1, self.current_command1.desc]
                                ),
                            )
                        else:
                            response = self.obd.connection.query(
                                self.current_command1
                            )
                            if response.value is None:
                                self._reconnect()
                                continue
                            # if s.value == None:
                            #    print("s.value is None!")
                            #    raise AttributeError
                            self.graph_x_vals1 = np.append(
                                self.graph_x_vals1, self.graph_counter1
                            )
                            try:
                                self.graph_y_vals1 = np.append(
                                    self.graph_y_vals1, float(response.value.magnitude)
                                )
                            except AttributeError:
                                self.graph_y_vals1 = np.append(
                                    self.graph_y_vals1, float(0)
                                )
                            # self.graph_x_vals1.append(self.graph_counter1)
                            # self.graph_y_vals1.append(float(s.value.magnitude))
                            if len(self.graph_x_vals1) > 200:
                                self.graph_x_vals1 = np.delete(
                                    self.graph_x_vals1, (0)
                                )
                                self.graph_y_vals1 = np.delete(
                                    self.graph_y_vals1, (0)
                                )
                                # self.graph_x_vals1.pop(0)
                                # self.graph_y_vals1.pop(0)

                            self.graph_counter1 = self.graph_counter1 + 1
                            prev_command1 = self.current_command1
                            self.graph_dirty1 = True
                            # wx.PostEvent(self._notify_window, GraphEvent(self.current_command1))
                            if response.value == None:
                                wx.PostEvent(
                                    self._notify_window,
                                    GraphsValueEvent([0, 2, str(0)]),
                                )
                                self.unit1 = "unit"
                            else:
                                wx.PostEvent(
                                    self._notify_window,
                                    GraphsValueEvent([0, 2, str(response.value)]),
                                )
                                try:
                                    self.unit1 = str(response.value).split(" ")[1]
                                except IndexError:
                                    self.unit1 = "unit"
                    else:
                        self.graph_x_vals1 = np.array([])
                        self.graph_y_vals1 = np.array([])
                        self.graph_counter1 = 0

                    if self.current_command2:
                        if not prev_command2 or (
                                prev_command2 != self.current_command2
                        ):
                            self.graph_x_vals2 = np.array([])
                            self.graph_y_vals2 = np.array([])
                            # self.graph_x_vals2 = []
                            # self.graph_y_vals2 = []
                            self.graph_counter2 = 0
                            wx.PostEvent(
                                self._notify_window,
                                GraphsValueEvent(
                                    [1, 0, self.current_command2.command]
                                ),
                            )
                            wx.PostEvent(
                                self._notify_window,
                                GraphsValueEvent(
                                    [1, 1, self.current_command2.desc]
                                ),
                            )
                        else:
                            response = self.obd.connection.query(
                                self.current_command2
                            )
                            if response.value is None:
                                self._reconnect()
                                continue
                            # if s.value == None:
                            #    print("s.value is None!")
                            #    raise AttributeError
                            self.graph_x_vals2 = np.append(
                                self.graph_x_vals2, self.graph_counter2
                            )
                            try:
                                self.graph_y_vals2 = np.append(
                                    self.graph_y_vals2, float(response.value.magnitude)
                                )
                            except AttributeError:
                                self.graph_y_vals2 = np.append(
                                    self.graph_y_vals2, float(0)
                                )
                            # self.graph_x_vals2.append(self.graph_counter2)
                            # self.graph_y_vals2.append(float(s.value.magnitude))
                            if len(self.graph_x_vals2) > 200:
                                self.graph_x_vals2 = np.delete(
                                    self.graph_x_vals2, (0)
                                )
                                self.graph_y_vals2 = np.delete(
                                    self.graph_y_vals2, (0)
                                )
                                # self.graph_x_vals2.pop(0)
                                # self.graph_y_vals2.pop(0)

                            self.graph_counter2 = self.graph_counter2 + 1
                            prev_command2 = self.current_command2
                            self.graph_dirty2 = True
                            # wx.PostEvent(self._notify_window, GraphEvent(self.current_command2))
                            if response.value == None:
                                wx.PostEvent(
                                    self._notify_window,
                                    GraphsValueEvent([1, 2, str(0)]),
                                )
                                self.unit2 = "unit"
                            else:
                                wx.PostEvent(
                                    self._notify_window,
                                    GraphsValueEvent([1, 2, str(response.value)]),
                                )
                                try:
                                    self.unit2 = str(response.value).split(" ")[1]
                                except IndexError:
                                    self.unit2 = "unit"
                    else:
                        self.graph_x_vals2 = np.array([])
                        self.graph_y_vals2 = np.array([])
                        self.graph_counter2 = 0

                    if self.current_command3:
                        if not prev_command3 or (
                                prev_command3 != self.current_command3
                        ):
                            self.graph_x_vals3 = np.array([])
                            self.graph_y_vals3 = np.array([])
                            # self.graph_x_vals3 = []
                            # self.graph_y_vals3 = []
                            self.graph_counter3 = 0
                            wx.PostEvent(
                                self._notify_window,
                                GraphsValueEvent(
                                    [2, 0, self.current_command3.command]
                                ),
                            )
                            wx.PostEvent(
                                self._notify_window,
                                GraphsValueEvent(
                                    [2, 1, self.current_command3.desc]
                                ),
                            )
                        else:
                            response = self.obd.connection.query(
                                self.current_command3
                            )
                            if response.value is None:
                                self._reconnect()
                                continue
                            # if s.value == None:
                            #    print("s.value is None!")
                            #    raise AttributeError
                            self.graph_x_vals3 = np.append(
                                self.graph_x_vals3, self.graph_counter3
                            )
                            try:
                                self.graph_y_vals3 = np.append(
                                    self.graph_y_vals3, float(response.value.magnitude)
                                )
                            except AttributeError:
                                self.graph_y_vals3 = np.append(
                                    self.graph_y_vals3, float(0)
                                )
                            # self.graph_x_vals3.append(self.graph_counter3)
                            # self.graph_y_vals3.append(float(s.value.magnitude))
                            if len(self.graph_x_vals3) > 200:
                                self.graph_x_vals3 = np.delete(
                                    self.graph_x_vals3, (0)
                                )
                                self.graph_y_vals3 = np.delete(
                                    self.graph_y_vals3, (0)
                                )
                                # self.graph_x_vals3.pop(0)
                                # self.graph_y_vals3.pop(0)

                            self.graph_counter3 = self.graph_counter3 + 1
                            prev_command3 = self.current_command3
                            self.graph_dirty3 = True
                            # wx.PostEvent(self._notify_window, GraphEvent(self.current_command3))
                            if response.value == None:
                                wx.PostEvent(
                                    self._notify_window,
                                    GraphsValueEvent([2, 2, str(0)]),
                                )
                                self.unit3 = "unit"
                            else:
                                wx.PostEvent(
                                    self._notify_window,
                                    GraphsValueEvent([2, 2, str(response.value)]),
                                )
                                try:
                                    self.unit3 = str(response.value).split(" ")[1]
                                except IndexError:
                                    self.unit3 = "unit"
                    else:
                        self.graph_x_vals3 = np.array([])
                        self.graph_y_vals3 = np.array([])
                        self.graph_counter3 = 0

                    if self.current_command4:
                        if not prev_command4 or (
                                prev_command4 != self.current_command4
                        ):
                            self.graph_x_vals4 = np.array([])
                            self.graph_y_vals4 = np.array([])
                            # self.graph_x_vals4 = []
                            # self.graph_y_vals4 = []
                            self.graph_counter4 = 0
                            wx.PostEvent(
                                self._notify_window,
                                GraphsValueEvent(
                                    [3, 0, self.current_command4.command]
                                ),
                            )
                            wx.PostEvent(
                                self._notify_window,
                                GraphsValueEvent(
                                    [3, 1, self.current_command4.desc]
                                ),
                            )
                        else:
                            response = self.obd.connection.query(
                                self.current_command4
                            )
                            if response.value is None:
                                self._reconnect()
                                continue
                            # if s.value == None:
                            #    print("s.value is None!")
                            #    raise AttributeError
                            self.graph_x_vals4 = np.append(
                                self.graph_x_vals4, self.graph_counter4
                            )

                            try:
                                self.graph_y_vals4 = np.append(
                                    self.graph_y_vals4, float(response.value.magnitude)
                                )
                            except AttributeError:
                                self.graph_y_vals4 = np.append(
                                    self.graph_y_vals4, float(0)
                                )

                            # self.graph_x_vals4.append(self.graph_counter4)
                            # self.graph_y_vals4.append(float(s.value.magnitude))
                            if len(self.graph_x_vals4) > 200:
                                self.graph_x_vals4 = np.delete(
                                    self.graph_x_vals4, (0)
                                )
                                self.graph_y_vals4 = np.delete(
                                    self.graph_y_vals4, (0)
                                )
                                # self.graph_x_vals4.pop(0)
                                # self.graph_y_vals4.pop(0)

                            self.graph_counter4 = self.graph_counter4 + 1
                            prev_command4 = self.current_command4
                            self.graph_dirty4 = True
                            # wx.PostEvent(self._notify_window, GraphEvent(self.current_command4))
                            if response.value is None:
                                wx.PostEvent(
                                    self._notify_window,
                                    GraphsValueEvent([3, 2, str(0)]),
                                )
                                self.unit4 = "unit"
                            else:
                                wx.PostEvent(
                                    self._notify_window,
                                    GraphsValueEvent([3, 2, str(response.value)]),
                                )
                                try:
                                    self.unit4 = str(response.value).split(" ")[1]
                                except IndexError:
                                    self.unit4 = "unit"
                    else:
                        self.graph_x_vals4 = np.array([])
                        self.graph_y_vals4 = np.array([])
                        self.graph_counter4 = 0

                    if self.first_time_graphs_plot:
                        self.unit1 = "unit"
                        self.unit2 = "unit"
                        self.unit3 = "unit"
                        self.unit4 = "unit"
                    if not self.current_command1:
                        desc1 = "None"
                    else:
                        desc1 = self.current_command1.desc
                    if not self.current_command2:
                        desc2 = "None"
                    else:
                        desc2 = self.current_command2.desc
                    if not self.current_command3:
                        desc3 = "None"
                    else:
                        desc3 = self.current_command3.desc
                    if not self.current_command4:
                        desc4 = "None"
                    else:
                        desc4 = self.current_command4.desc
                    wx.PostEvent(
                        self._notify_window,
                        GraphsEvent(
                            [
                                (
                                    self.graph_x_vals1,
                                    self.graph_y_vals1,
                                    self.unit1,
                                    desc1,
                                    self.graph_counter1,
                                ),
                                (
                                    self.graph_x_vals2,
                                    self.graph_y_vals2,
                                    self.unit2,
                                    desc2,
                                    self.graph_counter2,
                                ),
                                (
                                    self.graph_x_vals3,
                                    self.graph_y_vals3,
                                    self.unit3,
                                    desc3,
                                    self.graph_counter3,
                                ),
                                (
                                    self.graph_x_vals4,
                                    self.graph_y_vals4,
                                    self.unit4,
                                    desc4,
                                    self.graph_counter4,
                                ),
                                (self.first_time_graphs_plot),
                            ]
                        ),
                    )
                    self.first_time_graphs_plot = False
                    # time.sleep(0.2)

            elif active_tab == AppTab.TRACE:
                response = self.obd.connection.query(obd.commands.RPM)
                if response.value is None:
                    self._reconnect()
                    continue
            time_end = datetime.datetime.now()
            first_time = False
        self.state = "finished"
        print("state is finished")
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
        self.obd.connection.close()
        # self._notify_window.ThreadControl = 666

        # try:  # if stop is called before any connection port is not defined (and not connected )
        #     self.obd.connection.close()
        # except Exception as e:
        #     print(e)

        # if self.port != None: #if stop is called before any connection port is not defined (and not connected )
        #  self.port.close()
        wx.PostEvent(self._notify_window, StatusEvent([0, 1, "Disconnected"]))
        wx.PostEvent(self._notify_window, StatusEvent([1, 1, "----"]))
        wx.PostEvent(self._notify_window, StatusEvent([2, 1, "----"]))
        wx.PostEvent(self._notify_window, StatusEvent([3, 1, "----"]))
        wx.PostEvent(self._notify_window, StatusEvent([4, 1, "----"]))
        wx.PostEvent(self._notify_window, StatusEvent([5, 1, "----"]))
        wx.PostEvent(self._notify_window, CloseEvent([]))
        print("Sensor producer has stopped.")

    def _init_all_graphs(self):
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

    def _reconnect(self):
        self._init_all_graphs()
        if not self.init_communication():
            self._notify_window.ThreadControl = 666

    def _emit_test_events(self):
        response = self.obd.connection.query(obd.commands.RPM)
        if response.value is None:
            self._reconnect()
            return
        response = self.obd.connection.query(obd.commands[1][1])
        if response.value is None:
        #     NOT SUPPORTED, so do nothing
            return

        if response.value.MISFIRE_MONITORING.available:
            wx.PostEvent(
                self._notify_window, TestEvent([0, 1, "Available"])
            )
            if response.value.MISFIRE_MONITORING.complete:
                wx.PostEvent(
                    self._notify_window, TestEvent([0, 2, "Complete"])
                )
            else:
                wx.PostEvent(
                    self._notify_window, TestEvent([0, 2, "Incomplete"])
                )
        if response.value.FUEL_SYSTEM_MONITORING.available:
            wx.PostEvent(
                self._notify_window, TestEvent([1, 1, "Available"])
            )
            if response.value.FUEL_SYSTEM_MONITORING.complete:
                wx.PostEvent(
                    self._notify_window, TestEvent([1, 2, "Complete"])
                )
            else:
                wx.PostEvent(
                    self._notify_window, TestEvent([1, 2, "Incomplete"])
                )
        if response.value.COMPONENT_MONITORING.available:
            wx.PostEvent(
                self._notify_window, TestEvent([2, 1, "Available"])
            )
            if response.value.COMPONENT_MONITORING.complete:
                wx.PostEvent(
                    self._notify_window, TestEvent([2, 2, "Complete"])
                )
            else:
                wx.PostEvent(
                    self._notify_window, TestEvent([2, 2, "Incomplete"])
                )

        if response.value.CATALYST_MONITORING.available:
            wx.PostEvent(
                self._notify_window, TestEvent([3, 1, "Available"])
            )
            if response.value.CATALYST_MONITORING.complete:
                wx.PostEvent(
                    self._notify_window, TestEvent([3, 2, "Complete"])
                )
            else:
                wx.PostEvent(
                    self._notify_window, TestEvent([3, 2, "Incomplete"])
                )

        if response.value.HEATED_CATALYST_MONITORING.available:
            wx.PostEvent(
                self._notify_window, TestEvent([4, 1, "Available"])
            )
            if response.value.HEATED_CATALYST_MONITORING.complete:
                wx.PostEvent(
                    self._notify_window, TestEvent([4, 2, "Complete"])
                )
            else:
                wx.PostEvent(
                    self._notify_window, TestEvent([4, 2, "Incomplete"])
                )

        if response.value.EVAPORATIVE_SYSTEM_MONITORING.available:
            wx.PostEvent(
                self._notify_window, TestEvent([5, 1, "Available"])
            )
            if response.value.EVAPORATIVE_SYSTEM_MONITORING.complete:
                wx.PostEvent(
                    self._notify_window, TestEvent([5, 2, "Complete"])
                )
            else:
                wx.PostEvent(
                    self._notify_window, TestEvent([5, 2, "Incomplete"])
                )

        if response.value.SECONDARY_AIR_SYSTEM_MONITORING.available:
            wx.PostEvent(
                self._notify_window, TestEvent([6, 1, "Available"])
            )
            if response.value.SECONDARY_AIR_SYSTEM_MONITORING.complete:
                wx.PostEvent(
                    self._notify_window, TestEvent([6, 2, "Complete"])
                )
            else:
                wx.PostEvent(
                    self._notify_window, TestEvent([6, 2, "Incomplete"])
                )

        if response.value.OXYGEN_SENSOR_MONITORING.available:
            wx.PostEvent(
                self._notify_window, TestEvent([7, 1, "Available"])
            )
            if response.value.OXYGEN_SENSOR_MONITORING.complete:
                wx.PostEvent(
                    self._notify_window, TestEvent([7, 2, "Complete"])
                )
            else:
                wx.PostEvent(
                    self._notify_window, TestEvent([7, 2, "Incomplete"])
                )

        if response.value.OXYGEN_SENSOR_HEATER_MONITORING.available:
            wx.PostEvent(
                self._notify_window, TestEvent([8, 1, "Available"])
            )
            if response.value.OXYGEN_SENSOR_HEATER_MONITORING.complete:
                wx.PostEvent(
                    self._notify_window, TestEvent([8, 2, "Complete"])
                )
            else:
                wx.PostEvent(
                    self._notify_window, TestEvent([8, 2, "Incomplete"])
                )

        if response.value.EGR_VVT_SYSTEM_MONITORING.available:
            wx.PostEvent(
                self._notify_window, TestEvent([9, 1, "Available"])
            )
            if response.value.EGR_VVT_SYSTEM_MONITORING.complete:
                wx.PostEvent(
                    self._notify_window, TestEvent([9, 2, "Complete"])
                )
            else:
                wx.PostEvent(
                    self._notify_window, TestEvent([9, 2, "Incomplete"])
                )

        if response.value.NMHC_CATALYST_MONITORING.available:
            wx.PostEvent(
                self._notify_window, TestEvent([10, 1, "Available"])
            )
            if response.value.NMHC_CATALYST_MONITORING.complete:
                wx.PostEvent(
                    self._notify_window, TestEvent([10, 2, "Complete"])
                )
            else:
                wx.PostEvent(
                    self._notify_window,
                    TestEvent([10, 2, "Incomplete"]),
                )

        if response.value.NOX_SCR_AFTERTREATMENT_MONITORING.available:
            wx.PostEvent(
                self._notify_window, TestEvent([11, 1, "Available"])
            )
            if response.value.NOX_SCR_AFTERTREATMENT_MONITORING.complete:
                wx.PostEvent(
                    self._notify_window, TestEvent([11, 2, "Complete"])
                )
            else:
                wx.PostEvent(
                    self._notify_window,
                    TestEvent([11, 2, "Incomplete"]),
                )

        if response.value.BOOST_PRESSURE_MONITORING.available:
            wx.PostEvent(
                self._notify_window, TestEvent([12, 1, "Available"])
            )
            if response.value.BOOST_PRESSURE_MONITORING.complete:
                wx.PostEvent(
                    self._notify_window, TestEvent([12, 2, "Complete"])
                )
            else:
                wx.PostEvent(
                    self._notify_window,
                    TestEvent([12, 2, "Incomplete"]),
                )

        if response.value.EXHAUST_GAS_SENSOR_MONITORING.available:
            wx.PostEvent(
                self._notify_window, TestEvent([13, 1, "Available"])
            )
            if response.value.EXHAUST_GAS_SENSOR_MONITORING.complete:
                wx.PostEvent(
                    self._notify_window, TestEvent([13, 2, "Complete"])
                )
            else:
                wx.PostEvent(
                    self._notify_window,
                    TestEvent([13, 2, "Incomplete"]),
                )

        if response.value.PM_FILTER_MONITORING.available:
            wx.PostEvent(
                self._notify_window, TestEvent([14, 1, "Available"])
            )
            if response.value.PM_FILTER_MONITORING.complete:
                wx.PostEvent(
                    self._notify_window, TestEvent([14, 2, "Complete"])
                )
            else:
                wx.PostEvent(
                    self._notify_window,
                    TestEvent([14, 2, "Incomplete"]),
                )

        response = self.obd.connection.query(
            obd.commands.MONITOR_MISFIRE_CYLINDER_1
        )
        if response.value:
            result = response.value.MISFIRE_COUNT
            wx.PostEvent(
                self._notify_window, TestEvent([15, 2, str(result)])
            )
        response = self.obd.connection.query(
            obd.commands.MONITOR_MISFIRE_CYLINDER_2
        )
        if response.value:
            result = response.value.MISFIRE_COUNT
            wx.PostEvent(
                self._notify_window, TestEvent([16, 2, str(result)])
            )
        response = self.obd.connection.query(
            obd.commands.MONITOR_MISFIRE_CYLINDER_3
        )
        if response.value:
            result = response.value.MISFIRE_COUNT
            wx.PostEvent(
                self._notify_window, TestEvent([17, 2, str(result)])
            )
        response = self.obd.connection.query(
            obd.commands.MONITOR_MISFIRE_CYLINDER_4
        )
        if response.value:
            result = response.value.MISFIRE_COUNT
            wx.PostEvent(
                self._notify_window, TestEvent([18, 2, str(result)])
            )
        response = self.obd.connection.query(
            obd.commands.MONITOR_MISFIRE_CYLINDER_5
        )
        if response.value:
            result = response.value.MISFIRE_COUNT
            wx.PostEvent(
                self._notify_window, TestEvent([19, 2, str(result)])
            )
        response = self.obd.connection.query(
            obd.commands.MONITOR_MISFIRE_CYLINDER_6
        )
        if response.value:
            result = response.value.MISFIRE_COUNT
            wx.PostEvent(
                self._notify_window, TestEvent([20, 2, str(result)])
            )
        response = self.obd.connection.query(
            obd.commands.MONITOR_MISFIRE_CYLINDER_7
        )
        if response.value:
            result = response.value.MISFIRE_COUNT
            wx.PostEvent(
                self._notify_window, TestEvent([21, 2, str(result)])
            )
        response = self.obd.connection.query(
            obd.commands.MONITOR_MISFIRE_CYLINDER_8
        )
        if response.value:
            result = response.value.MISFIRE_COUNT
            wx.PostEvent(
                self._notify_window, TestEvent([22, 2, str(result)])
            )
        response = self.obd.connection.query(
            obd.commands.MONITOR_MISFIRE_CYLINDER_9
        )
        if response.value:
            result = response.value.MISFIRE_COUNT
            wx.PostEvent(
                self._notify_window, TestEvent([23, 2, str(result)])
            )
        response = self.obd.connection.query(
            obd.commands.MONITOR_MISFIRE_CYLINDER_10
        )
        if response.value:
            result = response.value.MISFIRE_COUNT
            wx.PostEvent(
                self._notify_window, TestEvent([24, 2, str(result)])
            )
        response = self.obd.connection.query(
            obd.commands.MONITOR_MISFIRE_CYLINDER_11
        )
        if response.value:
            result = response.value.MISFIRE_COUNT
            wx.PostEvent(
                self._notify_window, TestEvent([25, 2, str(result)])
            )
        response = self.obd.connection.query(
            obd.commands.MONITOR_MISFIRE_CYLINDER_12
        )
        if response.value:
            result = response.value.MISFIRE_COUNT
            wx.PostEvent(
                self._notify_window, TestEvent([26, 2, str(result)])
            )
