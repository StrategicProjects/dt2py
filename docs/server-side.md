# Server-side processing

For large tables, keep the data Python-side and let DataTables fetch one page at
a time. Pass `server_side=True`:

```python
dt2(big_df, server_side=True, pageLength=25, searching=True, ordering=True)
```

The full dataset stays in Python (it is **not** serialized to the client). When
the table needs a page, its `ajax` request is sent over the anywidget Comm to
Python, where [`dt2.server.process_ssp`](api.md#dt2.server.process_ssp) filters,
orders and paginates, and replies with just that page.

## How it works

```
browser                                   Python
───────                                   ──────
DataTables ajax(request)  ──Comm──▶  Dt2._on_msg
                                          process_ssp(request, full_data, cols)
table.draw()              ◀─Comm──   reply { draw, recordsTotal,
                                              recordsFiltered, data }
```

Requests are correlated by an incrementing `requestId`, so concurrent draws never
cross their replies.

## Semantics

- **Global search**: case-insensitive substring across all columns (matches the
  R package; per-column search is a deferred extra).
- **Ordering**: cascading stable sort; missing values sort last.
- **Paging**: `length = -1` returns all rows.

This mirrors the R `dt2_ssp_handler`. The whole path is pure and unit-tested, so
behaviour is identical whether or not a browser is attached.

## Updating data

```python
tbl.widget.replace_data(new_df)   # swaps the Python-side data and re-fetches
```

See [`examples/app_serverside.py`](examples.md) for a 50,000-row demo.
