# Quickstart

## Install

```bash
pip install dt2
# with Shiny for Python + pandas:
pip install "dt2" shiny shinywidgets pandas
```

The built JS bundle ships inside the wheel, so no Node toolchain is needed.

## A table in Shiny for Python

```python
import pandas as pd
from shiny import App, ui
from shinywidgets import output_widget, render_widget
from dt2 import dt2

df = pd.DataFrame(
    {"name": ["Ada", "Alan", "Grace"], "year": [1815, 1912, 1906]}
)

app_ui = ui.page_fluid(output_widget("tbl"))

def server(input, output, session):
    @render_widget
    def tbl():
        return dt2(df, select=True, pageLength=10)

app = App(app_ui, server)
```

Run it with `shiny run app.py`.

## Inputs

`dt2()` accepts a pandas/polars DataFrame or a list of dict rows. Any keyword
arguments are passed straight to DataTables (1:1 with its JS options):

```python
dt2(df, paging=False, ordering=True, searching=True)
```

For richer configuration, build an [`Options`](options.md) object and pass it:

```python
from dt2 import Options
opts = Options(df).cols_align(["year"], "right").order(("year", "desc"))
dt2(df, options=opts)
```

## In Jupyter

`Dt2` is an anywidget, so it also renders in notebooks:

```python
from dt2 import dt2
dt2(df, select=True)
```
