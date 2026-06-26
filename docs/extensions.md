# Extensions

All 15 DataTables v2 extensions are bundled — there is nothing extra to install.
Each activates through its `Options` helper (which sets the DataTables option the
extension reads).

```python
from dt2 import Options, dt2

opts = (Options(df)
        .buttons(["copyHtml5", "csvHtml5", "excelHtml5", "print"])
        .select({"style": "os"})
        .responsive()
        .fixed_header()
        .row_group("field"))

dt2(df, options=opts)
```

`dt2.extensions()` returns the bundled list and versions.

## Activation helpers

| Helper | DataTables option | Extension |
| --- | --- | --- |
| `buttons(ids, target=None)` | `buttons` (+ layout) | Buttons |
| `select(cfg=True)` | `select` | Select |
| `responsive(cfg=True)` | `responsive` | Responsive |
| `fixed_header(cfg=True)` | `fixedHeader` | FixedHeader |
| `fixed_columns(cfg)` | `fixedColumns` | FixedColumns |
| `key_table(cfg=True)` | `keys` | KeyTable |
| `scroller(scroll_y, cfg=True)` | `scroller` (+ `scrollY`) | Scroller |
| `row_group(data_src)` | `rowGroup` | RowGroup |
| `row_reorder(cfg=True)` | `rowReorder` | RowReorder |
| `col_reorder(cfg=True)` | `colReorder` | ColReorder |
| `search_panes(cfg=True)` | `searchPanes` | SearchPanes |
| `search_builder(cfg=True)` | `searchBuilder` | SearchBuilder |
| `state_restore(cfg=True)` | `stateRestore` (+ `stateSave`) | StateRestore |
| `column_control(cfg=True)` | `columnControl` | ColumnControl |

(DateTime is bundled as a dependency of SearchBuilder.)

## Buttons & export

```python
Options(df).buttons(["copyHtml5", "csvHtml5", "excelHtml5", "print"])
```

- Copy / CSV / Excel / Print work out of the box (**jszip** is bundled).
- **PDF export** (`pdfHtml5`) needs `pdfmake`, which is **not** bundled (it is
  ~1 MB) — a deferred optional extra.
- Buttons are placed in the layout automatically. To relocate them into your own
  container, pass `target="#my-toolbar"`.

For the simpler layout-based variant (button ids + a CSS class in a chosen
layout slot), use `use_buttons(...)`.
