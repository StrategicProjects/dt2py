# dt2 — DataTables v2 for Shiny for Python

<!-- badges: start -->
[![CI](https://github.com/StrategicProjects/dt2py/actions/workflows/ci.yml/badge.svg)](https://github.com/StrategicProjects/dt2py/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/dt2.svg)](https://pypi.org/project/dt2/)
[![Python versions](https://img.shields.io/pypi/pyversions/dt2.svg)](https://pypi.org/project/dt2/)
[![Docs](https://img.shields.io/badge/docs-mkdocs--material-blue.svg)](https://strategicprojects.github.io/dt2py/)
[![License](https://img.shields.io/badge/license-MIT-darkviolet.svg)](LICENSE)
[![R package: DT2](https://img.shields.io/badge/R%20package-DT2-198CE7.svg?logo=r)](https://github.com/StrategicProjects/DT2)
<!-- badges: end -->

A Python port of the R [**DT2**](https://github.com/StrategicProjects/DT2)
package: an [anywidget](https://anywidget.dev) binding for
[DataTables v2](https://datatables.net), designed for
[Shiny for Python](https://shiny.posit.co/py/) (and usable in Jupyter).

It configures DataTables via plain Python (1:1 with the JS API), reusing the
same DataTables runtime (2.3.4) and extensions as the R package.

📖 **Documentation:** <https://strategicprojects.github.io/dt2py/> ·
📦 **PyPI:** <https://pypi.org/project/dt2/>

> Status: **feature-complete toward R parity, pre-release.** Config, all 15
> extensions, server-side processing, proxy, events and inline inputs are
> implemented and unit-tested. The live in-browser Comm transport has not yet
> been visually verified. See [ROADMAP.md](ROADMAP.md) and [CHANGELOG.md](CHANGELOG.md).

## Install (dev)

```bash
npm install && npm run build        # build the JS bundle into src/dt2/static/
uv venv && uv pip install -e ".[shiny,pandas]"
```

(The built bundle is committed, so an installed wheel needs no Node toolchain.)

## Quick start

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

## Configure with `Options`

Chainable builder mirroring the R pipe helpers:

```python
from dt2 import Options, JS, dt2

opts = (Options(df)
        .cols_align(["revenue"], "right")
        .format_number(["revenue"], thousands=".", decimal=",", digits=2, prefix="R$ ")
        .format_datetime(["updated"], from_="YYYY-MM-DD", to="DD/MM/YYYY")
        .cols_render(["score"], JS("function(d,t){ return t==='display' ? d+'%' : d; }"))
        .order(("revenue", "desc"))
        .length_menu([10, 25, -1]))

dt2(df, options=opts)
```

`JS(...)` is the parity for `htmlwidgets::JS()`: the source is revived into a
real function in the browser, with `DataTable`, `$` and `moment` in scope.

## Extensions

All 15 DataTables extensions are bundled; activate via `Options`:

```python
opts = (Options(df)
        .buttons(["copyHtml5", "csvHtml5", "excelHtml5"])  # jszip bundled; PDF needs pdfmake
        .select({"style": "os"})
        .responsive()
        .fixed_header()
        .row_group("field"))
```

`dt2.extensions()` lists what is bundled.

## Server-side processing

Keep large data Python-side; DataTables fetches pages over the Comm:

```python
dt2(big_df, server_side=True, pageLength=25)
```

Filtering/ordering/paging run in `dt2.server.process_ssp`.

## Proxy, events and inline inputs

```python
# proxy (Python -> table): call on the rendered widget
tbl.widget.search("ada")
tbl.widget.order(("field", "desc"))
tbl.widget.select_rows([1, 3])

# events (table -> Python): read reactively
from shinywidgets import reactive_read
reactive_read(tbl.widget, "selected_rows")  # also: state, row_check, row_button

# inline row inputs
opts = Options(df).col_checkbox("select", value_col="active").col_button("act", label="Ping")
```

See [`examples/`](examples/) for runnable apps:
`app.py`, `app_config.py`, `app_extensions.py`, `app_serverside.py`,
`app_proxy_inputs.py`.

## How it relates to the R package

The DataTables runtime is shared conceptually with R DT2. What differs is the
**transport**: R talks to Shiny via `window.Shiny`; here the widget talks to the
Python kernel over the anywidget Comm, bridged to Shiny reactivity by
`shinywidgets`. The `htmlwidgets::JS()` mechanism becomes the `JS()` marker +
client-side reviver. See the header of `js/index.js` for the full mapping.

## License

MIT © André Leite
