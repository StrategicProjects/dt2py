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

### Phase 2 — extensions
- [ ] Add npm extension deps (buttons, select, responsive, fixedheader,
      fixedcolumns, rowgroup, rowreorder, colreorder, keytable, scroller,
      searchbuilder, searchpanes, staterestore, columncontrol, datetime)
- [ ] jszip/pdfmake/moment for Buttons export
- [ ] Modular loading parity (only ship what's requested)

### Phase 3 — Shiny integration
- [x] **Server-side processing (de-risked first):** DataTables `ajax` as a
      function routed over the Comm; `dt2.server.process_ssp` ports the R
      filter/order/paginate logic (no query-string parse needed — request
      arrives structured). Widget keeps full data Python-side; `_on_msg`
      replies with a correlated `dt2_ssp_response`. Unit + handler tests green.
      **Still to verify:** the live Comm round-trip in a browser (needs frontend).
- [ ] Proxy parity (remaining `R/dt2_proxy.R` methods; skeleton in place)
- [ ] Events parity (state, row checkbox/button inline inputs)
- [ ] Inline inputs (`dt2_inputs`) rendered + wired to reactivity
- [ ] Per-column search in SSP (R does global only — match, then optionally extend)

### Phase 4 — polish & release
- [ ] Tests (pytest + a JS smoke harness)
- [ ] Docs site / examples gallery
- [ ] CI (build JS, run tests), commit built bundle
- [ ] PyPI publish (`dt2`)

## Open questions
- Bundle size: shipping all extensions vs. lazy/optional extras. Lean toward
  optional `pip install dt2[buttons,searchpanes,...]` extras mapping to JS
  chunks, to keep the base wheel small.
- SSP transport latency over Comm vs. a Starlette route — benchmark in Phase 3.
