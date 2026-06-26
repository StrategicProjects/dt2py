// dt2 — anywidget adapter for DataTables v2.
//
// This is the Python-side equivalent of inst/htmlwidgets/dt2.js in the R
// package. The DataTables feature surface is reused as-is; what changes is the
// TRANSPORT: the R binding talks to Shiny through `window.Shiny`
// (setInputValue / addCustomMessageHandler), whereas here we talk to the
// Python kernel through the anywidget `model` (Comm). shinywidgets bridges that
// Comm to Shiny for Python reactivity.
//
//   R  htmlwidgets                     Python  anywidget
//   ------------------------------     ----------------------------------
//   Shiny.setInputValue(id+'_x', v) -> model.set('x', v); model.save_changes()
//   Shiny.addCustomMessageHandler   -> model.on('msg:custom', fn)
//   Ajax SSP via custom message     -> model.send(req) + 'msg:custom' reply

import $ from "jquery";
import DataTable from "datatables.net-bs5";
import "datatables.net-bs5/css/dataTables.bootstrap5.min.css";
// Register all DataTables extensions onto the shared DataTable (side effects).
import "./extensions.js";

const JS_MARKER = "__dt2_js__";

/** Compile a `{__dt2_js__: code}` marker into a function, with DataTable/$/moment
 *  in scope (DataTable is a module import here, not a global like in the R build).
 *  Trust boundary: `code` is supplied by the app author via dt2.JS(...) — the same
 *  trust level as the app's own Python — never end-user input. This mirrors
 *  htmlwidgets::JS()/DT in R; it is not an injection sink for untrusted data. */
function compileJs(code) {
  try {
    // eslint-disable-next-line no-new-func
    return new Function(
      "DataTable",
      "$",
      "moment",
      "return (" + code + ");",
    )(DataTable, $, typeof window !== "undefined" ? window.moment : undefined);
  } catch (e) {
    console.error("[dt2] failed to compile JS renderer:", code, e);
    return undefined;
  }
}

/** Recursively revive JS() markers anywhere in the config (mirror of
 *  htmlwidgets::JS handling). Real functions/values pass through untouched. */
function reviveJs(value) {
  if (Array.isArray(value)) return value.map(reviveJs);
  if (value && typeof value === "object") {
    if (typeof value[JS_MARKER] === "string") return compileJs(value[JS_MARKER]);
    const out = {};
    for (const k of Object.keys(value)) out[k] = reviveJs(value[k]);
    return out;
  }
  return value;
}

/** Normalize a column spec entry into a DataTables column definition. */
function toColumn(c) {
  if (typeof c === "string") return { data: c, title: c, defaultContent: "" };
  return Object.assign({ defaultContent: "" }, c);
}

/** Resolve an order column reference (1-based index or header name) to a
 *  0-based DataTables column index. */
function resolveOrderCol(dt, col) {
  if (typeof col === "string") {
    const idx = dt
      .columns()
      .indexes()
      .toArray()
      .find((i) => dt.column(i).header().textContent.trim() === col);
    return idx != null ? idx : 0;
  }
  return parseInt(col, 10) - 1;
}

/** Python -> JS: proxy commands (mirror of R/dt2_proxy.R, `cmd` protocol). */
function handleProxy(dt, msg) {
  const cmd = msg && (msg.cmd || msg.method);
  if (!cmd) return;
  try {
    switch (cmd) {
      case "replaceData":
        dt.clear();
        dt.rows.add(msg.data || []);
        dt.draw(false);
        break;
      case "draw":
        dt.draw(msg.resetPaging === true);
        break;
      case "reload": // server-side re-fetch
        dt.ajax.reload(null, msg.resetPaging !== false);
        break;
      case "order": {
        const spec = (msg.args && msg.args[0]) || [];
        dt.order(spec.map(([col, dir]) => [resolveOrderCol(dt, col), dir])).draw();
        break;
      }
      case "search":
        dt.search(msg.args[0], msg.args[1], msg.args[2], msg.args[3]).draw();
        break;
      case "clearSearch":
        dt.search("").columns().search("").draw();
        break;
      case "page":
        if (msg.args[0] === "number") dt.page(parseInt(msg.args[1], 10) - 1).draw(false);
        else dt.page(msg.args[0]).draw(false);
        break;
      case "selectRows": {
        if (msg.args[1]) dt.rows().deselect();
        const zero = (msg.args[0] || []).map((i) => i - 1);
        dt.rows(zero).select();
        break;
      }
      default:
        console.warn("[dt2] unknown proxy cmd:", cmd);
    }
  } catch (e) {
    console.error("[dt2] proxy", cmd, "failed:", e);
  }
}

function render({ model, el }) {
  el.classList.add("dt2-container");

  const table = document.createElement("table");
  table.className = "table table-striped table-bordered dt2-table";
  table.style.width = "100%";
  el.appendChild(table);

  const columns = (model.get("columns") || []).map(toColumn).map(reviveJs);
  const options = reviveJs(model.get("options") || {});
  const serverSide = !!model.get("server_side");

  // dt2-only directives, not DataTables options — pull them out of the config.
  const buttonsTarget = options.dt2_buttons_target;
  const momentLocale = options._momentLocale;
  delete options.dt2_buttons_target;
  delete options._momentLocale;
  if (momentLocale && typeof window !== "undefined" && window.moment) {
    try { window.moment.locale(momentLocale); } catch (e) { /* ignore */ }
  }

  // --- server-side processing: ajax as a function over the anywidget Comm ---
  // The DataTables request is forwarded to Python, which replies with a
  // matching `dt2_ssp_response`. Correlated by an incrementing requestId.
  let reqCounter = 0;
  const pending = new Map();
  const config = Object.assign({ columns }, options);
  if (serverSide) {
    config.serverSide = true;
    config.ajax = (request, callback) => {
      const requestId = ++reqCounter;
      pending.set(requestId, callback);
      model.send({ dt2_ssp: true, requestId, request });
    };
  } else {
    config.data = model.get("data") || [];
  }

  const dt = new DataTable(table, config);

  // Relocate the Buttons container to a custom selector (port of dt2_buttons target).
  if (buttonsTarget && dt.buttons) {
    try {
      const node = dt.buttons().container();
      const dest = document.querySelector(buttonsTarget);
      if (node && dest) dest.appendChild(node instanceof Element ? node : node[0]);
    } catch (e) {
      console.warn("[dt2] could not move buttons to", buttonsTarget, e);
    }
  }

  // Event traits dedupe by value, but DataTables can fire the "same" event
  // twice (e.g. clicking an already-selected row). A monotonic seq guarantees
  // the trait changes every time, so Shiny's reactive_read always re-fires —
  // the anywidget equivalent of Shiny's {priority:"event"} inputs.
  let seq = 0;

  // --- JS -> Python: selection ---
  const pushSelection = () => {
    const rows = dt
      .rows({ selected: true })
      .indexes()
      .toArray()
      .map((i) => i + 1); // 1-based, like R
    model.set("selected_rows", rows);
    model.save_changes();
  };
  dt.on("select.dt2 deselect.dt2", pushSelection);

  // --- JS -> Python: rich table state (mirror of dt2.js pushState) ---
  const pushState = (reason) => {
    let selected = [];
    try { selected = dt.rows({ selected: true }).indexes().toArray(); } catch (e) { /* no Select */ }
    model.set("state", {
      reason,
      order: dt.order(),
      search: dt.search(),
      page: dt.page.info(),
      selected,
      _seq: ++seq,
    });
    model.save_changes();
  };
  dt.on(
    "draw.dt2 order.dt2 search.dt2 page.dt2 select.dt2 deselect.dt2",
    (e) => pushState(e.type),
  );

  // --- JS -> Python: delegated inline row inputs (checkbox / button) ---
  const $tbl = $(table);
  $tbl.on("change.dt2inputs", "input.dt2-row-checkbox", function () {
    const row = dt.row($(this).closest("tr")).index();
    model.set("row_check", { row: row + 1, value: this.checked, _seq: ++seq });
    model.save_changes();
  });
  $tbl.on("click.dt2inputs", "button.dt2-row-button", function () {
    const row = dt.row($(this).closest("tr")).index();
    model.set("row_button", { row: row + 1, id: this.id, _seq: ++seq });
    model.save_changes();
  });

  // --- Python -> JS: proxy commands + SSP responses ---
  const onMsg = (msg) => {
    if (msg && msg.dt2_ssp_response) {
      const cb = pending.get(msg.requestId);
      if (cb) {
        pending.delete(msg.requestId);
        cb(msg.payload);
      }
      return;
    }
    handleProxy(dt, msg);
  };
  model.on("msg:custom", onMsg);

  return () => {
    model.off("msg:custom", onMsg);
    pending.clear();
    $tbl.off(".dt2inputs");
    dt.off(".dt2");
    dt.destroy();
    el.innerHTML = "";
  };
}

export default { render };
