# Proxy, events & inline inputs

## Proxy: drive the table from Python

The rendered widget **is** the proxy (no separate id/session like in R). Call
methods on it from a reactive context:

```python
tbl.widget.search("ada")
tbl.widget.order(("field", "desc"))     # column name or 1-based index
tbl.widget.page("number", 3)
tbl.widget.select_rows([1, 3])
tbl.widget.clear_search()
tbl.widget.replace_data(new_df)
```

Mirrors the R `dt2_proxy_*` verbs: `replace_data`, `draw`, `reload`, `order`,
`search`, `clear_search`, `page`, `select_rows`.

```python
from shiny import reactive

@reactive.effect
@reactive.event(input.q)
def _():
    tbl.widget.search(input.q())
```

## Events: read table state reactively

The widget exposes event traits; read them with `shinywidgets.reactive_read`:

```python
from shinywidgets import reactive_read

reactive_read(tbl.widget, "selected_rows")  # [1-based indices]
reactive_read(tbl.widget, "state")          # {reason, order, search, page, selected,
                                            #  rows_all, rows_current, rows_selected}
reactive_read(tbl.widget, "row_check")      # {row, value}  (inline checkbox)
reactive_read(tbl.widget, "row_button")     # {row, id}     (inline button)
```

### Which rows are visible?

`state` carries three 1-based index lists, named after the R package's
`input$<id>_rows_*` inputs (and DT's):

| Key             | Contents                                                    |
|-----------------|-------------------------------------------------------------|
| `rows_all`      | rows surviving the current filters (global + column search) |
| `rows_current`  | rows on the current page                                    |
| `rows_selected` | selected rows (Select extension)                            |

They refresh on every draw, so ColumnControl filters are reflected too.
Typical use: summarise or export exactly what the user filtered:

```python
@render.text
def summary():
    st = reactive_read(tbl.widget, "state") or {}
    idx = st.get("rows_all")
    sub = df if idx is None else df.iloc[[i - 1 for i in idx]]
    return f"{len(sub)} rows after filtering"
```

With `server_side=True` the indices come from the Python response; pass
`rows_all=False` to `dt2()` on very large tables to skip sending the full
index list on every draw (the keys are then `None`).

!!! note "Why events re-fire"
    Each event payload carries a monotonic `_seq`. Traits dedupe by value, so
    without it a repeated event (re-clicking the same row) would not re-trigger
    `reactive_read`. `_seq` is the anywidget stand-in for Shiny's
    `priority:"event"`.

## Inline row inputs

Render a control per row and receive its events:

```python
opts = (Options(df)
        .col_checkbox("select", value_col="active")  # seeds checked from a column
        .col_button("act", label="Ping"))

dt2(df, options=opts)
```

- A checkbox click sets `row_check = {row, value}`.
- A button click sets `row_button = {row, id}`.

`row` is the **1-based data row index** (independent of the visual sort order).
See [`examples/app_proxy_inputs.py`](examples.md).
