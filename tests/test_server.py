"""Tests for server-side processing — the highest-risk parity piece.

These exercise the pure data path (filter/order/paginate) that runs Python-side
when ``server_side=True``. The Comm round-trip itself needs a live frontend.
"""

from dt2.server import process_ssp

COLS = ["name", "field", "year"]
ROWS = [
    {"name": "Ada", "field": "Math", "year": 1815},
    {"name": "Alan", "field": "Logic", "year": 1912},
    {"name": "Grace", "field": "Navy", "year": 1906},
    {"name": "Linus", "field": "Kernel", "year": 1969},
    {"name": "Margaret", "field": "Apollo", "year": 1936},
]


def req(**kw):
    base = {"draw": 1, "start": 0, "length": 10, "search": {"value": ""}, "order": []}
    base.update(kw)
    return base


def test_passthrough_no_filter():
    out = process_ssp(req(), ROWS, COLS)
    assert out["draw"] == 1
    assert out["recordsTotal"] == 5
    assert out["recordsFiltered"] == 5
    assert len(out["data"]) == 5


def test_global_search_case_insensitive_substring():
    out = process_ssp(req(search={"value": "na"}), ROWS, COLS)
    # "Navy" (Grace) matches; nothing else contains "na"
    assert out["recordsFiltered"] == 1
    assert out["data"][0]["name"] == "Grace"


def test_search_matches_numeric_column():
    out = process_ssp(req(search={"value": "1815"}), ROWS, COLS)
    assert out["recordsFiltered"] == 1
    assert out["data"][0]["name"] == "Ada"


def test_order_desc_by_year():
    out = process_ssp(req(order=[{"column": 2, "dir": "desc"}]), ROWS, COLS)
    years = [r["year"] for r in out["data"]]
    assert years == sorted(years, reverse=True)
    assert out["data"][0]["name"] == "Linus"  # 1969


def test_order_asc_by_name():
    out = process_ssp(req(order=[{"column": 0, "dir": "asc"}]), ROWS, COLS)
    names = [r["name"] for r in out["data"]]
    assert names == sorted(names)


def test_pagination_window():
    out = process_ssp(
        req(start=1, length=2, order=[{"column": 0, "dir": "asc"}]), ROWS, COLS
    )
    assert out["recordsTotal"] == 5
    assert out["recordsFiltered"] == 5
    assert [r["name"] for r in out["data"]] == ["Alan", "Grace"]


def test_filtered_count_reflects_search_not_page():
    out = process_ssp(
        req(search={"value": "a"}, start=0, length=2), ROWS, COLS
    )
    # rows containing "a" (case-insensitive): Ada, Alan, Grace, Margaret, Navy(Grace)
    assert out["recordsFiltered"] >= 3
    assert len(out["data"]) <= 2  # page caps the returned rows


def test_none_values_sort_last():
    rows = ROWS + [{"name": "Zed", "field": "X", "year": None}]
    out = process_ssp(req(order=[{"column": 2, "dir": "asc"}]), rows, COLS)
    assert out["data"][-1]["name"] == "Zed"


def test_length_negative_returns_all():
    out = process_ssp(req(length=-1), ROWS, COLS)
    assert len(out["data"]) == 5
