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

  const data = model.get("data") || [];
  const columns = (model.get("columns") || []).map(toColumn);
  const options = model.get("options") || {};

  const config = Object.assign({ data, columns }, options);

  const dt = new DataTable(table, config);

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

  // --- Python -> JS: proxy / custom messages ---
  const onMsg = (msg) => handleProxy(dt, msg);
  model.on("msg:custom", onMsg);

  return () => {
    model.off("msg:custom", onMsg);
    dt.off(".dt2");
    dt.destroy();
    el.innerHTML = "";
  };
}

export default { render };
