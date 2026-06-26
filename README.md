# dt2 — DataTables v2 for Shiny for Python

A Python port of the R [**DT2**](https://github.com/StrategicProjects/DT2)
package: an [anywidget](https://anywidget.dev) binding for
[DataTables v2](https://datatables.net), designed for
[Shiny for Python](https://shiny.posit.co/py/) (and usable in Jupyter).

It configures DataTables via plain Python dicts (1:1 with the JS API), reusing
the same vendored DataTables runtime and extensions as the R package. Target:
**feature parity** with R DT2 — config, extensions, proxy, events, inline
inputs, and server-side processing.

> Status: **early scaffold.** A minimal table renders and selection events flow
> back to Shiny. See [ROADMAP.md](ROADMAP.md) for the parity checklist.

## Install (dev)

```bash
npm install && npm run build        # build the JS bundle into src/dt2/static/
uv venv && uv pip install -e ".[shiny,pandas]"
```

## Use

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

See [`examples/app.py`](examples/app.py).

## How it relates to the R package

The DataTables JS runtime is shared conceptually with R DT2. What differs is the
**transport**: R talks to Shiny via `window.Shiny`; here the widget talks to the
Python kernel over the anywidget Comm, bridged to Shiny reactivity by
`shinywidgets`. See the header of `js/index.js` for the mapping.

## License

MIT © André Leite
