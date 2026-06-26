// DataTables v2 extensions — side-effect imports register them onto the shared
// DataTable instance (esbuild dedupes datatables.net-bs5, so the `DataTable`
// imported in index.js is the same object these augment).
//
// All extensions are bundled (parity-complete); they activate only when their
// option is set (buttons, select, responsive, fixedHeader, ...). The R package's
// modular per-extension loading is a download-size optimization, deferred here
// to optional extras (see ROADMAP Phase 2 follow-ups).

// --- jszip enables Buttons' Excel/CSV-zip export (uses window.JSZip global).
//     pdfmake (PDF export) is intentionally NOT bundled — it is ~1MB; PDF is a
//     deferred optional extra. ---
import JSZip from "jszip";
if (typeof window !== "undefined" && !window.JSZip) window.JSZip = JSZip;

// --- Buttons (core + bs5 bridge + button types) ---
import "datatables.net-buttons-bs5";
import "datatables.net-buttons/js/buttons.colVis.mjs";
import "datatables.net-buttons/js/buttons.html5.mjs";
import "datatables.net-buttons/js/buttons.print.mjs";

// --- selection / layout / navigation ---
import "datatables.net-select-bs5";
import "datatables.net-responsive-bs5";
import "datatables.net-fixedheader-bs5";
import "datatables.net-fixedcolumns-bs5";
import "datatables.net-keytable-bs5";
import "datatables.net-scroller-bs5";

// --- grouping / reordering ---
import "datatables.net-rowgroup-bs5";
import "datatables.net-rowreorder-bs5";
import "datatables.net-colreorder-bs5";

// --- searching / state (DateTime is a SearchBuilder dependency) ---
import "datatables.net-datetime";
import "datatables.net-searchbuilder-bs5";
import "datatables.net-searchpanes-bs5";
import "datatables.net-staterestore-bs5";
import "datatables.net-columncontrol-bs5";

// --- extension CSS (bootstrap5 variants). DateTime ships only .scss, skipped. ---
import "datatables.net-buttons-bs5/css/buttons.bootstrap5.min.css";
import "datatables.net-select-bs5/css/select.bootstrap5.min.css";
import "datatables.net-responsive-bs5/css/responsive.bootstrap5.min.css";
import "datatables.net-fixedheader-bs5/css/fixedHeader.bootstrap5.min.css";
import "datatables.net-fixedcolumns-bs5/css/fixedColumns.bootstrap5.min.css";
import "datatables.net-keytable-bs5/css/keyTable.bootstrap5.min.css";
import "datatables.net-scroller-bs5/css/scroller.bootstrap5.min.css";
import "datatables.net-rowgroup-bs5/css/rowGroup.bootstrap5.min.css";
import "datatables.net-rowreorder-bs5/css/rowReorder.bootstrap5.min.css";
import "datatables.net-colreorder-bs5/css/colReorder.bootstrap5.min.css";
import "datatables.net-searchbuilder-bs5/css/searchBuilder.bootstrap5.min.css";
import "datatables.net-searchpanes-bs5/css/searchPanes.bootstrap5.min.css";
import "datatables.net-staterestore-bs5/css/stateRestore.bootstrap5.min.css";
import "datatables.net-columncontrol-bs5/css/columnControl.bootstrap5.min.css";
