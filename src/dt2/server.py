"""Server-side processing (SSP) for dt2.

Python port of R/dt2_server_processing.R. Unlike the R version, the request
arrives already structured over the anywidget Comm (the DataTables ``ajax``
function hands us the request object directly), so there is no query-string to
parse — we go straight to filter → order → paginate.

The core :func:`process_ssp` is pure (list-of-dict rows in, payload dict out)
and is unit-tested without a browser.
"""

from __future__ import annotations

from typing import Any, Sequence


def _sort_key(value: Any):
    """Sort key that pushes None/NaN last and tolerates a homogeneous column."""
    is_missing = value is None or (isinstance(value, float) and value != value)
    return (is_missing, value)


def process_ssp(
    request: dict,
    rows: Sequence[dict],
    columns: Sequence[str],
) -> dict:
    """Filter, order and paginate ``rows`` per a DataTables SSP ``request``.

    Mirrors :func:`dt2_ssp_handler` in the R package: global case-insensitive
    substring search across all columns, cascading stable sort (last order key
    applied first), then paging. Returns the DataTables payload.
    """
    draw = int(request.get("draw", 1) or 1)
    start = max(0, int(request.get("start", 0) or 0))
    length = int(request.get("length", 10) or 0)

    search = request.get("search") or {}
    search_value = (search.get("value") or "").strip()
    order = request.get("order") or []
    cols = list(columns)

    result = list(rows)
    total = len(result)

    # --- global search: case-insensitive substring across all columns ---
    if search_value:
        pat = search_value.lower()
        result = [
            r
            for r in result
            if any(pat in str(r.get(c, "")).lower() for c in cols)
        ]

    filtered = len(result)

    # --- ordering: apply in reverse so the first key dominates (stable sort) ---
    for o in reversed(order):
        try:
            col_idx = int(o.get("column", 0))
        except (TypeError, ValueError):
            continue
        if not (0 <= col_idx < len(cols)):
            continue
        name = cols[col_idx]
        descending = str(o.get("dir", "asc")).lower().startswith("desc")
        try:
            result = sorted(result, key=lambda r: _sort_key(r.get(name)), reverse=descending)
        except TypeError:
            # mixed types in the column → fall back to string comparison
            result = sorted(
                result,
                key=lambda r: (r.get(name) is None, str(r.get(name))),
                reverse=descending,
            )

    # --- paginate (length < 0 means "all", per the DataTables convention) ---
    if length >= 0:
        result = result[start : start + length]

    return {
        "draw": draw,
        "recordsTotal": total,
        "recordsFiltered": filtered,
        "data": result,
    }
