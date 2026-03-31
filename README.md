# PlotBook

A free, open-source publication-quality graph editor for scientists. Built with Python, PyQt6, and matplotlib.

PlotBook provides a spreadsheet-style data entry interface paired with a live-updating graph canvas, making it straightforward to create, format, and export scientific figures.

## Features

### Data Entry
- **Three table formats**:
  - **XY** — shared X column with Y series (scatter, line, area plots)
  - **Column** — each column is a group, rows are replicates (bar, box, violin, dot plots)
  - **Grouped** — rows are categories, columns are groups (grouped and stacked bar charts)
- **Four entry modes** per table: raw replicates, mean ± SD, mean ± SEM, or single values
- Paste from Excel/Google Sheets (tab-separated), with **Paste Transposed** option
- Double-click column headers to rename; **Swap X and Mean** for quick column reordering
- Auto-expanding rows as you type

### Graph Types
| XY Format | Column Format | Grouped Format |
|-----------|--------------|----------------|
| Scatter | Bar | Grouped Bar |
| Line | Box & Whisker | Stacked Bar |
| Line + Scatter | Violin | |
| Spline | Dot Plot | |
| Area | | |

### Formatting
- **Series styling** — colour, markers (shape/size/fill), lines (style/width), bar width/opacity/edge
- **Error bars** — SD, SEM, 95% CI, 99% CI, range; direction (both/above/below); cap width and line width
- **Axes** — label text (multi-line, with symbol picker), font family/size/bold/italic, tick label font, label spacing, tick rotation, tick label wrapping, min/max range with Auto reset, log scale, grid lines, axis inversion
- **Scientific notation** — when values are very small or large, the exponent is automatically moved into the axis label (e.g. `Papp (cm/s) [×10⁻⁷]`) instead of floating at the axis edge
- **Title** — multi-line, full font control
- **Legend** — show/hide, position, font, frame
- **7 colour palettes** — Default, Prism, Pastel, Grayscale, Colorblind Safe, Nature, Science

### Annotations
- **Reference/normalisation lines** — horizontal or vertical, with label text, colour, line style, opacity, and position control
- **Bar/point labels** — place text (e.g. `*`, `***`, `ns`, `p<0.05`) above individual bars or data points
- **Comparison brackets** — draw bracket lines between two bars/points with significance text; auto-stacking for multiple brackets
- **Symbol picker** (Ω button) — insert Greek letters (α β γ δ ...), superscripts/subscripts (⁰¹²³ ₀₁₂₃), and math symbols (± × ÷ ° µ ∞ ≤ ≥) into any text field

### Trendlines
- **7 fit types** — linear, quadratic, cubic, exponential, logarithmic, power
- Equation and R² display with configurable font and position
- Adjustable line colour/style/width and extrapolation beyond data range

### Style Presets
- Save the current graph formatting as a named preset
- Apply saved presets to any sheet with one click
- Import/export style files (`.json`) to share with others
- Stored in `~/.plotbook/styles/`

### Pop-Out Graph Window
- Detach the graph into a separate resizable window (`Ctrl+G`)
- Minimal toolbar: Home, Pan, Save
- **Copy to Clipboard** button for pasting into documents
- **Preset sizes** (Small, Medium, Large, Wide, Presentation, A4, Square) or type custom dimensions
- Live-synced with data and formatting changes

### Project Management
- Multiple sheets per project with a navigator sidebar
- Duplicate, rename, or delete sheets via right-click
- Save/load projects as `.plotbook` files (JSON format)
- Import CSV/TSV files
- Export graphs as PNG, SVG, or PDF

## Installation

**Requirements:** Python 3.10+

```bash
pip install -e .
```

With optional statistics support (confidence intervals using scipy):

```bash
pip install -e ".[stats]"
```

### Dependencies
- PyQt6 ≥ 6.5
- matplotlib ≥ 3.7
- numpy ≥ 1.24
- scipy ≥ 1.10 *(optional, for CI error bars)*

## Usage

```bash
python -m plotbook
```

Or if installed via pip:

```bash
plotbook
```

The application opens with a default XY scatter sheet. Use **Sheet > New Sheet** (or the toolbar) to create additional sheets with different formats.

### Quick Start

1. **Create a sheet** — choose a table format (XY, Column, or Grouped) and data entry mode
2. **Enter data** — type values into the spreadsheet; the graph updates live
3. **Choose a graph type** — use the toolbar dropdown or Sheet > Change Graph Type
4. **Format** — use the tabbed Format panel on the right (Series, Error Bars, X/Y Axis, Title, Legend, Ref Lines, Annotate, Trendline)
5. **Export** — File > Export Graph (PNG/SVG/PDF) or use the pop-out window's Copy to Clipboard

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+T` | New Sheet |
| `Ctrl+G` | Pop out graph window |
| `Ctrl+E` | Export graph |
| `Ctrl+S` | Save project |
| `Ctrl+O` | Open project |
| `Ctrl+C` / `Ctrl+V` | Copy / Paste in spreadsheet |
| `Delete` | Clear selected cells |
| Double-click header | Rename column |
| Double-click sheet | Rename sheet |
| Right-click sheet | Duplicate / Delete sheet |

## Project Structure

```
src/plotbook/
├── models/          # Data model layer (zero Qt imports)
│   ├── enums.py         # TableFormat, EntryMode, GraphType, etc.
│   ├── datatable.py     # DataTable, DataSeries, ColumnDef
│   ├── table_formats.py # XYTable, ColumnTable, GroupedTable
│   ├── graph_spec.py    # GraphSpec (declarative graph description)
│   ├── style.py         # FontSpec, SeriesStyle, AxisStyle, Trendline, etc.
│   ├── style_preset.py  # Save/load reusable style presets
│   ├── palette.py       # Colour palettes
│   └── project.py       # Project, Sheet
├── stats/
│   └── descriptive.py   # mean, sd, sem, ci, quartiles
├── rendering/       # Stateless matplotlib rendering (zero Qt imports)
│   ├── engine.py        # render(DataTable, GraphSpec) -> Figure
│   ├── series_renderers.py  # One function per graph type
│   ├── error_bars.py    # Error bar drawing
│   ├── formatters.py    # Axis/title/legend/trendline/annotation formatting
│   └── export.py        # PNG/SVG/PDF export
├── viewmodels/      # Qt bridge layer
│   ├── table_model.py   # QAbstractTableModel for the spreadsheet
│   └── graph_viewmodel.py  # Debounced rendering bridge
├── ui/              # PyQt6 widgets
│   ├── main_window.py   # Main application window
│   ├── spreadsheet.py   # Data entry with editable headers
│   ├── graph_canvas.py  # Inline + pop-out graph display
│   ├── format_panel.py  # Tabbed formatting sidebar
│   ├── format_pages/    # Individual format tabs
│   ├── navigator.py     # Sheet list sidebar
│   ├── symbol_picker.py # Greek/math symbol insertion
│   └── *.py             # Dialogs (new sheet, graph type)
└── io/              # File I/O
    ├── file_format.py   # .plotbook JSON save/load
    ├── csv_import.py    # CSV/TSV import
    └── clipboard.py     # Clipboard utilities
```

## Architecture

PlotBook uses a clean MVC separation:

- **Models** have zero Qt imports and are independently testable
- **Rendering** is stateless: `render(DataTable, GraphSpec) -> matplotlib.Figure`
- **ViewModels** bridge Qt signals to the model/rendering layers
- **UI** handles all user interaction

Data flows:
```
Cell edit → DataTableModel → DataTable (numpy) → dataChanged signal
         → GraphViewModel (100ms debounce) → RenderEngine → Figure
         → GraphCanvas.update_figure() → visible graph
```

## Contributing

Contributions are welcome. Please open an issue or pull request.

## Licence

This project is provided as-is for free use. See the repository for details.
