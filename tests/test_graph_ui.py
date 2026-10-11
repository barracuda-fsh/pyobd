import unittest

import wx

from about_ui import ABOUT_DIALOG_TEXT
from app_events import GraphEvent, GraphValueEvent
from graph_ui import GraphUIMixin
from sensor_worker import SensorProducer


class FakeCommand:
    def __init__(self, key, description):
        self.command = key
        self.desc = description


class FakeListControl:
    def __init__(self, selected=()):
        self.rows = []
        self.selected = set(selected)

    def GetFirstSelected(self):
        return min(self.selected) if self.selected else wx.NOT_FOUND

    def GetNextSelected(self, current):
        remaining = sorted(index for index in self.selected if index > current)
        return remaining[0] if remaining else wx.NOT_FOUND

    def GetItemCount(self):
        return len(self.rows)

    def DeleteAllItems(self):
        self.rows = []

    def InsertItem(self, index, value):
        self.rows.insert(index, [value, "", ""])

    def SetItem(self, row, column, value):
        self.rows[row][column] = value

    def Select(self, index, on=True):
        if on:
            self.selected.add(index)
        else:
            self.selected.discard(index)

    def GetItemState(self, index, _state):
        return wx.LIST_STATE_SELECTED if index in self.selected else 0

    def IsSelected(self, index):
        return index in self.selected


class GraphHarness(GraphUIMixin):
    def __init__(self, commands, selected=()):
        self.selected_graph_commands = commands
        self.isolated_graph_command_key = None
        self.graph_individual_mode = False
        self.graph_list_ctrl = FakeListControl(selected)
        self.graph_view_button = FakeButton()
        for index, command in enumerate(commands):
            self.graph_list_ctrl.InsertItem(index, command.command.decode())
            self.graph_list_ctrl.SetItem(index, 1, command.desc)

    def _rebuild_graph_canvases(self):
        pass


class Event:
    def __init__(self, data):
        self.data = data


class FakeButton:
    def SetLabel(self, label):
        self.label = label

    def SetToolTip(self, tooltip):
        self.tooltip = tooltip


class GraphUITests(unittest.TestCase):
    def test_graph_starts_combined(self):
        graph = GraphHarness([FakeCommand(b"010C", "RPM")])
        self.assertFalse(graph.graph_individual_mode)
        self.assertIsNone(graph.isolated_graph_command_key)

    def test_remove_selected_removes_multiple_rows(self):
        commands = [
            FakeCommand(b"010C", "RPM"),
            FakeCommand(b"010D", "Speed"),
            FakeCommand(b"0105", "Coolant"),
        ]
        graph = GraphHarness(commands, selected=(0, 2))
        graph.graph_streaming_enabled = True
        graph.OnRemoveGraphPid(None)
        self.assertEqual([command.command for command in graph.selected_graph_commands], [b"010D"])

    def test_add_pid_remains_available_during_playback(self):
        rpm = FakeCommand(b"010C", "RPM")
        speed = FakeCommand(b"010D", "Speed")
        graph = GraphHarness([rpm])
        graph.graph_streaming_enabled = True
        graph.graph_command_catalog = [rpm, speed]
        self.assertEqual(graph._add_graph_commands_by_catalog_indices([1]), 1)
        self.assertEqual([command.command for command in graph.selected_graph_commands], [b"010C", b"010D"])

    def test_clicking_pid_toggles_selection_without_changing_view(self):
        commands = [FakeCommand(b"010C", "RPM"), FakeCommand(b"010D", "Speed")]
        graph = GraphHarness(commands)
        graph._toggle_graph_row_selection(1)
        self.assertTrue(graph.graph_list_ctrl.IsSelected(1))
        graph._toggle_graph_row_selection(1)
        self.assertFalse(graph.graph_list_ctrl.IsSelected(1))
        self.assertFalse(graph.graph_individual_mode)

    def test_context_action_isolates_and_restores_graph(self):
        commands = [FakeCommand(b"010C", "RPM"), FakeCommand(b"010D", "Speed")]
        graph = GraphHarness(commands)
        graph.graph_individual_mode = True
        graph._isolate_graph_index(1)
        self.assertEqual(graph.isolated_graph_command_key, b"010D")
        self.assertFalse(graph.graph_individual_mode)
        graph._show_all_graphs()
        self.assertIsNone(graph.isolated_graph_command_key)

    def test_value_updates_follow_pid_after_rows_change(self):
        commands = [FakeCommand(b"010C", "RPM"), FakeCommand(b"010D", "Speed")]
        graph = GraphHarness(commands)
        graph.OnGraphValue(Event([b"010D", 2, "42 mph"]))
        self.assertEqual(graph.graph_list_ctrl.rows[1][2], "42 mph")
        self.assertEqual(graph.graph_list_ctrl.rows[0][2], "")

    def test_about_dialog_credits_farebrothers(self):
        self.assertIn("(C) 2025 FareBrothers, LLC", ABOUT_DIALOG_TEXT)
        self.assertIn("DodgeOBD", ABOUT_DIALOG_TEXT)
        self.assertIn("NissanOBD", ABOUT_DIALOG_TEXT)
        self.assertIn("website hosting and game server hosting", ABOUT_DIALOG_TEXT)
        self.assertIn("Operating since 2023", ABOUT_DIALOG_TEXT)

    def test_worker_and_ui_share_graph_event_types(self):
        self.assertTrue(issubclass(GraphEvent, wx.PyEvent))
        self.assertTrue(issubclass(GraphValueEvent, wx.PyEvent))
        self.assertTrue(issubclass(SensorProducer, object))

    def test_demo_polling_is_faster_than_adapter_polling(self):
        self.assertLess(
            SensorProducer._target_loop_interval(True),
            SensorProducer._target_loop_interval(False),
        )

    def test_isolation_only_polls_the_visible_pid(self):
        commands = [FakeCommand(b"010C", "RPM"), FakeCommand(b"010D", "Speed")]
        selected = SensorProducer._graph_commands_to_poll(commands, b"010D")
        self.assertEqual([command.command for command in selected], [b"010D"])


if __name__ == "__main__":
    unittest.main()
