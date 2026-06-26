"""Proxy + inline inputs + events demo.

Run with:  shiny run examples/app_proxy_inputs.py

- Buttons drive the table from Python via the proxy API (search, order, page).
- Each row has a checkbox and an action button (inline inputs); clicks flow
  back as reactive events.
"""

import pandas as pd
from shiny import App, reactive, render, ui
from shinywidgets import output_widget, render_widget, reactive_read

from dt2 import Options, dt2

df = pd.DataFrame(
    {
        "select": [""] * 6,
        "name": ["Ada", "Alan", "Grace", "Linus", "Margaret", "Donald"],
        "field": ["Math", "Logic", "Navy", "Kernel", "Apollo", "Art"],
        "active": [True, False, True, True, False, True],
        "act": [""] * 6,
    }
)

opts = (
    Options(df)
    .col_checkbox("select", value_col="active")
    .col_button("act", label="Ping")
    .order(("name", "asc"))
)

app_ui = ui.page_fluid(
    ui.h3("dt2 — proxy + inline inputs + events"),
    ui.input_text("q", "Search (drives the table via proxy):", ""),
    ui.input_action_button("sort_year", "Order by field desc (proxy)"),
    output_widget("tbl"),
    ui.output_text_verbatim("events"),
)


def server(input, output, session):
    @render_widget
    def tbl():
        return dt2(df, options=opts, pageLength=5)

    @reactive.effect
    @reactive.event(input.q)
    def _search():
        tbl.widget.search(input.q())

    @reactive.effect
    @reactive.event(input.sort_year)
    def _order():
        tbl.widget.order(("field", "desc"))

    @render.text
    def events():
        chk = reactive_read(tbl.widget, "row_check")
        btn = reactive_read(tbl.widget, "row_button")
        return f"last checkbox: {chk}\nlast button:   {btn}"


app = App(app_ui, server)
