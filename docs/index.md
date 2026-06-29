# dt2

<p align="center">
  <img src="assets/logo.svg" alt="dt2 hex logo" width="200">
</p>

**DataTables v2 for Shiny for Python** — an [anywidget](https://anywidget.dev)
binding for [DataTables v2](https://datatables.net), and the Python port of the R
[**DT2**](https://github.com/StrategicProjects/DT2) package.

It configures DataTables via plain Python (1:1 with the JS API), reusing the same
DataTables runtime (2.3.4) and extensions as the R package. Works in
[Shiny for Python](https://shiny.posit.co/py/) and Jupyter.

```bash
pip install dt2
```

```python
import pandas as pd
from shiny import App, ui
from shinywidgets import output_widget, render_widget
from dt2 import dt2

df = pd.read_csv("data.csv")
app_ui = ui.page_fluid(output_widget("tbl"))

def server(input, output, session):
    @render_widget
    def tbl():
        return dt2(df, select=True, pageLength=10)

app = App(app_ui, server)
```

## What you get

- [**Configurable tables**](options.md) via a chainable `Options` builder
  (formats, alignment, ordering, custom JS renderers).
- [**All 15 DataTables extensions**](extensions.md) bundled (Buttons, Select,
  Responsive, FixedHeader, SearchPanes, RowGroup, …).
- [**Server-side processing**](server-side.md) for large data, over the widget Comm.
- [**Proxy, events and inline inputs**](proxy-events.md) wired to Shiny reactivity.

## Relationship to the R package

`dt2` mirrors the API of the R [DT2](https://github.com/StrategicProjects/DT2)
package. The difference is the **transport**: R talks to Shiny via `window.Shiny`;
here the widget talks to the Python kernel over the anywidget Comm, bridged to
Shiny reactivity by `shinywidgets`. The `htmlwidgets::JS()` mechanism becomes the
[`JS()`](options.md#raw-javascript-renderers) marker plus a client-side reviver.

| | R | Python |
| --- | --- | --- |
| Package | [`DT2`](https://github.com/StrategicProjects/DT2) (CRAN) | [`dt2`](https://pypi.org/project/dt2/) (PyPI) |
| Frontend | htmlwidgets / Shiny (R) | anywidget / Shiny for Python |
| Docs | pkgdown site | this site |
