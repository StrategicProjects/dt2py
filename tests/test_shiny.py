"""Tests for Phase 3 — proxy commands, inline inputs, event traits."""

import pytest

from dt2 import JS, Options, dt2
from dt2.options import JS_MARKER

ROWS = [{"name": "Ada", "flag": True}, {"name": "Alan", "flag": False}]


def widget(**kw):
    w = dt2(ROWS, **kw)
    w._sent = []
    w.send = lambda content, **_: w._sent.append(content)  # capture proxy messages
    return w


# ---- proxy commands (mirror R/dt2_proxy.R `cmd` protocol) ----
def test_replace_data_client_side():
    w = widget()
    w.replace_data([{"name": "Zed", "flag": True}])
    assert w._sent[-1] == {"cmd": "replaceData", "data": [{"name": "Zed", "flag": True}]}


def test_replace_data_server_side_reloads_and_swaps():
    w = widget(server_side=True)
    w.replace_data([{"name": "Zed", "flag": True}])
    assert w._sent[-1]["cmd"] == "reload"
    assert w._full_data == [{"name": "Zed", "flag": True}]


def test_order_builds_args():
    w = widget()
    w.order(("name", "desc"))
    assert w._sent[-1] == {"cmd": "order", "args": [[["name", "desc"]]]}


def test_search_args_order():
    w = widget()
    w.search("ada", regex=True)
    assert w._sent[-1] == {"cmd": "search", "args": ["ada", True, True, True]}


def test_page_number():
    w = widget()
    w.page("number", 3)
    assert w._sent[-1] == {"cmd": "page", "args": ["number", 3]}


def test_select_rows_1based():
    w = widget()
    w.select_rows([1, 3], reset=False)
    assert w._sent[-1] == {"cmd": "selectRows", "args": [[1, 3], False]}


def test_clear_search_and_draw():
    w = widget()
    w.clear_search()
    w.draw()
    assert w._sent[-2] == {"cmd": "clearSearch"}
    assert w._sent[-1] == {"cmd": "draw", "resetPaging": False}


# ---- event traits exist for reactive_read ----
def test_event_traits_present():
    w = dt2(ROWS)
    for trait in ("selected_rows", "state", "row_check", "row_button"):
        assert w.has_trait(trait)


# ---- inline inputs (port of R/dt2_inputs.R) ----
def test_col_checkbox_render_marker():
    o = Options(columns=["name", "flag"]).col_checkbox("name")
    code = o["columnDefs"][0]["render"][JS_MARKER]
    assert "dt2-row-checkbox" in code
    assert "row_chk_" in code
    assert "meta.row+1" in code


def test_col_checkbox_value_col_seeds_checked():
    o = Options(columns=["name", "flag"]).col_checkbox("name", value_col="flag")
    code = o["columnDefs"][0]["render"][JS_MARKER]
    # reads the 'flag' column (index 1) for the initial state
    assert 'row["flag"]' in code or "row[1]" in code


def test_col_button_render_marker_and_escaping():
    o = Options(columns=["name"]).col_button("name", label="<go>")
    code = o["columnDefs"][0]["render"][JS_MARKER]
    assert "dt2-row-button" in code
    assert "&lt;go&gt;" in code  # label HTML-escaped


def test_inline_inputs_flow_through_dt2():
    o = Options(columns=["name", "flag"]).col_checkbox("flag", value_col="flag")
    w = dt2(ROWS, options=o)
    assert w.options["columnDefs"][0]["targets"] == 1
