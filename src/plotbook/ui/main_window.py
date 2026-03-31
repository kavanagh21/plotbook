"""Main application window."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import (
    QDockWidget,
    QFileDialog,
    QInputDialog,
    QMainWindow,
    QMenu,
    QMenuBar,
    QMessageBox,
    QSplitter,
    QToolBar,
    QComboBox,
    QLabel,
    QWidget,
    QVBoxLayout,
)

from plotbook.models.enums import (
    GRAPH_TYPES_FOR_FORMAT,
    GRAPH_TYPE_NAMES,
    EntryMode,
    GraphType,
    TableFormat,
)
from plotbook.models.project import Project, Sheet
from plotbook.rendering.export import export_figure
from plotbook.ui.format_panel import FormatPanel
from plotbook.ui.graph_canvas import GraphCanvas, PopOutGraphWindow
from plotbook.ui.graph_type_dialog import GraphTypeDialog
from plotbook.ui.navigator import Navigator
from plotbook.ui.new_sheet_dialog import NewSheetDialog
from plotbook.ui.spreadsheet import SpreadsheetWidget
from plotbook.viewmodels.graph_viewmodel import GraphViewModel
from plotbook.viewmodels.table_model import DataTableModel


class MainWindow(QMainWindow):
    """
    Main application window.

    Layout:
    ┌──────────────────────────────────────────────────┐
    │  Menu Bar  |  Toolbar                            │
    ├────────┬─────────────────────────────┬───────────┤
    │        │     Vertical Splitter       │           │
    │  Nav   │  ┌───────────────────────┐  │  Format   │
    │  Tree  │  │   Spreadsheet         │  │  Panel    │
    │        │  ├───────────────────────┤  │  (Dock)   │
    │        │  │   Graph Canvas        │  │           │
    │        │  └───────────────────────┘  │           │
    ├────────┴─────────────────────────────┴───────────┤
    │  Status Bar                                      │
    └──────────────────────────────────────────────────┘
    """

    def __init__(self, project: Project, parent=None):
        super().__init__(parent)
        self._project = project
        self._current_sheet: Sheet | None = None
        self._table_model: DataTableModel | None = None
        self._graph_vm: GraphViewModel | None = None
        self._popout_window: PopOutGraphWindow | None = None

        self.setWindowTitle("PlotBook")
        self.resize(1200, 800)

        # Create components
        self._navigator = Navigator()
        self._spreadsheet = SpreadsheetWidget()
        self._graph_canvas = GraphCanvas()
        self._format_panel = FormatPanel()

        # Layout
        self._setup_layout()
        self._setup_menubar()
        self._setup_toolbar()
        self._connect_signals()

        # Create default sheet if project is empty
        if not project.sheets:
            sheet = project.add_sheet(
                TableFormat.XY, EntryMode.RAW, GraphType.SCATTER, "Sheet 1"
            )

        self._navigator.set_project(project)

        # Select first sheet
        if project.sheets:
            self._navigator.select_sheet(project.sheets[0].id)
            self._switch_sheet(project.sheets[0])

    def _setup_layout(self) -> None:
        # Central splitter: spreadsheet on top, graph on bottom
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(self._spreadsheet)
        splitter.addWidget(self._graph_canvas)
        splitter.setSizes([300, 500])
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        self.setCentralWidget(splitter)

        # Navigator dock (left)
        nav_dock = QDockWidget("Sheets", self)
        nav_dock.setWidget(self._navigator)
        nav_dock.setMinimumWidth(150)
        nav_dock.setMaximumWidth(250)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, nav_dock)

        # Format panel dock (right)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self._format_panel)

        # Status bar
        self.statusBar().showMessage("Ready")

    def _setup_menubar(self) -> None:
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        new_action = QAction("&New Project", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self._on_new_project)
        file_menu.addAction(new_action)

        open_action = QAction("&Open...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self._on_open)
        file_menu.addAction(open_action)

        save_action = QAction("&Save", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self._on_save)
        file_menu.addAction(save_action)

        save_as_action = QAction("Save &As...", self)
        save_as_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        save_as_action.triggered.connect(self._on_save_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        import_csv_action = QAction("&Import CSV...", self)
        import_csv_action.triggered.connect(self._on_import_csv)
        file_menu.addAction(import_csv_action)

        file_menu.addSeparator()

        export_action = QAction("&Export Graph...", self)
        export_action.setShortcut(QKeySequence("Ctrl+E"))
        export_action.triggered.connect(self._on_export)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence("Alt+F4"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View menu
        view_menu = menubar.addMenu("&View")

        self._popout_action = QAction("Pop Out &Graph", self)
        self._popout_action.setShortcut(QKeySequence("Ctrl+G"))
        self._popout_action.setCheckable(True)
        self._popout_action.triggered.connect(self._on_toggle_popout)
        view_menu.addAction(self._popout_action)

        # Sheet menu
        sheet_menu = menubar.addMenu("&Sheet")

        new_sheet_action = QAction("&New Sheet...", self)
        new_sheet_action.setShortcut(QKeySequence("Ctrl+T"))
        new_sheet_action.triggered.connect(self._on_new_sheet)
        sheet_menu.addAction(new_sheet_action)

        change_type_action = QAction("Change &Graph Type...", self)
        change_type_action.triggered.connect(self._on_change_graph_type)
        sheet_menu.addAction(change_type_action)

        sheet_menu.addSeparator()
        swap_xy_action = QAction("Swap &X and Mean Columns", self)
        swap_xy_action.triggered.connect(self._on_swap_x_and_mean)
        sheet_menu.addAction(swap_xy_action)

        # Style menu
        style_menu = menubar.addMenu("St&yle")

        save_style_action = QAction("&Save Current Style...", self)
        save_style_action.triggered.connect(self._on_save_style)
        style_menu.addAction(save_style_action)

        self._apply_style_menu = style_menu.addMenu("&Apply Style")
        self._apply_style_menu.aboutToShow.connect(self._populate_apply_style_menu)

        self._delete_style_menu = style_menu.addMenu("&Delete Style")
        self._delete_style_menu.aboutToShow.connect(self._populate_delete_style_menu)

        style_menu.addSeparator()

        import_style_action = QAction("&Import Style File...", self)
        import_style_action.triggered.connect(self._on_import_style)
        style_menu.addAction(import_style_action)

        export_style_action = QAction("&Export Current Style...", self)
        export_style_action.triggered.connect(self._on_export_style)
        style_menu.addAction(export_style_action)

        # Palette menu
        palette_menu = menubar.addMenu("&Palette")
        from plotbook.models.palette import load_palettes
        palettes = load_palettes()
        for name in palettes:
            action = QAction(name.replace("_", " ").title(), self)
            action.triggered.connect(lambda checked, n=name: self._on_change_palette(n))
            palette_menu.addAction(action)

    def _setup_toolbar(self) -> None:
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        toolbar.addAction("New Sheet", self._on_new_sheet)
        toolbar.addSeparator()

        # Graph type quick selector
        toolbar.addWidget(QLabel(" Graph: "))
        self._graph_type_combo = QComboBox()
        self._graph_type_combo.setMinimumWidth(130)
        self._graph_type_combo.currentIndexChanged.connect(self._on_graph_type_combo_changed)
        toolbar.addWidget(self._graph_type_combo)

        toolbar.addSeparator()
        toolbar.addAction("Pop Out", self._on_toggle_popout)
        toolbar.addSeparator()
        toolbar.addAction("Export", self._on_export)

    def _connect_signals(self) -> None:
        # Navigator
        self._navigator.sheetSelected.connect(self._on_sheet_selected)
        self._navigator.sheetDeleteRequested.connect(self._on_delete_sheet)
        self._navigator.sheetDuplicateRequested.connect(self._on_duplicate_sheet)
        self._navigator.sheetRenamed.connect(self._on_rename_sheet)

        # Spreadsheet
        self._spreadsheet.seriesAdded.connect(self._on_series_structure_changed)
        self._spreadsheet.seriesRemoved.connect(self._on_series_structure_changed)
        self._spreadsheet.seriesRenamed.connect(self._on_series_structure_changed)

    # -----------------------------------------------------------------
    # Figure distribution: send figures to both inline and pop-out
    # -----------------------------------------------------------------

    def _on_figure_ready(self, fig) -> None:
        """Route rendered figures to the inline canvas and the pop-out window."""
        self._graph_canvas.update_figure(fig)
        if self._popout_window is not None and self._popout_window.isVisible():
            # Re-render a second copy for the pop-out (matplotlib figures
            # can only belong to one canvas, so we render again).
            from plotbook.rendering.engine import render
            if self._current_sheet:
                fig2 = render(
                    self._current_sheet.data_table,
                    self._current_sheet.graph_spec,
                )
                self._popout_window.update_figure(fig2)

    def _switch_sheet(self, sheet: Sheet) -> None:
        """Switch to a different sheet."""
        self._current_sheet = sheet

        # Table model
        self._table_model = DataTableModel(sheet.data_table)
        self._spreadsheet.set_model(self._table_model)

        # Graph viewmodel
        self._graph_vm = GraphViewModel(sheet)
        self._graph_vm.figureReady.connect(self._on_figure_ready)

        # Connect table edits to re-render
        self._table_model.dataChanged.connect(self._graph_vm.request_render)

        # Format panel
        self._format_panel.load_from_spec(sheet.graph_spec, sheet.data_table)
        self._format_panel.connect_to_viewmodel(self._graph_vm)

        # Update graph type combo
        self._update_graph_type_combo(sheet)

        # Initial render
        self._graph_vm.force_render()

        self.statusBar().showMessage(
            f"Sheet: {sheet.name} | "
            f"Format: {sheet.data_table.table_format.name} | "
            f"Graph: {GRAPH_TYPE_NAMES.get(sheet.graph_spec.graph_type, '')}"
        )

    def _update_graph_type_combo(self, sheet: Sheet) -> None:
        self._graph_type_combo.blockSignals(True)
        self._graph_type_combo.clear()
        for gt in GRAPH_TYPES_FOR_FORMAT.get(sheet.data_table.table_format, []):
            self._graph_type_combo.addItem(GRAPH_TYPE_NAMES.get(gt, gt.name), gt)
        idx = self._graph_type_combo.findData(sheet.graph_spec.graph_type)
        if idx >= 0:
            self._graph_type_combo.setCurrentIndex(idx)
        self._graph_type_combo.blockSignals(False)

    # -----------------------------------------------------------------
    # Pop-out graph window
    # -----------------------------------------------------------------

    def _on_toggle_popout(self) -> None:
        if self._popout_window is not None and self._popout_window.isVisible():
            self._popout_window.close()
            self._popout_window = None
            self._popout_action.setChecked(False)
        else:
            self._popout_window = PopOutGraphWindow()
            self._popout_window.closed.connect(self._on_popout_closed)
            self._popout_window.show()
            self._popout_action.setChecked(True)

            # Send current figure immediately
            if self._current_sheet:
                from plotbook.rendering.engine import render
                fig = render(
                    self._current_sheet.data_table,
                    self._current_sheet.graph_spec,
                )
                self._popout_window.update_figure(fig)

    def _on_popout_closed(self) -> None:
        self._popout_window = None
        self._popout_action.setChecked(False)

    # -----------------------------------------------------------------
    # Style presets
    # -----------------------------------------------------------------

    def _on_save_style(self) -> None:
        if self._current_sheet is None:
            return

        name, ok = QInputDialog.getText(
            self, "Save Style Preset",
            "Preset name:",
        )
        if not ok or not name.strip():
            return

        desc, _ = QInputDialog.getText(
            self, "Save Style Preset",
            "Description (optional):",
        )

        from plotbook.models.style_preset import StylePreset, save_preset
        preset = StylePreset.from_graph_spec(
            self._current_sheet.graph_spec, name.strip(), desc.strip()
        )
        path = save_preset(preset)
        self.statusBar().showMessage(f"Style saved: {name.strip()}")

    def _populate_apply_style_menu(self) -> None:
        self._apply_style_menu.clear()
        from plotbook.models.style_preset import list_presets
        presets = list_presets()

        if not presets:
            action = self._apply_style_menu.addAction("(No saved styles)")
            action.setEnabled(False)
            return

        for preset in presets:
            label = preset.name
            if preset.description:
                label += f"  -  {preset.description}"
            self._apply_style_menu.addAction(
                label,
                lambda p=preset: self._apply_preset(p),
            )

    def _apply_preset(self, preset) -> None:
        if self._current_sheet is None:
            return

        from plotbook.models.style_preset import StylePreset
        preset.apply_to(self._current_sheet.graph_spec)

        # Refresh UI
        self._format_panel.load_from_spec(
            self._current_sheet.graph_spec,
            self._current_sheet.data_table,
        )
        if self._graph_vm:
            self._graph_vm.force_render()

        self.statusBar().showMessage(f"Applied style: {preset.name}")

    def _populate_delete_style_menu(self) -> None:
        self._delete_style_menu.clear()
        from plotbook.models.style_preset import list_presets
        presets = list_presets()

        if not presets:
            action = self._delete_style_menu.addAction("(No saved styles)")
            action.setEnabled(False)
            return

        for preset in presets:
            self._delete_style_menu.addAction(
                preset.name,
                lambda n=preset.name: self._delete_preset(n),
            )

    def _delete_preset(self, name: str) -> None:
        reply = QMessageBox.question(
            self, "Delete Style",
            f"Delete style preset '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            from plotbook.models.style_preset import delete_preset
            delete_preset(name)
            self.statusBar().showMessage(f"Deleted style: {name}")

    def _on_export_style(self) -> None:
        """Export current style as a .json file the user can share."""
        if self._current_sheet is None:
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Export Style",
            "",
            "Style Files (*.json);;All Files (*)",
        )
        if not path:
            return

        from plotbook.models.style_preset import StylePreset
        import json
        preset = StylePreset.from_graph_spec(
            self._current_sheet.graph_spec,
            name=self._current_sheet.name + " style",
        )
        with open(path, "w", encoding="utf-8") as f:
            json.dump(preset.to_dict(), f, indent=2)
        self.statusBar().showMessage(f"Style exported to {path}")

    def _on_import_style(self) -> None:
        """Import a .json style file and apply it."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Style",
            "",
            "Style Files (*.json);;All Files (*)",
        )
        if not path:
            return

        from plotbook.models.style_preset import load_preset, save_preset
        try:
            preset = load_preset(path)
            # Save it to the local preset library too
            save_preset(preset)
            # Apply it
            self._apply_preset(preset)
            self.statusBar().showMessage(f"Imported and applied style: {preset.name}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to import style:\n{e}")

    # -----------------------------------------------------------------
    # Other slots
    # -----------------------------------------------------------------

    def _on_sheet_selected(self, sheet_id: str) -> None:
        for sheet in self._project.sheets:
            if sheet.id == sheet_id:
                self._switch_sheet(sheet)
                return

    def _on_new_sheet(self) -> None:
        dialog = NewSheetDialog(self)
        if dialog.exec():
            name, fmt, entry_mode, graph_type = dialog.result_values()
            sheet = self._project.add_sheet(fmt, entry_mode, graph_type, name)
            self._navigator.refresh()
            self._navigator.select_sheet(sheet.id)
            self._switch_sheet(sheet)

    def _on_delete_sheet(self, sheet_id: str) -> None:
        if len(self._project.sheets) <= 1:
            QMessageBox.warning(self, "Cannot Delete", "Must have at least one sheet.")
            return

        self._project.remove_sheet(sheet_id)
        self._navigator.refresh()
        if self._project.sheets:
            self._navigator.select_sheet(self._project.sheets[0].id)
            self._switch_sheet(self._project.sheets[0])

    def _on_duplicate_sheet(self, sheet_id: str) -> None:
        """Deep-copy a sheet (data + formatting) and add it to the project."""
        import json
        source = None
        for s in self._project.sheets:
            if s.id == sheet_id:
                source = s
                break
        if source is None:
            return

        from plotbook.models.project import Sheet
        d = source.to_dict()
        # Give it a new ID and name
        import uuid
        d["id"] = uuid.uuid4().hex[:8]
        d["name"] = source.name + " (copy)"
        new_sheet = Sheet.from_dict(d)
        self._project.sheets.append(new_sheet)
        self._project.dirty = True
        self._navigator.refresh()
        self._navigator.select_sheet(new_sheet.id)
        self._switch_sheet(new_sheet)
        self.statusBar().showMessage(f"Duplicated sheet: {source.name}")

    def _on_rename_sheet(self, sheet_id: str, new_name: str) -> None:
        for s in self._project.sheets:
            if s.id == sheet_id:
                s.name = new_name
                s.data_table.name = new_name
                break
        self._navigator.refresh()
        if self._current_sheet and self._current_sheet.id == sheet_id:
            self.statusBar().showMessage(f"Sheet renamed to: {new_name}")

    def _on_swap_x_and_mean(self) -> None:
        """Swap the X column with the Mean column for XY tables."""
        if self._current_sheet is None:
            return
        from plotbook.models.table_formats import XYTable
        table = self._current_sheet.data_table
        if not isinstance(table, XYTable):
            QMessageBox.information(self, "Swap", "This only works on XY format sheets.")
            return
        table.swap_x_and_mean()
        # Refresh everything
        if self._table_model:
            self._table_model.refresh_structure()
        if self._graph_vm:
            self._graph_vm.force_render()
        self.statusBar().showMessage("Swapped X and Mean columns")

    def _on_change_graph_type(self) -> None:
        if self._current_sheet is None:
            return

        dialog = GraphTypeDialog(
            self._current_sheet.data_table.table_format,
            self._current_sheet.graph_spec.graph_type,
            self,
        )
        if dialog.exec():
            gt = dialog.selected_type()
            if self._graph_vm:
                self._graph_vm.set_graph_type(gt)
                self._update_graph_type_combo(self._current_sheet)

    def _on_graph_type_combo_changed(self, index: int) -> None:
        gt = self._graph_type_combo.currentData()
        if gt and self._graph_vm:
            self._graph_vm.set_graph_type(gt)

    def _on_change_palette(self, palette_name: str) -> None:
        if self._current_sheet is None:
            return
        spec = self._current_sheet.graph_spec
        spec.palette_name = palette_name
        # Re-assign colors
        from plotbook.models.palette import get_palette
        palette = get_palette(palette_name)
        for i, series in enumerate(self._current_sheet.data_table.series):
            if series.id in spec.series_styles:
                spec.series_styles[series.id].color = palette.color_at(i)
        if self._graph_vm:
            self._graph_vm.force_render()
        self._format_panel.load_from_spec(spec, self._current_sheet.data_table)

    def _on_series_structure_changed(self, *args) -> None:
        """Called when series are added/removed from the spreadsheet."""
        if self._current_sheet and self._graph_vm:
            # Ensure styles exist for any new series
            spec = self._current_sheet.graph_spec
            for i, s in enumerate(self._current_sheet.data_table.series):
                spec.ensure_series_style(s.id, i)
            # Reload format panel
            self._format_panel.load_from_spec(spec, self._current_sheet.data_table)
            self._graph_vm.force_render()

    def _on_export(self) -> None:
        if self._graph_canvas.get_figure() is None:
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Export Graph",
            "",
            "PNG Image (*.png);;SVG Vector (*.svg);;PDF Document (*.pdf);;All Files (*)",
        )
        if path:
            fig = self._graph_canvas.get_figure()
            export_figure(fig, path)
            self.statusBar().showMessage(f"Exported to {path}")

    def _on_new_project(self) -> None:
        self._project = Project(name="Untitled Project")
        sheet = self._project.add_sheet(
            TableFormat.XY, EntryMode.RAW, GraphType.SCATTER, "Sheet 1"
        )
        self._navigator.set_project(self._project)
        self._navigator.select_sheet(sheet.id)
        self._switch_sheet(sheet)

    def _on_save(self) -> None:
        if self._project.file_path:
            self._save_to(self._project.file_path)
        else:
            self._on_save_as()

    def _on_save_as(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Project",
            "",
            "PlotBook Files (*.plotbook);;All Files (*)",
        )
        if path:
            self._save_to(path)

    def _save_to(self, path: str) -> None:
        from plotbook.io.file_format import save_project
        save_project(self._project, path)
        self._project.file_path = path
        self._project.dirty = False
        self.statusBar().showMessage(f"Saved to {path}")

    def _on_open(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Project",
            "",
            "PlotBook Files (*.plotbook);;All Files (*)",
        )
        if path:
            from plotbook.io.file_format import load_project
            try:
                project = load_project(path)
                project.file_path = path
                self._project = project
                self._navigator.set_project(project)
                if project.sheets:
                    self._navigator.select_sheet(project.sheets[0].id)
                    self._switch_sheet(project.sheets[0])
                self.statusBar().showMessage(f"Opened {path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open file:\n{e}")

    def _on_import_csv(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Import CSV",
            "",
            "CSV Files (*.csv *.tsv *.txt);;All Files (*)",
        )
        if path:
            from plotbook.io.csv_import import import_csv_to_sheet
            try:
                sheet = import_csv_to_sheet(path, self._project)
                self._navigator.refresh()
                self._navigator.select_sheet(sheet.id)
                self._switch_sheet(sheet)
                self.statusBar().showMessage(f"Imported {path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to import CSV:\n{e}")

    def closeEvent(self, event) -> None:
        # Close pop-out window if open
        if self._popout_window is not None:
            self._popout_window.close()
            self._popout_window = None
        super().closeEvent(event)
