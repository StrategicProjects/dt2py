"""Tests for Phase 2 — extension activation helpers + registry."""

import pytest

from dt2 import Options, dt2, extensions

COLS = ["name", "field", "year"]


def opts():
    return Options(columns=COLS)


def test_registry_lists_bundled_extensions():
    exts = extensions()
    names = {e["name"] for e in exts}
    # a representative spread of what is bundled
    assert {"Buttons", "Select", "Responsive", "SearchPanes", "ColumnControl"} <= names
    assert all("version" in e for e in exts)


def test_select_default_true():
    assert opts().select()["select"] is True


def test_select_with_config():
    o = opts().select({"style": "multi"})
    assert o["select"] == {"style": "multi"}


def test_responsive_and_fixed_header():
    o = opts().responsive().fixed_header()
    assert o["responsive"] is True
    assert o["fixedHeader"] is True


def test_key_table_sets_keys_option():
    # DataTables reads KeyTable via the `keys` option, not `keyTable`
    o = opts().key_table()
    assert o["keys"] is True
    assert "keyTable" not in o


def test_fixed_columns_config():
    o = opts().fixed_columns({"left": 2})
    assert o["fixedColumns"] == {"left": 2}


def test_row_group_from_column_name():
    o = opts().row_group("field")
    assert o["rowGroup"] == {"dataSrc": "field"}


def test_row_group_full_config_passthrough():
    o = opts().row_group({"dataSrc": "field", "startRender": None})
    assert o["rowGroup"]["dataSrc"] == "field"


def test_scroller_requires_scrolly_and_defer():
    o = opts().scroller("300px")
    assert o["scroller"] is True
    assert o["scrollY"] == "300px"
    assert o["deferRender"] is True


def test_state_restore_enables_statesave():
    o = opts().state_restore()
    assert o["stateRestore"] is True
    assert o["stateSave"] is True


def test_search_panes_and_builder():
    o = opts().search_panes().search_builder()
    assert o["searchPanes"] is True
    assert o["searchBuilder"] is True


def test_buttons_with_target():
    o = opts().buttons(["copyHtml5", "csvHtml5"], target="#toolbar")
    assert o["buttons"] == ["copyHtml5", "csvHtml5"]
    assert o["dt2_buttons_target"] == "#toolbar"


def test_buttons_default_set():
    o = opts().buttons()
    assert "excelHtml5" in o["buttons"]


def test_chaining_multiple_extensions():
    o = (
        opts()
        .select()
        .responsive()
        .row_group("field")
        .order(("year", "desc"))
    )
    assert o["select"] is True
    assert o["responsive"] is True
    assert o["rowGroup"]["dataSrc"] == "field"
    assert o["order"] == [[2, "desc"]]


def test_extensions_flow_through_dt2():
    o = opts().select().buttons(["copyHtml5"])
    w = dt2([{"name": "Ada", "field": "Math", "year": 1815}], options=o)
    assert w.options["select"] is True
    assert w.options["buttons"] == ["copyHtml5"]
