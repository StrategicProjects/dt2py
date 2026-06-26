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

    # JS -> Python (events) — read these reactively in Shiny via reactive_read()
    selected_rows = traitlets.List(default_value=[]).tag(sync=True)
    state = traitlets.Dict(default_value={}).tag(sync=True)

    # ---- proxy API (Python -> JS), mirrors R/dt2_proxy.R ----
    def proxy_reload(self, reset_paging: bool = True) -> None:
        self.send({"method": "reload", "resetPaging": reset_paging})

    def proxy_clear_search(self) -> None:
        self.send({"method": "clearSearch"})

    def proxy_search(self, value: str) -> None:
        self.send({"method": "search", "value": value})

    def proxy_select_rows(self, rows: Sequence[int]) -> None:
        self.send({"method": "selectRows", "rows": list(rows)})

    def proxy_update_data(self, data: Any) -> None:
        self.send({"method": "updateData", "data": _rows(data)[0]})


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
    **options: Any,
) -> Dt2:
    """Create a :class:`Dt2` table from a DataFrame or list of records.

    Parameters
    ----------
    data:
        A pandas/polars DataFrame, or a list of dict rows.
    columns:
        Optional explicit column spec (names or DataTables column dicts). When
        omitted, columns are inferred from ``data``.
    **options:
        Passed through verbatim as DataTables options (1:1 with the JS API),
        matching the R package's plain-list convention.
    """
    rows, inferred = _rows(data)
    cols: list[ColumnSpec] = list(columns) if columns is not None else list(inferred)
    return Dt2(data=rows, columns=cols, options=options)
