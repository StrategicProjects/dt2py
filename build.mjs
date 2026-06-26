// Bundles the anywidget adapter + DataTables v2 stack into src/dt2/static/.
// Output: index.js (ESM, anywidget _esm) and index.css (anywidget _css).
import * as esbuild from "esbuild";

const watch = process.argv.includes("--watch");

/** @type {import('esbuild').BuildOptions} */
const opts = {
  entryPoints: ["js/index.js"],
  outfile: "src/dt2/static/index.js",
  bundle: true,
  format: "esm",
  minify: !watch,
  sourcemap: watch,
  // DataTables ships font/image-free CSS for the bs5 integration; bundle CSS
  // imported from JS into a sibling index.css that anywidget loads as _css.
  loader: {
    ".css": "css",
    ".woff": "dataurl",
    ".woff2": "dataurl",
    ".ttf": "dataurl",
    ".eot": "dataurl",
    ".svg": "dataurl",
    ".png": "dataurl",
  },
  logLevel: "info",
};

if (watch) {
  const ctx = await esbuild.context(opts);
  await ctx.watch();
  console.log("[dt2] watching js/ for changes…");
} else {
  await esbuild.build(opts);
  console.log("[dt2] built src/dt2/static/index.{js,css}");
}
