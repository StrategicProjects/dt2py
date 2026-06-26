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
reactive_read(tbl.widget, "state")          # {reason, order, search, page, selected}
reactive_read(tbl.widget, "row_check")      # {row, value}  (inline checkbox)
reactive_read(tbl.widget, "row_button")     # {row, id}     (inline button)
```

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
