# Changelog

All notable changes to **dt2** (the Python port) are documented here.
Format loosely follows [Keep a Changelog](https://keepachangelog.com).

## [Unreleased]

Initial development toward feature parity with the R
[DT2](https://github.com/StrategicProjects/DT2) package.

### Added
- **Core widget** (`dt2()`, `Dt2`): anywidget binding for DataTables v2 (2.3.4),
  for Shiny for Python and Jupyter. Accepts pandas/polars frames and records.
- **Config builder** (`Options`): chainable port of the R `dt2_options` /
  `dt2_formats` helpers — `order`, `search_global`, `length_menu`, `language`,
  `use_buttons`, `cols_align/width/hide/escape`,
  `format_number/datetime/number_abbrev/time_relative`, `cols_render`,
  `cols_render_orthogonal`, `register_renderer`/`use_renderer`.
- **`JS()`**: parity for `htmlwidgets::JS()` — renderer source is revived into a
  real function client-side (with `DataTable`/`$`/`moment` in scope).
- **Extensions** (all 15 bundled): Buttons, Select, Responsive, FixedHeader,
  FixedColumns, KeyTable, Scroller, RowGroup, RowReorder, ColReorder, DateTime,
  SearchBuilder, SearchPanes, StateRestore, ColumnControl. Activation helpers on
  `Options` + an `extensions()` registry. jszip bundled for Excel/CSV export.
- **Server-side processing** (`server_side=True`): data stays Python-side and
  pages are filtered/ordered/paginated over the Comm (`dt2.server.process_ssp`).
- **Proxy API** on the widget: `replace_data`, `draw`, `reload`, `order`,
  `search`, `clear_search`, `page`, `select_rows`.
- **Events**: `selected_rows`, `state`, `row_check`, `row_button` traits
  (read reactively with `shinywidgets.reactive_read`).
- **Inline inputs**: `Options.col_checkbox`, `Options.col_button`.

### Known gaps / deferred
- Live in-browser Comm transport not yet visually verified.
- PDF export (pdfmake) not bundled; `format_time_relative` needs
  moment-with-locales; extensions are all-bundled (no modular/lazy loading yet);
  SSP search is global-only (matches R).
