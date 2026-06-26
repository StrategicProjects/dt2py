"""Extensions demo: Buttons (export), Select, Responsive, FixedHeader, RowGroup.

Run with:  shiny run examples/app_extensions.py
All extensions are bundled; each activates via its Options helper.
Excel/CSV/copy export works (jszip bundled); PDF needs pdfmake (not bundled).
"""

import pandas as pd
from shiny import App, ui
from shinywidgets import output_widget, render_widget

from dt2 import Options, dt2

fields = ["Math", "Logic", "Navy", "Kernel", "Apollo"]
df = pd.DataFrame(
    {
        "name": [f"person_{i:03d}" for i in range(40)],
        "field": [fields[i % len(fields)] for i in range(40)],
        "year": [1900 + (i % 120) for i in range(40)],
    }
)

opts = (
    Options(df)
    .buttons(["copyHtml5", "csvHtml5", "excelHtml5", "print"])
    .select({"style": "os"})
    .responsive()
    .fixed_header()
    .row_group("field")
    .order(("field", "asc"))
    .length_menu([10, 25, -1])
)

app_ui = ui.page_fluid(
    ui.h3("dt2 — extensions (Buttons, Select, Responsive, FixedHeader, RowGroup)"),
    output_widget("tbl"),
)


def server(input, output, session):
    @render_widget
    def tbl():
        return dt2(df, options=opts)


app = App(app_ui, server)
