"""dt2 — DataTables v2 widget for Shiny for Python (and Jupyter).

Python port of the R DT2 package. The widget is an anywidget; the heavy
lifting (the DataTables v2 runtime) is reused via the bundled JS adapter in
``static/``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional, Sequence, Union

import anywidget
import traitlets

from .server import process_ssp

_STATIC = Path(__file__).parent / "static"

ColumnSpec = Union[str, dict]


class Dt2(anywidget.AnyWidget):
    """A DataTables v2 table.

    Prefer the :func:`dt2` constructor, which accepts pandas/polars frames and
    lists of dicts and fills these traits for you.
    """

    _esm = _STATIC / "index.js"
    _css = _STATIC / "index.css"

    # Python -> JS (config)
    data = traitlets.List(default_value=[]).tag(sync=True)
    columns = traitlets.List(default_value=[]).tag(sync=True)
    options = traitlets.Dict(default_value={}).tag(sync=True)
    server_side = traitlets.Bool(False).tag(sync=True)

    # JS -> Python (events) — read these reactively in Shiny via reactive_read()
    selected_rows = traitlets.List(default_value=[]).tag(sync=True)
    state = traitlets.Dict(default_value={}).tag(sync=True)
    row_check = traitlets.Dict(default_value={}).tag(sync=True)  # {row, value, _seq}
    row_button = traitlets.Dict(default_value={}).tag(sync=True)  # {row, id, _seq}

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # Full dataset kept Python-side for server-side processing — deliberately
        # NOT a synced trait (the whole point of SSP is to not ship it all).
        self._full_data: list[dict] = kwargs.pop("_full_data", []) or []
        self._col_names: list[str] = kwargs.pop("_col_names", []) or []
        super().__init__(*args, **kwargs)
        self.on_msg(self._on_msg)

    # ---- server-side processing round-trip (Comm) ----
    def _on_msg(self, _widget: Any, content: Any, _buffers: Any) -> None:
        if not isinstance(content, dict) or not content.get("dt2_ssp"):
            return
        payload = process_ssp(content.get("request", {}), self._full_data, self._col_names)
        self.send(
            {
                "dt2_ssp_response": True,
                "requestId": content.get("requestId"),
                "payload": payload,
            }
        )

    # ---- proxy API (Python -> JS), mirrors R/dt2_proxy.R ----
    # The widget *is* the proxy here (no separate id/session like in R/Shiny);
    # call these methods on the rendered widget instance.
    def replace_data(self, data: Any) -> None:
        """Replace all table data. For server-side tables this swaps the
        Python-side dataset and triggers a client re-fetch instead."""
        rows, cols = _rows(data)
        if self.server_side:
            self._full_data = rows
            self._col_names = cols or self._col_names
            self.send({"cmd": "reload", "resetPaging": False})
        else:
            self.send({"cmd": "replaceData", "data": rows})

    def draw(self, reset_paging: bool = False) -> None:
        self.send({"cmd": "draw", "resetPaging": reset_paging})

    def reload(self, reset_paging: bool = True) -> None:
        """Re-fetch a server-side table."""
        self.send({"cmd": "reload", "resetPaging": reset_paging})

    def order(self, *specs: Sequence[Any]) -> None:
        """Reorder. Each spec is ``(col, "asc"|"desc")``; col is a 1-based index
        or a column header name (resolved client-side)."""
        self.send({"cmd": "order", "args": [[list(s) for s in specs]]})

    def search(
        self,
        value: str,
        regex: bool = False,
        smart: bool = True,
        case_insensitive: bool = True,
    ) -> None:
        self.send({"cmd": "search", "args": [value, regex, smart, case_insensitive]})

    def clear_search(self) -> None:
        self.send({"cmd": "clearSearch"})

    def page(self, action: Union[str, int] = "first", number: Optional[int] = None) -> None:
        """Navigate paging. ``action`` in first/previous/next/last/number; for
        'number', pass a 1-based ``number``."""
        self.send({"cmd": "page", "args": [action, number]})

    def select_rows(self, indexes: Sequence[int], reset: bool = True) -> None:
        """Select rows by 1-based index (Select extension)."""
        self.send({"cmd": "selectRows", "args": [list(indexes), bool(reset)]})


def _col_data_names(columns: Sequence[ColumnSpec]) -> list[str]:
    """The data-key for each column spec (the key used in row dicts)."""
    names: list[str] = []
    for c in columns:
        if isinstance(c, str):
            names.append(c)
        elif isinstance(c, dict):
            names.append(str(c.get("data", c.get("title", ""))))
    return names


def _rows(data: Any) -> tuple[list[dict], list[str]]:
    """Return (list-of-row-dicts, column-names) for the supported inputs."""
    # pandas
    if hasattr(data, "to_dict") and hasattr(data, "columns"):
        cols = [str(c) for c in data.columns]
        return data.to_dict(orient="records"), cols
    # polars
    if hasattr(data, "to_dicts") and hasattr(data, "columns"):
        return data.to_dicts(), [str(c) for c in data.columns]
    # list of dicts
    if isinstance(data, list):
        if data and isinstance(data[0], dict):
            cols: list[str] = []
            for row in data:
                for k in row:
                    if k not in cols:
                        cols.append(k)
            return data, cols
        return data, []
    raise TypeError(f"dt2(): unsupported data type {type(data)!r}")


def dt2(
    data: Any,
    columns: Optional[Sequence[ColumnSpec]] = None,
    *,
    options: Optional[dict] = None,
    server_side: bool = False,
    **kwoptions: Any,
) -> Dt2:
    """Create a :class:`Dt2` table from a DataFrame or list of records.

    Parameters
    ----------
    data:
        A pandas/polars DataFrame, or a list of dict rows.
    columns:
        Optional explicit column spec (names or DataTables column dicts). When
        omitted, columns are inferred from ``data``.
    options:
        A dict or :class:`dt2.options.Options` of DataTables options. Merged
        with any keyword options (the keyword options win on conflict).
    server_side:
        When True, the data stays Python-side and DataTables fetches pages over
        the Comm (filter/order/paginate handled by :func:`dt2.server.process_ssp`).
        Use for large tables.
    **kwoptions:
        Extra DataTables options passed verbatim (1:1 with the JS API), matching
        the R package's plain-list convention.
    """
    rows, inferred = _rows(data)
    cols: list[ColumnSpec] = list(columns) if columns is not None else list(inferred)
    col_names = _col_data_names(cols)

    merged: dict[str, Any] = dict(options or {})
    merged.update(kwoptions)
    options = merged

    if server_side:
        return Dt2(
            data=[],
            columns=cols,
            options=options,
            server_side=True,
            _full_data=rows,
            _col_names=col_names,
        )
    return Dt2(data=rows, columns=cols, options=options)
