"""Reusable symbol/Greek letter picker for inserting special characters."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


# Character groups for the picker
_SYMBOL_GROUPS: list[tuple[str, list[tuple[str, str]]]] = [
    ("Greek Lower", [
        ("α", "alpha"), ("β", "beta"), ("γ", "gamma"), ("δ", "delta"),
        ("ε", "epsilon"), ("ζ", "zeta"), ("η", "eta"), ("θ", "theta"),
        ("ι", "iota"), ("κ", "kappa"), ("λ", "lambda"), ("μ", "mu"),
        ("ν", "nu"), ("ξ", "xi"), ("π", "pi"), ("ρ", "rho"),
        ("σ", "sigma"), ("τ", "tau"), ("υ", "upsilon"), ("φ", "phi"),
        ("χ", "chi"), ("ψ", "psi"), ("ω", "omega"),
    ]),
    ("Greek Upper", [
        ("Α", "Alpha"), ("Β", "Beta"), ("Γ", "Gamma"), ("Δ", "Delta"),
        ("Ε", "Epsilon"), ("Ζ", "Zeta"), ("Η", "Eta"), ("Θ", "Theta"),
        ("Λ", "Lambda"), ("Ξ", "Xi"), ("Π", "Pi"), ("Σ", "Sigma"),
        ("Φ", "Phi"), ("Ψ", "Psi"), ("Ω", "Omega"),
    ]),
    ("Super/Sub", [
        ("⁰", "super 0"), ("¹", "super 1"), ("²", "super 2"), ("³", "super 3"),
        ("⁴", "super 4"), ("⁵", "super 5"), ("⁶", "super 6"), ("⁷", "super 7"),
        ("⁸", "super 8"), ("⁹", "super 9"), ("⁺", "super +"), ("⁻", "super -"),
        ("⁽", "super ("), ("⁾", "super )"), ("ⁿ", "super n"),
        ("₀", "sub 0"), ("₁", "sub 1"), ("₂", "sub 2"), ("₃", "sub 3"),
        ("₄", "sub 4"), ("₅", "sub 5"), ("₆", "sub 6"), ("₇", "sub 7"),
        ("₈", "sub 8"), ("₉", "sub 9"), ("₊", "sub +"), ("₋", "sub -"),
        ("₍", "sub ("), ("₎", "sub )"),
    ]),
    ("Math/Science", [
        ("±", "plus-minus"), ("×", "multiply"), ("÷", "divide"), ("·", "dot"),
        ("°", "degree"), ("µ", "micro"), ("‰", "per mille"), ("∞", "infinity"),
        ("√", "sqrt"), ("∑", "sum"), ("∏", "product"), ("∫", "integral"),
        ("∂", "partial"), ("∇", "nabla"), ("≈", "approx"), ("≠", "not equal"),
        ("≤", "leq"), ("≥", "geq"), ("→", "arrow right"), ("←", "arrow left"),
        ("↑", "arrow up"), ("↓", "arrow down"), ("↔", "arrow both"),
        ("Å", "angstrom"), ("ℓ", "script l"), ("ℏ", "h-bar"),
        ("′", "prime"), ("″", "double prime"),
    ]),
]


class SymbolPickerPopup(QWidget):
    """Popup widget showing a grid of symbols organised in tabs."""

    def __init__(self, target_line_edit: QLineEdit, parent=None):
        super().__init__(parent, Qt.WindowType.Popup)
        self._target = target_line_edit
        self.setWindowTitle("Insert Symbol")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        tabs = QTabWidget()
        tabs.setTabPosition(QTabWidget.TabPosition.North)

        for group_name, symbols in _SYMBOL_GROUPS:
            page = QWidget()
            grid = QGridLayout(page)
            grid.setSpacing(2)
            cols = 8
            for i, (char, tooltip) in enumerate(symbols):
                btn = QPushButton(char)
                btn.setFixedSize(32, 32)
                btn.setToolTip(tooltip)
                btn.setStyleSheet("font-size: 14px;")
                btn.clicked.connect(lambda checked, c=char: self._insert(c))
                grid.addWidget(btn, i // cols, i % cols)
            tabs.addTab(page, group_name)

        layout.addWidget(tabs)

    def _insert(self, char: str) -> None:
        """Insert character at the cursor position in the target widget."""
        from PyQt6.QtWidgets import QPlainTextEdit, QTextEdit
        if isinstance(self._target, (QPlainTextEdit, QTextEdit)):
            self._target.insertPlainText(char)
        else:
            # QLineEdit
            pos = self._target.cursorPosition()
            text = self._target.text()
            self._target.setText(text[:pos] + char + text[pos:])
            self._target.setCursorPosition(pos + len(char))
        self._target.setFocus()
        self.close()


class SymbolButton(QToolButton):
    """
    A small button (Ω) that opens a symbol picker popup.
    Attach to any QLineEdit to let the user insert Greek letters etc.
    """

    def __init__(self, target_widget, parent=None):
        super().__init__(parent)
        self._target = target_widget
        self.setText("Ω")
        self.setToolTip("Insert symbol (Greek letters, superscripts, math)")
        self.setFixedSize(28, 28)
        self.setStyleSheet("font-size: 13px; font-weight: bold;")
        self.clicked.connect(self._show_picker)

    def _show_picker(self) -> None:
        popup = SymbolPickerPopup(self._target, self)
        # Position below the button
        pos = self.mapToGlobal(self.rect().bottomLeft())
        popup.move(pos)
        popup.show()
