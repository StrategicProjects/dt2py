# Changelog

All notable changes to **dt2** (the Python port) are documented here.
Format loosely follows [Keep a Changelog](https://keepachangelog.com).

## [0.1.0] — 2026-06-26

First release. Feature parity with the R
[DT2](https://github.com/StrategicProjects/DT2) package, verified live in a
browser (Shiny for Python).

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
- **moment.js bundled** — powers `format_datetime` and `format_time_relative`
  (`DataTable.render.datetime` requires it).

### Fixed
- Verified end to end in a real browser (Shiny for Python): core render,
  selection events, SSP (50k rows: render + server-side search), config
  renderers (number/datetime/custom), extensions (RowGroup, Buttons), and inline
  inputs with `row_check`/`row_button` events.
- `format_datetime` failed ("Formatted date without Moment.js or Luxon"), which
  surfaced as a blocking `alert()` — moment is now bundled and DataTables'
  `errMode` is set to `throw` so future warnings log instead of freezing the tab.
- `Options.buttons()` now places buttons in the layout when no `target` is given,
  so they actually render (DataTables 2.x only shows buttons referenced there).

### Known gaps / deferred
- PDF export (pdfmake) not bundled; `format_time_relative` needs
  moment-with-locales for non-`en` locales; extensions are all-bundled (no
  modular/lazy loading yet); SSP search is global-only (matches R).
