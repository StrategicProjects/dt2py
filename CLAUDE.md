# CLAUDE.md

Guidance for working in the **dt2** (Python) repository.

## What this package is

`dt2` is the **Python port** of the R [DT2](https://github.com/StrategicProjects/DT2)
package: an [anywidget](https://anywidget.dev) binding for **DataTables v2**, for
[Shiny for Python](https://shiny.posit.co/py/) (and usable in Jupyter). It
configures DataTables via plain Python (1:1 with the JS API), reusing the same
DataTables runtime and extensions as the R package.

- Python: `src/dt2/`  ·  JS adapter: `js/`  ·  built bundle: `src/dt2/static/`
- Examples: `examples/`  ·  tests: `tests/`
- Published on PyPI as `dt2`. Companion to (not a fork of) the R package.

## Layout

- `src/dt2/widget.py` — `Dt2` anywidget + `dt2()` constructor + proxy methods + SSP `on_msg`.
- `src/dt2/options.py` — `Options` builder, `JS()` marker, name→index resolution, `extensions()`.
- `src/dt2/server.py` — `process_ssp()` (server-side filter/order/paginate).
- `js/index.js` — anywidget adapter: render, `reviveJs`, proxy `handleProxy`, events, SSP ajax.
- `js/extensions.js` — side-effect imports of all 15 DataTables extensions + jszip + moment.

## Common commands

```bash
npm install              # once
npm run build            # esbuild js/ -> src/dt2/static/index.{js,css}  (REQUIRED after any js/ change)
npm run dev              # esbuild watch

uv pip install -e ".[shiny,pandas,dev]"
python -m pytest         # 60 tests (config, extensions, SSP, proxy/inputs)

uv build                 # sdist + wheel
uvx twine check dist/*   # validate PyPI metadata

# run an example in a browser
.venv/bin/shiny run examples/app_extensions.py --port 8770
```

## Conventions / gotchas

- **The JS bundle is committed.** After editing anything in `js/`, run
  `npm run build` and commit `src/dt2/static/`. CI fails if it is stale
  (`git diff --exit-code -- src/dt2/static/`).
- **Transport = anywidget Comm, NOT `window.Shiny`.** `js/index.js` is a rewrite
  of the R `dt2.js` glue. Mapping: `Shiny.setInputValue` → `model.set(...)` +
  `model.save_changes()` (a synced trait); `addCustomMessageHandler` →
  `model.on('msg:custom')`; SSP ajax → `model.send` request + `msg:custom` reply
  (correlated by `requestId`).
- **`JS()` is the `htmlwidgets::JS()` parity.** Python marks renderer source as
  `{"__dt2_js__": code}`; `reviveJs()` recursively compiles markers into
  functions with `DataTable`/`$`/`moment` **passed into scope** — because in the
  bundle `DataTable` is a module import, not a `window` global like in R.
- **Event traits need a monotonic `_seq`.** Traits dedupe by value, so repeated
  events (re-click) wouldn't re-fire under `reactive_read`. `_seq` is the
  anywidget stand-in for Shiny's `priority:"event"`. Applies to `state`,
  `row_check`, `row_button`.
- **`Options(df)` seeds the column-name map** used by `_name_to_idx` (port of
  `.dt2_name_to_idx`, warns on unknown/unset). This removes the R
  "forgot to set options$columns" footgun. Names → 1-based indices; columnDefs
  `targets` are 0-based.
- **`format_datetime`/`format_time_relative` need moment** (`DataTable.render.datetime`
  requires it) — moment is bundled in `js/extensions.js`.
- **Buttons must be placed in `layout`** to render in DataTables 2.x.
  `Options.buttons()` adds `layout.topStart` when no `target` is given.
- **`DataTable.ext.errMode = "throw"`** (set in `index.js`): DataTables warnings
  default to a blocking `alert()` that freezes the tab (and the browser-automation
  channel). Keep it as `throw` so issues log to the console instead.

## Pinned versions

DataTables `2.3.4` / jQuery `3.7.1` (match the R vendored bundle). Extension npm
packages pinned in `package.json`; `_EXTENSIONS` in `options.py` mirrors them.

## Release flow

1. Bump `version` in `pyproject.toml` **and** `__version__` in `src/dt2/__init__.py`.
2. Update `CHANGELOG.md` (`[X.Y.Z] — date`).
3. `npm run build` + commit; `python -m pytest`; `uv build` + `uvx twine check dist/*`.
4. Push, then **publish a GitHub Release** with tag `vX.Y.Z` — this triggers
   `.github/workflows/release.yml`, which builds and publishes to PyPI via
   **Trusted Publishing** (OIDC, no stored token; PyPI publisher must be
   configured: project `dt2`, owner `StrategicProjects`, repo `dt2py`, workflow
   `release.yml`, environment `pypi`).

## Deferred / optional extras

pdfmake (PDF export), moment-with-locales (non-`en` `format_time_relative`),
modular/lazy extension loading (currently all bundled, ~766kb js), per-column
SSP search (currently global-only, matching R).

## House rules

- Branch per change + PR is not enforced here (solo pre-1.0), but keep commits
  scoped and the bundle in sync with `js/`.
- Never commit `node_modules/`, `dist/`, `.DS_Store`.
