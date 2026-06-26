# Configuring tables

`Options` is a chainable builder mirroring the R package's pipe helpers. Seed it
with your data (or `columns=[...]`) so column names resolve to indices:

```python
from dt2 import Options, JS, dt2

opts = (Options(df)
        .cols_align(["revenue"], "right")
        .format_number(["revenue"], thousands=".", decimal=",", digits=2, prefix="R$ ")
        .format_datetime(["updated"], from_="YYYY-MM-DD", to="DD/MM/YYYY")
        .order(("revenue", "desc"))
        .length_menu([10, 25, 50, -1]))

dt2(df, options=opts)
```

`dt2(df, options=opts, **kw)` merges builder options with keyword options (the
keyword ones win on conflict).

## Column appearance

```python
(Options(df)
 .cols_align(["score"], "center")     # text-start / -center / -end
 .cols_width({"name": "180px"})
 .cols_hide(["internal_id"])
 .cols_escape(["html_col"], escape=False))  # render raw HTML (trusted only)
```

Columns are referenced by **name** (resolved against the seeded column list) or
by **1-based index**. Unknown names warn loudly rather than failing silently.

## Number & date formatting

```python
(Options(df)
 .format_number(["amount"], thousands=".", decimal=",", digits=2, prefix="R$ ")
 .format_number_abbrev(["views"], digits=1)        # 1.2k / 3.4M / 5.6B
 .format_datetime(["ts"], from_="YYYY-MM-DD", to="DD/MM/YYYY")
 .format_time_relative(["ts"]))                    # "3 days ago" (needs moment)
```

!!! note
    `format_datetime` / `format_time_relative` use `DataTable.render.datetime`
    and `moment.js`, which is bundled. Non-`en` locales for relative time need
    moment-with-locales (a deferred extra).

## Raw JavaScript renderers

`JS(...)` is the Python parity for `htmlwidgets::JS()`. The source is revived
into a real function in the browser, with `DataTable`, `$` and `moment` in scope:

```python
opts = Options(df).cols_render(
    ["score"],
    JS(
        "function(d,t){ if(t!=='display') return d;"
        " var c = d>=0.75?'success':d>=0.5?'warning':'danger';"
        " return '<span class=\"badge text-bg-'+c+'\">'+(d*100).toFixed(0)+'%</span>'; }"
    ),
)
```

For orthogonal data (different output for display vs sort vs filter), use
`cols_render_orthogonal(display=JS(...), sort=JS(...), ...)`. Reusable renderers
can be registered by name:

```python
from dt2 import register_renderer
register_renderer("pct", JS("function(d,t){ return (d*100).toFixed(0)+'%'; }"))
Options(df).use_renderer(["score"], "pct")
```

## Ordering, search, paging, language

```python
(Options(df)
 .order(("year", "desc"), ("name", "asc"))    # multi-column
 .search_global("ada")
 .length_menu([10, 25, -1])                    # -1 = "All"
 .language(url="https://cdn.datatables.net/plug-ins/2.3.3/i18n/pt-BR.json"))
```

See the full surface in the [API reference](api.md#dt2.Options).
