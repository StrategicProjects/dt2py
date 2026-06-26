# dt2 (Python) — parity roadmap

Goal: **feature parity** with the R DT2 package, delivered via anywidget for
Shiny for Python. The DataTables v2 runtime (2.3.4) and extensions are reused;
the work is reimplementing the R binding layer in Python and re-wiring the
Shiny transport onto the anywidget Comm.

## Architecture decisions (locked)

- **Repo:** `StrategicProjects/dt2py` (separate from the R repo).
- **PyPI / import name:** `dt2`.
- **Mechanism:** anywidget (`shinywidgets` bridges it to Shiny for Python).
- **JS:** bundled with esbuild from `js/index.js` → `src/dt2/static/index.{js,css}`.
- **DataTables:** pinned to `2.3.4` / jQuery `3.7.1` to match the R bundle.

## Transport mapping (R → Python)

| R (htmlwidgets / Shiny)                  | Python (anywidget)                          |
| ---------------------------------------- | ------------------------------------------- |
| `Shiny.setInputValue(id+'_state', v)`    | `model.set('state', v); model.save_changes()` |
| `Shiny.setInputValue(id+'_row_check')`   | trait + `model.save_changes()`              |
| `Shiny.addCustomMessageHandler(id+'_proxy')` | `model.on('msg:custom', fn)`            |
| SSP Ajax via custom message round-trip   | `model.send(req)` + `model.on('msg:custom')` reply |

## Phases

### Phase 0 — scaffold ✅ (this commit)
- [x] Repo, pyproject (hatchling), package.json (esbuild)
- [x] anywidget adapter `js/index.js` (core render + proxy/event skeleton)
- [x] `Dt2` widget + `dt2()` constructor (pandas/polars/records)
- [x] Shiny example app
- [x] Build bundle; widget constructs, traits populate, app serves (HTTP 200)
- [ ] Visual in-browser render + selection (needs Chrome extension online)

### Phase 1 — config parity ✅
- [x] `Options` builder (chainable) covering the R `dt2_options`/`dt2_formats`
      surface: `order`, `search_global`, `length_menu`, `language`, `use_buttons`,
      `cols_align/width/hide/escape`, `format_number/datetime/number_abbrev/time_relative`,
      `cols_render`, `cols_render_orthogonal`, `register/use_renderer`.
- [x] Name→index resolution (`_name_to_idx`, ported with warnings); seed names
      from a DataFrame/records via `Options(df)` — removes the R "forgot to set
      options$columns" footgun.
- [x] **`JS()` parity for `htmlwidgets::JS()`:** Python marks renderer source as
      `{"__dt2_js__": code}`; `index.js` `reviveJs()` recursively compiles markers
      into functions with `DataTable`/`$`/`moment` in scope. Proven in node.
- [x] `dt2(df, options=opts, **kw)` merge. 22 unit tests + JS revive test green.
- [x] Quote-safe values via `json.dumps` (`_js_str`, port of `.dt2_js_str`).

### Phase 2 — extensions ✅
- [x] All 15 extensions bundled via esbuild (`js/extensions.js`): Buttons,
      Select, Responsive, FixedHeader, FixedColumns, KeyTable, Scroller,
      RowGroup, RowReorder, ColReorder, DateTime, SearchBuilder, SearchPanes,
      StateRestore, ColumnControl. Verified present in the built bundle.
- [x] jszip bundled (Excel/CSV/copy export via `window.JSZip`).
- [x] Python activation helpers on `Options`: `select/responsive/fixed_header/
      fixed_columns/key_table/col_reorder/row_reorder/row_group/scroller/
      search_panes/search_builder/state_restore/column_control/buttons`, plus
      `extensions()` registry (parity with R `dt2_extensions()`).
- [x] `buttons(target=...)` relocation (port of R `dt2_buttons`) handled in JS.
- [x] `_momentLocale` applied client-side. 15 extension tests green (46 total).
- [ ] **Deferred follow-ups:** pdfmake (PDF export, ~1MB) as an optional extra;
      moment-with-locales for `format_time_relative`; modular/lazy loading so the
      base wheel ships only requested extensions (parity with R's per-ext loading).

### Phase 3 — Shiny integration
- [x] **Server-side processing (de-risked first):** DataTables `ajax` as a
      function routed over the Comm; `dt2.server.process_ssp` ports the R
      filter/order/paginate logic (no query-string parse needed — request
      arrives structured). Widget keeps full data Python-side; `_on_msg`
      replies with a correlated `dt2_ssp_response`. Unit + handler tests green.
      **Still to verify:** the live Comm round-trip in a browser (needs frontend).
- [x] **Proxy parity** (`cmd` protocol mirroring R/dt2_proxy.R): widget methods
      `replace_data`, `draw`, `reload`, `order`, `search`, `clear_search`,
      `page`, `select_rows`. Order resolves header names → indices client-side.
- [x] **Events parity**: enriched `state` ({reason, order, search, page,
      selected}) + `selected_rows`; a monotonic `_seq` makes event traits
      re-fire under `reactive_read` (anywidget equivalent of Shiny's
      `priority:"event"`).
- [x] **Inline inputs** (port of R/dt2_inputs.R): `Options.col_checkbox` /
      `col_button` render delegated controls; clicks set `row_check` /
      `row_button` event traits. Verified in node (render compiles, seeds
      checked state) + 12 tests (58 total). Example `app_proxy_inputs.py`.
- [ ] Per-column search in SSP (R does global only — match, then optionally extend)

### Phase 4 — polish & release
- [x] Tests: 58 pytest cases (config, extensions, SSP, proxy/inputs) + node
      smoke checks for the JS adapter. `[tool.pytest.ini_options]` configured.
- [x] CI (`.github/workflows/ci.yml`): builds the JS bundle, asserts the
      committed `src/dt2/static` is fresh, installs and runs pytest on Python
      3.9/3.11/3.13; syntax-checks the adapter sources.
- [x] Wheel verified: includes the built bundle; fresh `pip install` works with
      no Node toolchain (703kb bundle, 15 extensions, widget builds).
- [x] Release workflow (`release.yml`): builds + publishes to PyPI via Trusted
      Publishing on a published GitHub Release (maintainer-triggered).
- [x] README (full API), CHANGELOG, examples gallery (5 runnable apps).
- [x] **Live in-browser verification** (Shiny for Python): core render +
      selection, SSP (50k rows: render + search), config renderers
      (number/datetime/custom badge), extensions (RowGroup + Buttons), and
      inline inputs with row_check/row_button events — all confirmed. Two bugs
      found & fixed: moment.js now bundled (datetime), buttons placed in layout.
- [ ] **PyPI publish** — maintainer action: configure the PyPI trusted publisher,
      then publish a GitHub Release to trigger `release.yml`.

## Open questions
- Bundle size: shipping all extensions vs. lazy/optional extras. Lean toward
  optional `pip install dt2[buttons,searchpanes,...]` extras mapping to JS
  chunks, to keep the base wheel small.
- SSP transport latency over Comm vs. a Starlette route — benchmark in Phase 3.
