"""Navigator tree for sheets."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QInputDialog,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QVBoxLayout,
    QWidget,
)

from plotbook.models.project import Project, Sheet


class Navigator(QWidget):
    """Left sidebar listing all sheets in the project."""

    sheetSelected = pyqtSignal(str)        # sheet_id
    sheetDeleteRequested = pyqtSignal(str)  # sheet_id
    sheetDuplicateRequested = pyqtSignal(str)  # sheet_id
    sheetRenamed = pyqtSignal(str, str)     # sheet_id, new_name

    def __init__(self, parent=None):
        super().__init__(parent)
        self._list = QListWidget()
        self._list.currentItemChanged.connect(self._on_item_changed)
        self._list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._list.customContextMenuRequested.connect(self._show_context_menu)
        self._list.itemDoubleClicked.connect(self._on_double_click)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._list)

        self._project: Project | None = None

    def set_project(self, project: Project) -> None:
        self._project = project
        self.refresh()

    def refresh(self) -> None:
        if self._project is None:
            return

        self._list.blockSignals(True)
        current_id = None
        if self._list.currentItem():
            current_id = self._list.currentItem().data(Qt.ItemDataRole.UserRole)

        self._list.clear()
        for sheet in self._project.sheets:
            item = QListWidgetItem(sheet.name)
            item.setData(Qt.ItemDataRole.UserRole, sheet.id)
            self._list.addItem(item)

        # Restore selection
        if current_id:
            for i in range(self._list.count()):
                if self._list.item(i).data(Qt.ItemDataRole.UserRole) == current_id:
                    self._list.setCurrentRow(i)
                    break

        self._list.blockSignals(False)

    def select_sheet(self, sheet_id: str) -> None:
        for i in range(self._list.count()):
            item = self._list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == sheet_id:
                self._list.setCurrentRow(i)
                return

    def _on_item_changed(self, current: QListWidgetItem, previous) -> None:
        if current:
            sheet_id = current.data(Qt.ItemDataRole.UserRole)
            self.sheetSelected.emit(sheet_id)

    def _on_double_click(self, item: QListWidgetItem) -> None:
        """Double-click a sheet to rename it."""
        sheet_id = item.data(Qt.ItemDataRole.UserRole)
        current_name = item.text()
        new_name, ok = QInputDialog.getText(
            self, "Rename Sheet", "New name:", text=current_name
        )
        if ok and new_name.strip():
            self.sheetRenamed.emit(sheet_id, new_name.strip())

    def _show_context_menu(self, pos) -> None:
        item = self._list.itemAt(pos)
        if item is None:
            return

        sheet_id = item.data(Qt.ItemDataRole.UserRole)
        menu = QMenu(self)
        menu.addAction("Rename Sheet", lambda: self._rename_sheet(sheet_id, item.text()))
        menu.addAction("Duplicate Sheet", lambda: self.sheetDuplicateRequested.emit(sheet_id))
        menu.addSeparator()
        menu.addAction("Delete Sheet", lambda: self.sheetDeleteRequested.emit(sheet_id))
        menu.exec(self._list.viewport().mapToGlobal(pos))

    def _rename_sheet(self, sheet_id: str, current_name: str) -> None:
        new_name, ok = QInputDialog.getText(
            self, "Rename Sheet", "New name:", text=current_name
        )
        if ok and new_name.strip():
            self.sheetRenamed.emit(sheet_id, new_name.strip())
