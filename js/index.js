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

/** R -> Python: proxy commands (mirror of R/dt2_proxy.R). */
function handleProxy(dt, msg) {
  if (!msg || !msg.method) return;
  switch (msg.method) {
    case "reload":
      dt.ajax.reload(null, msg.resetPaging !== false);
      break;
    case "clearSearch":
      dt.search("").columns().search("").draw();
      break;
    case "search":
      dt.search(msg.value || "").draw();
      break;
    case "selectRows": {
      dt.rows().deselect();
      (msg.rows || []).forEach((r) => dt.row(r - 1).select());
      break;
    }
    case "selectPage":
      dt.page(msg.page - 1).draw("page");
      break;
    case "updateData":
      dt.clear();
      dt.rows.add(msg.data || []).draw(false);
      break;
    case "reloadData":
      dt.draw(msg.resetPaging !== false);
      break;
    default:
      console.warn("[dt2] unknown proxy method:", msg.method);
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

  // --- JS -> Python: table state (search / order / page) ---
  const pushState = (type) => {
    model.set("state", {
      type,
      search: dt.search(),
      order: dt.order(),
      page: dt.page(),
      pageLength: dt.page.len(),
    });
    model.save_changes();
  };
  dt.on(
    "draw.dt2 order.dt2 search.dt2 page.dt2",
    (e) => pushState(e.type),
  );

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
    dt.off(".dt2");
    dt.destroy();
    el.innerHTML = "";
  };
}

export default { render };
