"""Config helpers — Python port of R/dt2_options.R, dt2_formats.R, dt2_utils.R.

The R package builds DataTables options as a plain list and ships JS renderer
functions via ``htmlwidgets::JS()``. Here, options are a plain dict and JS
functions are marked with :class:`JS`; the JS adapter (``index.js``) revives
those markers into real functions before handing the config to DataTables.

Recommended usage mirrors the R pipe style, but chained:

    opts = (Options(df)
            .cols_align(["year"], "right")
            .format_number(["amount"], digits=2, decimal=",", thousands=".")
            .order(("year", "desc"))
            .length_menu([10, 25, 50, -1]))
    dt2(df, options=opts)
"""

from __future__ import annotations

import json
import warnings
from typing import Any, Iterable, Optional, Sequence, Union

JS_MARKER = "__dt2_js__"

ColRef = Union[str, int, Sequence[Union[str, int]]]

# module-level registry, mirrors R's .dt2_renderers env
_RENDERERS: dict[str, "JS"] = {}


class JS(dict):
    """A raw JavaScript expression, revived into a function client-side.

    Equivalent to ``htmlwidgets::JS()``. Serializes to ``{"__dt2_js__": code}``;
    ``index.js`` compiles it with ``DataTable``, ``$`` and ``moment`` in scope.
    """

    def __init__(self, code: str) -> None:
        if not isinstance(code, str):
            raise TypeError("JS() expects a JavaScript source string.")
        super().__init__({JS_MARKER: code})

    @property
    def code(self) -> str:
        return self[JS_MARKER]


def _js_str(x: Any, null_as: str = "null") -> str:
    """Port of .dt2_js_str: quote-safe JS literal via JSON (None -> null_as)."""
    if x is None:
        return null_as
    return json.dumps(x)


def _column_names(data: Any) -> list[str]:
    """Best-effort column-name list from a DataFrame/records/sequence."""
    if data is None:
        return []
    if hasattr(data, "columns"):  # pandas / polars
        return [str(c) for c in data.columns]
    if isinstance(data, (list, tuple)):
        if data and isinstance(data[0], dict):
            names: list[str] = []
            for row in data:
                for k in row:
                    if k not in names:
                        names.append(k)
            return names
        return [str(c) for c in data]
    raise TypeError(f"Cannot derive column names from {type(data)!r}")


def _name_to_idx(cols: ColRef, columns: Sequence[str]) -> list[int]:
    """Resolve names or 1-based indices to 1-based indices.

    Port of .dt2_name_to_idx — warns loudly (instead of silent NaN) when
    ``columns`` is unset or a name is unknown.
    """
    if isinstance(cols, (str, int)):
        cols = [cols]
    out: list[int] = []
    for c in cols:
        if isinstance(c, bool):  # guard: bool is an int subclass
            raise TypeError("Column references must be names or 1-based indices.")
        if isinstance(c, int):
            out.append(int(c))
            continue
        if not isinstance(c, str):
            raise TypeError("Column references must be names or 1-based indices.")
        if not columns:
            warnings.warn(
                "Column names were passed but the Options has no column list, so "
                "they cannot be resolved. Build with Options(df) / "
                "Options(columns=[...]), or pass 1-based indices.",
                stacklevel=3,
            )
            continue
        try:
            out.append(columns.index(c) + 1)
        except ValueError:
            warnings.warn(f"Unknown column name: {c!r}.", stacklevel=3)
    return out


class Options(dict):
    """Chainable builder for DataTables v2 options (a plain dict subclass).

    Pass either a DataFrame/records to seed the column-name map, or
    ``columns=[...]`` explicitly. The names are used only to resolve column
    references in the helpers; they are not emitted as a DataTables option.
    """

    def __init__(
        self,
        data: Any = None,
        *,
        columns: Optional[Sequence[str]] = None,
        **initial: Any,
    ) -> None:
        super().__init__(**initial)
        self._columns: list[str] = (
            [str(c) for c in columns] if columns is not None else _column_names(data)
        )

    # ---- internal ----
    def _add_defs(self, idx: Iterable[int], **spec: Any) -> "Options":
        defs = self.setdefault("columnDefs", [])
        for i in idx:
            defs.append({"targets": i - 1, **{k: v for k, v in spec.items()}})
        return self

    def _idx(self, cols: ColRef) -> list[int]:
        return _name_to_idx(cols, self._columns)

    # ---- ordering / search / paging (dt2_options.R) ----
    def order(self, *specs: Sequence[Any]) -> "Options":
        """Initial ordering. Each spec is ``(col, "asc"|"desc")``; col is a name
        or 1-based index."""
        ord_list = []
        for col, direction in specs:
            idx = self._idx(col)
            if idx:
                ord_list.append([idx[0] - 1, direction])
        self["order"] = ord_list
        return self

    def search_global(
        self,
        value: str,
        *,
        regex: bool = False,
        smart: bool = True,
        case_insensitive: bool = True,
    ) -> "Options":
        self["search"] = {
            "value": value,
            "regex": regex,
            "smart": smart,
            "caseInsensitive": case_insensitive,
        }
        return self

    def length_menu(
        self,
        values: Sequence[int] = (10, 25, 50, -1),
        labels: Optional[Sequence[str]] = None,
    ) -> "Options":
        values = list(values)
        if labels is not None and len(labels) == len(values):
            menu: list[Any] = []
            for v, l in zip(values, labels):
                menu.append(v if str(v) == l else {"label": l, "value": v})
            self["lengthMenu"] = menu
        else:
            self["lengthMenu"] = [int(v) for v in values]
            if -1 in values:
                lang = self.setdefault("language", {})
                lang.setdefault("lengthLabels", {})["-1"] = "All"
        return self

    def language(
        self,
        lang: Optional[dict] = None,
        *,
        url: Optional[str] = None,
    ) -> "Options":
        if url is not None:
            self["language"] = {"url": url}
        elif isinstance(lang, dict):
            self["language"] = lang
        return self

    def use_buttons(
        self,
        buttons: Sequence[str] = ("copy", "csv", "excel", "print"),
        *,
        position: str = "topEnd",
        button_class: Optional[str] = None,
    ) -> "Options":
        if button_class is not None:
            self["buttons"] = [
                {"extend": b, "className": button_class} for b in buttons
            ]
        else:
            self["buttons"] = list(buttons)
        self.setdefault("layout", {})[position] = "buttons"
        return self

    # ---- column appearance (dt2_options.R) ----
    def cols_width(self, mapping: dict) -> "Options":
        """``mapping``: ``{column_name_or_index: "120px", ...}``."""
        for name, width in mapping.items():
            self._add_defs(self._idx(name), width=width)
        return self

    def cols_align(self, cols: ColRef, align: str = "left") -> "Options":
        cls = {"left": "text-start", "center": "text-center", "right": "text-end"}
        if align not in cls:
            raise ValueError("align must be one of 'left', 'center', 'right'.")
        return self._add_defs(self._idx(cols), className=cls[align])

    def cols_hide(self, cols: ColRef) -> "Options":
        return self._add_defs(self._idx(cols), visible=False)

    def cols_escape(self, cols: ColRef, escape: bool = True) -> "Options":
        if escape:
            render = JS(
                "function(d,t){ if(t!=='display'||d==null) return d;"
                " return String(d).replace(/&/g,'&amp;').replace(/</g,'&lt;')"
                ".replace(/>/g,'&gt;').replace(/\"/g,'&quot;').replace(/'/g,'&#39;'); }"
            )
        else:
            render = JS("function(d,t){return d;}")
        return self._add_defs(self._idx(cols), render=render)

    # ---- renderers / formats (dt2_formats.R) ----
    def format_number(
        self,
        cols: ColRef,
        *,
        thousands: Optional[str] = None,
        decimal: Optional[str] = None,
        digits: int = 0,
        prefix: str = "",
        prefix_right: str = "",
    ) -> "Options":
        js = JS(
            "DataTable.render.number(%s,%s,%d,%s,%s)"
            % (
                _js_str(thousands),
                _js_str(decimal),
                int(digits),
                _js_str(prefix),
                _js_str(prefix_right),
            )
        )
        return self._add_defs(self._idx(cols), render=js)

    def format_datetime(
        self,
        cols: ColRef,
        *,
        from_: Optional[str] = None,
        to: str = "DD/MM/YYYY",
        locale: Optional[str] = None,
        default: Optional[str] = None,
    ) -> "Options":
        args = ", ".join(
            [
                _js_str(from_, "undefined"),
                _js_str(to, "undefined"),
                _js_str(locale, "undefined"),
                _js_str(default, "undefined"),
            ]
        )
        js = JS("DataTable.render.datetime(%s)" % args)
        return self._add_defs(self._idx(cols), render=js)

    def format_number_abbrev(
        self,
        cols: ColRef,
        *,
        digits: int = 1,
        locale: Optional[str] = None,
    ) -> "Options":
        d = int(digits)
        if not locale:
            code = (
                "function(d,t,row,meta){"
                "if(t!=='display'&&t!=='filter')return d;"
                "var n=Number(d);if(!isFinite(n))return d;"
                "var abs=Math.abs(n),sign=n<0?'-':'';"
                "function fmt(x){return x.toFixed(%d);}"
                "if(abs>=1e9)return sign+fmt(abs/1e9)+'B';"
                "if(abs>=1e6)return sign+fmt(abs/1e6)+'M';"
                "if(abs>=1e3)return sign+fmt(abs/1e3)+'k';"
                "return n.toFixed(%d);}" % (d, d)
            )
        else:
            loc = json.dumps(locale)
            code = (
                "function(d,t,row,meta){"
                "if(t!=='display'&&t!=='filter')return d;"
                "var n=Number(d);if(!isFinite(n))return d;"
                "var abs=Math.abs(n),sign=n<0?'-':'';"
                "function fmt(x){return Number(x.toFixed(%d)).toLocaleString(%s);}"
                "if(abs>=1e9)return sign+fmt(abs/1e9)+'B';"
                "if(abs>=1e6)return sign+fmt(abs/1e6)+'M';"
                "if(abs>=1e3)return sign+fmt(abs/1e3)+'k';"
                "return n.toLocaleString(%s,{minimumFractionDigits:%d,maximumFractionDigits:%d});}"
                % (d, loc, loc, d, d)
            )
        return self._add_defs(self._idx(cols), render=JS(code))

    def format_time_relative(self, cols: ColRef, *, locale: str = "pt-br") -> "Options":
        self["_momentLocale"] = locale
        js = JS(
            "function(d,t,row,meta){if(d==null||d==='')return d;"
            "try{if(window.moment){var m=moment(d);if(m.isValid())return m.fromNow();}}"
            "catch(e){}return d;}"
        )
        return self._add_defs(self._idx(cols), render=js)

    def cols_render(self, cols: ColRef, js_render: JS) -> "Options":
        if not isinstance(js_render, JS):
            raise TypeError("js_render must be a dt2.JS(...) instance.")
        return self._add_defs(self._idx(cols), render=js_render)

    def cols_render_orthogonal(
        self,
        cols: ColRef,
        *,
        display: Optional[JS] = None,
        sort: Optional[JS] = None,
        filter: Optional[JS] = None,
        type: Optional[JS] = None,
    ) -> "Options":
        parts = {
            k: v
            for k, v in {
                "display": display,
                "sort": sort,
                "filter": filter,
                "type": type,
            }.items()
            if v is not None
        }
        if not parts:
            raise ValueError("Provide at least one of display/sort/filter/type.")
        # nested JS markers are revived recursively client-side
        return self._add_defs(self._idx(cols), render=dict(parts))

    def use_renderer(self, cols: ColRef, name: str) -> "Options":
        js = _RENDERERS.get(name)
        if js is None:
            raise KeyError(f"Renderer {name!r} is not registered.")
        return self._add_defs(self._idx(cols), render=js)

    # ---- extension activation (Phase 2) ----
    # Each sets the DataTables option the bundled extension reads. Accept True or
    # a config dict (1:1 with the extension's option), matching the R convention.
    def _set(self, key: str, value: Any) -> "Options":
        self[key] = value
        return self

    def select(self, value: Union[bool, dict] = True) -> "Options":
        return self._set("select", value)

    def responsive(self, value: Union[bool, dict] = True) -> "Options":
        return self._set("responsive", value)

    def fixed_header(self, value: Union[bool, dict] = True) -> "Options":
        return self._set("fixedHeader", value)

    def fixed_columns(self, value: Union[bool, dict] = True) -> "Options":
        return self._set("fixedColumns", value)

    def key_table(self, value: Union[bool, dict] = True) -> "Options":
        return self._set("keys", value)

    def col_reorder(self, value: Union[bool, dict] = True) -> "Options":
        return self._set("colReorder", value)

    def row_reorder(self, value: Union[bool, dict] = True) -> "Options":
        return self._set("rowReorder", value)

    def row_group(self, data_src: Union[str, int, dict]) -> "Options":
        """Group rows by a column. Pass a column data-key/index or a full
        rowGroup config dict."""
        cfg = data_src if isinstance(data_src, dict) else {"dataSrc": data_src}
        return self._set("rowGroup", cfg)

    def scroller(self, scroll_y: str = "400px", value: Union[bool, dict] = True) -> "Options":
        """Virtual scrolling. Requires scrollY; deferRender is enabled for it."""
        self["scrollY"] = scroll_y
        self["deferRender"] = True
        return self._set("scroller", value)

    def search_panes(self, value: Union[bool, dict] = True) -> "Options":
        return self._set("searchPanes", value)

    def search_builder(self, value: Union[bool, dict] = True) -> "Options":
        return self._set("searchBuilder", value)

    def state_restore(self, value: Union[bool, dict] = True) -> "Options":
        self["stateSave"] = True
        return self._set("stateRestore", value)

    def column_control(self, value: Any = True) -> "Options":
        return self._set("columnControl", value)

    def buttons(
        self,
        buttons: Sequence[Any] = ("copyHtml5", "csvHtml5", "excelHtml5", "print"),
        *,
        target: Optional[str] = None,
    ) -> "Options":
        """Configure Buttons with full button ids/objects (port of R dt2_buttons).

        ``target`` is an optional CSS selector to relocate the rendered buttons
        container after init. For the simpler layout-based case use
        :meth:`use_buttons`. PDF export (``pdfHtml5``) needs pdfmake, which is
        not bundled."""
        self["buttons"] = list(buttons)
        if target is not None:
            self["dt2_buttons_target"] = target
        return self

    # ---- inline row inputs (port of R/dt2_inputs.R) ----
    def col_checkbox(
        self,
        col: ColRef,
        *,
        input_id_prefix: str = "row_chk_",
        value_col: Optional[Union[str, int]] = None,
    ) -> "Options":
        """Render a checkbox per row in ``col``. Clicks set the widget's
        ``row_check`` event ({row, value}). ``value_col`` seeds the initial
        checked state from another column (name or 1-based index)."""
        if value_col is None:
            value_js = "false"
        else:
            if isinstance(value_col, str):
                name = value_col
                idx0 = (self._columns.index(name) if name in self._columns else 0)
            else:
                idx0 = int(value_col) - 1
                name = self._columns[idx0] if 0 <= idx0 < len(self._columns) else ""
            value_js = "(Array.isArray(row) ? row[%d] : row[%s])" % (idx0, json.dumps(name))
        code = (
            "function(d,t,row,meta){ if(t!=='display') return d;"
            " var rid='%s'+(meta.row+1);"
            " var checked=%s?' checked':'';"
            " return '<input type=\"checkbox\" class=\"dt2-row-checkbox form-check-input\" id=\"'+rid+'\"'+checked+'/>'; }"
            % (input_id_prefix, value_js)
        )
        return self._add_defs(self._idx(col), render=JS(code))

    def col_button(
        self,
        col: ColRef,
        *,
        label: str = "Action",
        input_id_prefix: str = "row_btn_",
        button_class: str = "dt2-row-button btn btn-sm btn-primary",
    ) -> "Options":
        """Render an action button per row in ``col``. Clicks set the widget's
        ``row_button`` event ({row, id})."""
        import html as _html

        code = (
            "function(d,t,row,meta){ if(t!=='display') return d;"
            " var rid='%s'+(meta.row+1);"
            " return '<button type=\"button\" class=\"%s\" id=\"'+rid+'\">%s</button>'; }"
            % (input_id_prefix, button_class, _html.escape(label))
        )
        return self._add_defs(self._idx(col), render=JS(code))


def register_renderer(name: str, js: JS) -> str:
    """Register a named JS renderer for later use via Options.use_renderer."""
    if not isinstance(js, JS):
        raise TypeError("js must be a dt2.JS(...) instance.")
    _RENDERERS[name] = js
    return name


# Extensions bundled in index.js (all activate via their option). Versions match
# the npm packages pinned in package.json. Mirrors R's .dt2_extension_registry().
_EXTENSIONS: list[dict] = [
    {"name": "Buttons", "version": "3.2.4", "option": "buttons"},
    {"name": "Select", "version": "3.1.0", "option": "select"},
    {"name": "Responsive", "version": "3.0.6", "option": "responsive"},
    {"name": "FixedHeader", "version": "4.0.3", "option": "fixedHeader"},
    {"name": "FixedColumns", "version": "5.0.5", "option": "fixedColumns"},
    {"name": "KeyTable", "version": "2.12.1", "option": "keys"},
    {"name": "Scroller", "version": "2.4.3", "option": "scroller"},
    {"name": "RowGroup", "version": "1.6.0", "option": "rowGroup"},
    {"name": "RowReorder", "version": "1.5.0", "option": "rowReorder"},
    {"name": "ColReorder", "version": "2.1.1", "option": "colReorder"},
    {"name": "DateTime", "version": "1.6.0", "option": None},
    {"name": "SearchBuilder", "version": "1.8.4", "option": "searchBuilder"},
    {"name": "SearchPanes", "version": "2.3.5", "option": "searchPanes"},
    {"name": "StateRestore", "version": "1.4.2", "option": "stateRestore"},
    {"name": "ColumnControl", "version": "1.2.1", "option": "columnControl"},
]


def extensions() -> list[dict]:
    """List bundled DataTables extensions (parity with R ``dt2_extensions()``).

    All are bundled in the JS asset and activate via their option (set with the
    corresponding ``Options`` helper). PDF export (pdfmake) is not bundled.
    """
    return [dict(e) for e in _EXTENSIONS]
