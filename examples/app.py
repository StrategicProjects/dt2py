"""Minimal Shiny for Python app exercising the dt2 widget.

Run with:  shiny run examples/app.py
Requires:  pip install -e ".[shiny,pandas]"
"""

import pandas as pd
from shiny import App, reactive, render, ui
from shinywidgets import output_widget, render_widget, reactive_read

from dt2 import dt2

df = pd.DataFrame(
    {
        "name": ["Ada", "Alan", "Grace", "Linus", "Margaret"],
        "field": ["Math", "Logic", "Navy", "Kernel", "Apollo"],
        "year": [1815, 1912, 1906, 1969, 1936],
    }
)

app_ui = ui.page_fluid(
    ui.h3("dt2 — DataTables v2 in Shiny for Python"),
    output_widget("tbl"),
    ui.output_text_verbatim("selection"),
)


def server(input, output, session):
    @render_widget
    def tbl():
        return dt2(df, select=True, pageLength=5)

    @render.text
    def selection():
        rows = reactive_read(tbl.widget, "selected_rows")
        return f"selected rows (1-based): {rows}"


app = App(app_ui, server)
