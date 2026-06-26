"""Config-helpers demo: alignment, number/datetime formatting, ordering, custom JS.

Run with:  shiny run examples/app_config.py
Mirrors the R pipe style: build an Options, then pass it to dt2().
"""

import pandas as pd
from shiny import App, ui
from shinywidgets import output_widget, render_widget

from dt2 import JS, Options, dt2

df = pd.DataFrame(
    {
        "product": ["Alpha", "Beta", "Gamma", "Delta"],
        "revenue": [1234567.5, 89012.0, 4500.25, 23000000.0],
        "updated": ["2026-01-15", "2026-03-02", "2026-05-20", "2026-06-10"],
        "score": [0.91, 0.42, 0.77, 0.63],
    }
)

opts = (
    Options(df)
    .cols_align(["revenue", "score"], "right")
    .format_number(["revenue"], thousands=".", decimal=",", digits=2, prefix="R$ ")
    .format_datetime(["updated"], from_="YYYY-MM-DD", to="DD/MM/YYYY")
    .cols_render(
        ["score"],
        JS(
            "function(d,t){ if(t!=='display') return d;"
            " var pct=(d*100).toFixed(0)+'%';"
            " var color=d>=0.75?'success':d>=0.5?'warning':'danger';"
            " return '<span class=\"badge text-bg-'+color+'\">'+pct+'</span>'; }"
        ),
    )
    .order(("revenue", "desc"))
    .length_menu([5, 10, -1])
)

app_ui = ui.page_fluid(
    ui.h3("dt2 — config helpers (format, align, order, custom JS render)"),
    output_widget("tbl"),
)


def server(input, output, session):
    @render_widget
    def tbl():
        return dt2(df, options=opts)


app = App(app_ui, server)
