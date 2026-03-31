"""Application entry point."""

import sys

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("PlotBook")
    app.setApplicationVersion("0.1.0")
    app.setStyle("Fusion")

    from plotbook.ui.main_window import MainWindow
    from plotbook.models.project import Project

    project = Project(name="Untitled Project")
    window = MainWindow(project)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
