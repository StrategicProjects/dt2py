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
- [ ] Build bundle, smoke-test render + selection in a real app

### Phase 1 — config parity
- [ ] Column helpers (`dt2_cols_*`, formats, ordering) → Python equivalents
- [ ] Name→index resolution (port `.dt2_name_to_idx`, with warnings)
- [ ] Quote-safe value handling (Python serializes to JSON natively — verify)
- [ ] Options builder covering the R `dt2_options` surface

### Phase 2 — extensions
- [ ] Add npm extension deps (buttons, select, responsive, fixedheader,
      fixedcolumns, rowgroup, rowreorder, colreorder, keytable, scroller,
      searchbuilder, searchpanes, staterestore, columncontrol, datetime)
- [ ] jszip/pdfmake/moment for Buttons export
- [ ] Modular loading parity (only ship what's requested)

### Phase 3 — Shiny integration
- [ ] Proxy parity (all `R/dt2_proxy.R` methods)
- [ ] Events parity (state, row checkbox/button inline inputs)
- [ ] Inline inputs (`dt2_inputs`) rendered + wired to reactivity
- [ ] Server-side processing: DataTables `ajax` as a function routed over the
      Comm; Python side ports `.dt2_parse_ssp_request` / paging / filtering

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
