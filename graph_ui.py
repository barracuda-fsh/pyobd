"""Graph page UI and interaction logic for pyOBD."""

import wx
from wx.lib import plot as wxplot

import obd


GRAPH_COLOURS = ["blue", "red", "green", "orange", "purple", "brown", "black", "cyan"]


class GraphUIMixin:
    """Owns graph selection, controls, layout, and rendering."""

    def _build_graph_command_catalog(self):
        excluded = {b"0100", b"0101", b"0120", b"0140", b"0103", b"0102", b"011C", b"0113", b"0141", b"0151"}
        self.graph_command_catalog = [
            command for command in obd.commands[1]
            if command and command.command not in excluded
        ]
        self.graph_command_catalog.append(obd.commands.ELM_VOLTAGE)
        self.graph_command_labels = [
            f"{command.command.decode(errors='ignore')} - {command.desc}"
            for command in self.graph_command_catalog
        ]
        self.selected_graph_commands = []
        self.isolated_graph_command_key = None

    def _set_graph_streaming(self, enabled):
        self.graph_streaming_enabled = bool(enabled)
        if hasattr(self, "graph_play_button"):
            self.graph_play_button.SetLabel("Stop" if self.graph_streaming_enabled else "Play")

        if not self.graph_streaming_enabled:
            for row in range(self.graph_list_ctrl.GetItemCount()):
                self.graph_list_ctrl.SetItem(row, 2, "---")
            self._clear_graph_canvases()

    def OnToggleGraphStreaming(self, _event):
        if not self.graph_streaming_enabled:
            if not self.selected_graph_commands:
                wx.MessageBox(
                    "Add at least one PID before starting the graph.",
                    "Graph",
                    wx.OK | wx.ICON_INFORMATION,
                )
                return
            self._set_graph_streaming(True)
        else:
            self._set_graph_streaming(False)

    def _selected_graph_keys(self):
        keys = []
        selected = self.graph_list_ctrl.GetFirstSelected()
        while selected != wx.NOT_FOUND:
            if 0 <= selected < len(self.selected_graph_commands):
                keys.append(self.selected_graph_commands[selected].command)
            selected = self.graph_list_ctrl.GetNextSelected(selected)
        return keys

    def _refresh_graph_selection_ui(self):
        selected_keys = set(self._selected_graph_keys()) if hasattr(self, "graph_list_ctrl") else set()
        self.graph_list_ctrl.DeleteAllItems()
        for index, command in enumerate(self.selected_graph_commands):
            self.graph_list_ctrl.InsertItem(index, command.command.decode(errors="ignore"))
            self.graph_list_ctrl.SetItem(index, 1, command.desc)
            self.graph_list_ctrl.SetItem(index, 2, "---")
            if command.command in selected_keys:
                self.graph_list_ctrl.Select(index)

        valid_keys = {command.command for command in self.selected_graph_commands}
        if self.isolated_graph_command_key not in valid_keys:
            self.isolated_graph_command_key = None
        self._rebuild_graph_canvases()

    def _add_graph_commands_by_catalog_indices(self, catalog_indices):
        added_count = 0
        for index in catalog_indices:
            if not 0 <= index < len(self.graph_command_catalog):
                continue
            command = self.graph_command_catalog[index]
            if command not in self.selected_graph_commands:
                self.selected_graph_commands.append(command)
                added_count += 1

        if added_count:
            self._refresh_graph_selection_ui()
        return added_count

    def _show_add_graph_pid_dialog(self):
        dialog = wx.Dialog(self.frame, -1, "Add PID", size=(680, 540))
        root = wx.BoxSizer(wx.VERTICAL)
        search_ctrl = wx.TextCtrl(dialog)
        list_box = wx.ListBox(dialog, style=wx.LB_EXTENDED)
        add_button = wx.Button(dialog, label="Add Selected")
        done_button = wx.Button(dialog, wx.ID_CANCEL, "Done")

        button_row = wx.BoxSizer(wx.HORIZONTAL)
        button_row.Add(add_button)
        button_row.AddStretchSpacer()
        button_row.Add(done_button)

        root.Add(wx.StaticText(dialog, label="Search (contains):"), 0, wx.LEFT | wx.RIGHT | wx.TOP, 10)
        root.Add(search_ctrl, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 6)
        root.Add(list_box, 1, wx.EXPAND | wx.ALL, 10)
        root.Add(wx.StaticText(dialog, label="Tip: use Ctrl/Shift to select multiple PIDs."), 0, wx.LEFT | wx.RIGHT, 10)
        root.Add(button_row, 0, wx.EXPAND | wx.ALL, 10)
        dialog.SetSizer(root)

        filtered_indices = []
        selected_catalog_indices = set()

        def current_catalog_indices():
            return [
                filtered_indices[index]
                for index in list_box.GetSelections()
                if 0 <= index < len(filtered_indices)
            ]

        def update_filter(_event=None):
            selected_catalog_indices.update(current_catalog_indices())
            query = search_ctrl.GetValue().strip().lower()
            list_box.Clear()
            filtered_indices.clear()
            for index, label in enumerate(self.graph_command_labels):
                if not query or query in label.lower():
                    filtered_indices.append(index)
                    list_box.Append(label)
            for view_index, catalog_index in enumerate(filtered_indices):
                if catalog_index in selected_catalog_indices:
                    list_box.SetSelection(view_index)

        def add_selected(_event=None):
            selected_catalog_indices.update(current_catalog_indices())
            if not selected_catalog_indices:
                wx.MessageBox("Select at least one PID to add.", "Graph", wx.OK | wx.ICON_INFORMATION)
                return
            self._add_graph_commands_by_catalog_indices(sorted(selected_catalog_indices))
            selected_catalog_indices.clear()
            update_filter()
            search_ctrl.SetFocus()

        search_ctrl.Bind(wx.EVT_TEXT, update_filter)
        add_button.Bind(wx.EVT_BUTTON, add_selected)
        list_box.Bind(wx.EVT_LISTBOX_DCLICK, add_selected)
        update_filter()
        search_ctrl.SetFocus()
        dialog.ShowModal()
        dialog.Destroy()

    def OnAddGraphPid(self, _event):
        self._show_add_graph_pid_dialog()

    def OnRemoveGraphPid(self, _event):
        selected_indices = []
        selected = self.graph_list_ctrl.GetFirstSelected()
        while selected != wx.NOT_FOUND:
            selected_indices.append(selected)
            selected = self.graph_list_ctrl.GetNextSelected(selected)

        if not selected_indices:
            return

        self._clear_graph_selection()
        for index in reversed(selected_indices):
            if 0 <= index < len(self.selected_graph_commands):
                del self.selected_graph_commands[index]
        self._refresh_graph_selection_ui()

    def _toggle_graph_row_selection(self, index):
        if not 0 <= index < self.graph_list_ctrl.GetItemCount():
            return
        is_selected = bool(self.graph_list_ctrl.GetItemState(index, wx.LIST_STATE_SELECTED))
        self.graph_list_ctrl.Select(index, not is_selected)

    def OnGraphListClick(self, event):
        index, _flags = self.graph_list_ctrl.HitTest(event.GetPosition())
        if index == wx.NOT_FOUND:
            event.Skip()
            return
        # Consume the native click so choosing one row does not clear other rows.
        self._toggle_graph_row_selection(index)

    def OnGraphViewToggle(self, _event):
        self.graph_individual_mode = not self.graph_individual_mode
        self.isolated_graph_command_key = None
        self._update_graph_view_button()
        self._rebuild_graph_canvases()

    def _update_graph_view_button(self):
        if self.graph_individual_mode:
            self.graph_view_button.SetLabel("≋")
            self.graph_view_button.SetToolTip("Show all PIDs on one combined graph")
        else:
            self.graph_view_button.SetLabel("▦")
            self.graph_view_button.SetToolTip("Show one graph for each PID")

    def _clear_graph_selection(self):
        for index in range(self.graph_list_ctrl.GetItemCount()):
            self.graph_list_ctrl.Select(index, False)

    def _isolate_graph_index(self, index):
        if not 0 <= index < len(self.selected_graph_commands):
            return
        self.isolated_graph_command_key = self.selected_graph_commands[index].command
        self.graph_individual_mode = False
        self._update_graph_view_button()
        self._rebuild_graph_canvases()

    def _show_all_graphs(self):
        self.isolated_graph_command_key = None
        self._rebuild_graph_canvases()

    def OnGraphListRightClick(self, event):
        index = event.GetIndex()
        if not 0 <= index < len(self.selected_graph_commands):
            return
        if not self.graph_list_ctrl.IsSelected(index):
            self.graph_list_ctrl.Select(index, True)

        menu = wx.Menu()
        isolate_item = menu.Append(wx.ID_ANY, "Isolate on Graph")
        show_all_item = menu.Append(wx.ID_ANY, "Show All on Graph")
        menu.AppendSeparator()
        delete_item = menu.Append(wx.ID_ANY, "Delete Selected")
        clear_item = menu.Append(wx.ID_ANY, "Clear Selection")

        self.graph_list_ctrl.Bind(wx.EVT_MENU, lambda _evt: self._isolate_graph_index(index), isolate_item)
        self.graph_list_ctrl.Bind(wx.EVT_MENU, lambda _evt: self._show_all_graphs(), show_all_item)
        self.graph_list_ctrl.Bind(wx.EVT_MENU, self.OnRemoveGraphPid, delete_item)
        self.graph_list_ctrl.Bind(wx.EVT_MENU, lambda _evt: self._clear_graph_selection(), clear_item)
        self.graph_list_ctrl.PopupMenu(menu)
        menu.Destroy()

    def _clear_graph_host(self):
        if not hasattr(self, "graph_plot_sizer"):
            return
        self.graph_plot_sizer.Clear(delete_windows=True)
        self.panel = None
        self.individual_graph_canvases = []

    def _new_plot_canvas(self, minimum_height=260):
        canvas = wxplot.PlotCanvas(self.graph_plot_host)
        canvas.SetMinSize((-1, minimum_height))
        self.graph_plot_sizer.Add(canvas, 1 if minimum_height >= 300 else 0, wx.EXPAND | wx.ALL, 4)
        return canvas

    def _rebuild_graph_canvases(self):
        if not hasattr(self, "graph_plot_host"):
            return
        self._clear_graph_host()
        if self.graph_individual_mode:
            for _command in self.selected_graph_commands:
                self.individual_graph_canvases.append(self._new_plot_canvas(220))
        else:
            self.panel = self._new_plot_canvas(320)
        self.graph_plot_host.SetScrollRate(10, 10)
        self.graph_plot_host.FitInside()
        self.graph_plot_host.Layout()

    def _clear_graph_canvases(self):
        canvases = list(getattr(self, "individual_graph_canvases", []))
        panel = getattr(self, "panel", None)
        if panel is not None:
            canvases.append(panel)
        for canvas in canvases:
            try:
                canvas.Clear()
            except Exception:
                pass

    def build_graph_page(self):
        self.graph_panel = wx.Panel(self.nb)
        root = wx.BoxSizer(wx.VERTICAL)
        toolbar = wx.BoxSizer(wx.HORIZONTAL)

        self.add_graph_pid_button = wx.Button(self.graph_panel, label="Add PID")
        self.remove_graph_pid_button = wx.Button(self.graph_panel, label="Remove Selected")
        self.graph_play_button = wx.Button(self.graph_panel, label="Play")
        self.graph_view_button = wx.Button(self.graph_panel, label="▦", size=(48, 42))
        self.graph_individual_mode = False
        view_font = self.graph_view_button.GetFont()
        view_font.SetPointSize(18)
        self.graph_view_button.SetFont(view_font)

        toolbar.Add(self.add_graph_pid_button, 0, wx.RIGHT, 8)
        toolbar.Add(self.remove_graph_pid_button, 0, wx.RIGHT, 8)
        toolbar.Add(self.graph_play_button, 0, wx.RIGHT, 16)
        toolbar.AddStretchSpacer(1)
        toolbar.Add(self.graph_view_button, 0, wx.ALIGN_CENTER_VERTICAL)

        self.graph_list_ctrl = self.MyListCtrl(
            self.graph_panel,
            wx.NewIdRef(),
            style=wx.LC_REPORT | wx.SUNKEN_BORDER | wx.LC_HRULES,
        )
        self.graph_list_ctrl.InsertColumn(0, "PID", width=80)
        self.graph_list_ctrl.InsertColumn(1, "Sensor", width=360)
        self.graph_list_ctrl.InsertColumn(2, "Value", width=180)
        self.graph_list_ctrl.SetMinSize((-1, 170))
        self.graph_list_ctrl.SetToolTip(
            "Click rows to select or unselect them. Right-click a row for graph actions."
        )

        self.graph_plot_host = wx.ScrolledWindow(self.graph_panel, style=wx.VSCROLL)
        self.graph_plot_sizer = wx.BoxSizer(wx.VERTICAL)
        self.graph_plot_host.SetSizer(self.graph_plot_sizer)
        self.individual_graph_canvases = []

        root.Add(toolbar, 0, wx.EXPAND | wx.ALL, 10)
        root.Add(self.graph_list_ctrl, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        root.Add(self.graph_plot_host, 1, wx.EXPAND | wx.ALL, 6)
        self.graph_panel.SetSizer(root)

        self._build_graph_command_catalog()
        self.graph_streaming_enabled = False
        self.add_graph_pid_button.Bind(wx.EVT_BUTTON, self.OnAddGraphPid)
        self.remove_graph_pid_button.Bind(wx.EVT_BUTTON, self.OnRemoveGraphPid)
        self.graph_play_button.Bind(wx.EVT_BUTTON, self.OnToggleGraphStreaming)
        self.graph_view_button.Bind(wx.EVT_BUTTON, self.OnGraphViewToggle)
        self.graph_list_ctrl.Bind(wx.EVT_LEFT_DOWN, self.OnGraphListClick)
        self.graph_list_ctrl.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnGraphListRightClick)

        self.nb.AddPage(self.graph_panel, "Graph")
        self._update_graph_view_button()
        self._rebuild_graph_canvases()
        self._set_graph_streaming(False)

    def _draw_series(self, canvas, series_list, title, graph_counter):
        lines = []
        for index, series in enumerate(series_list):
            xy_data = list(zip(series[0], series[1]))
            if len(xy_data) < 2:
                continue
            lines.append(wxplot.PolyLine(
                xy_data,
                colour=GRAPH_COLOURS[index % len(GRAPH_COLOURS)],
                width=2,
                style=wx.PENSTYLE_SOLID,
            ))
        if not lines:
            canvas.Clear()
            return
        graphics = wxplot.PlotGraphics(lines, title, "frame", "value")
        canvas.Draw(graphics, xAxis=(max(0, graph_counter - 450), max(1, graph_counter)))

    def OnGraph(self, event):
        plot_series, graph_counter, _first_time = event.data

        try:
            if self.graph_individual_mode:
                if len(self.individual_graph_canvases) != len(self.selected_graph_commands):
                    self._rebuild_graph_canvases()
                series_by_key = {series[4]: series for series in plot_series}
                for index, command in enumerate(self.selected_graph_commands):
                    series = series_by_key.get(command.command)
                    self._draw_series(
                        self.individual_graph_canvases[index],
                        [series] if series else [],
                        command.desc,
                        graph_counter,
                    )
                self.graph_plot_host.FitInside()
            else:
                visible_series = plot_series
                title = "Live Graphs"
                if self.isolated_graph_command_key is not None:
                    visible_series = [
                        series for series in plot_series
                        if series[4] == self.isolated_graph_command_key
                    ]
                    if visible_series:
                        title = visible_series[0][3]
                self._draw_series(self.panel, visible_series, title, graph_counter)
        except Exception:
            self._clear_graph_canvases()

    def OnGraphValue(self, event):
        command_key, column, value = event.data
        for row, command in enumerate(self.selected_graph_commands):
            if command.command == command_key:
                if row < self.graph_list_ctrl.GetItemCount():
                    self.graph_list_ctrl.SetItem(row, column, value)
                return

