"""Server-side processing demo: 50k rows, paged/filtered/sorted in Python.

Run with:  shiny run examples/app_serverside.py
The browser only ever holds one page of rows; filtering/sorting/paging round-trip
to Python over the anywidget Comm (see dt2.server.process_ssp).
"""

import pandas as pd
from shiny import App, ui
from shinywidgets import output_widget, render_widget

from dt2 import dt2

N = 50_000
fields = ["Math", "Logic", "Navy", "Kernel", "Apollo"]
df = pd.DataFrame(
    {
        "id": range(1, N + 1),
        "name": [f"person_{i:05d}" for i in range(N)],
        "field": [fields[i % len(fields)] for i in range(N)],
        "year": [1800 + (i % 220) for i in range(N)],
    }
)

app_ui = ui.page_fluid(
    ui.h3(f"dt2 — server-side processing ({N:,} rows)"),
    output_widget("tbl"),
)


def server(input, output, session):
    @render_widget
    def tbl():
        return dt2(df, server_side=True, pageLength=10, searching=True, ordering=True)


app = App(app_ui, server)
