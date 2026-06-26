"""Tests for the config-parity layer (Options builder, JS markers, name resolution)."""

import json
import warnings

import pytest

from dt2 import JS, Options, dt2, register_renderer
from dt2.options import JS_MARKER, _name_to_idx

COLS = ["name", "field", "year"]


def opts():
    return Options(columns=COLS)


# ---- name -> index resolution (port of .dt2_name_to_idx) ----
def test_name_to_idx_resolves_names_1based():
    assert _name_to_idx(["name", "year"], COLS) == [1, 3]


def test_name_to_idx_passes_through_indices():
    assert _name_to_idx([2, 3], COLS) == [2, 3]


def test_name_to_idx_warns_unknown_name():
    with pytest.warns(UserWarning, match="Unknown column name"):
        out = _name_to_idx(["nope"], COLS)
    assert out == []


def test_name_to_idx_warns_when_no_columns():
    with pytest.warns(UserWarning, match="no column list"):
        _name_to_idx(["name"], [])


def test_bool_rejected():
    with pytest.raises(TypeError):
        _name_to_idx([True], COLS)


# ---- columnDefs structure (targets are 0-based, like JS) ----
def test_cols_align_columndef():
    o = opts().cols_align(["year"], "right")
    assert o["columnDefs"] == [{"targets": 2, "className": "text-end"}]


def test_cols_hide_and_width_accumulate():
    o = opts().cols_hide(["field"]).cols_width({"name": "120px"})
    assert {"targets": 1, "visible": False} in o["columnDefs"]
    assert {"targets": 0, "width": "120px"} in o["columnDefs"]


def test_align_invalid():
    with pytest.raises(ValueError):
        opts().cols_align(["year"], "middle")


# ---- ordering / paging ----
def test_order_by_name_is_0based_index():
    o = opts().order(("year", "desc"))
    assert o["order"] == [[2, "desc"]]


def test_length_menu_all_adds_language_label():
    o = opts().length_menu([10, 25, -1])
    assert o["lengthMenu"] == [10, 25, -1]
    assert o["language"]["lengthLabels"]["-1"] == "All"


def test_length_menu_labels():
    o = opts().length_menu([10, 100], labels=["10", "hundred"])
    assert o["lengthMenu"] == [10, {"label": "hundred", "value": 100}]


# ---- JS markers ----
def test_js_serializes_to_marker():
    j = JS("function(d,t){return d;}")
    assert j == {JS_MARKER: "function(d,t){return d;}"}
    assert json.loads(json.dumps(j)) == j  # JSON round-trip survives


def test_format_number_builds_render_call():
    o = opts().format_number(["year"], thousands=".", decimal=",", digits=2, prefix="R$ ")
    render = o["columnDefs"][0]["render"]
    assert render[JS_MARKER] == 'DataTable.render.number(".",",",2,"R$ ","")'
    assert o["columnDefs"][0]["targets"] == 2


def test_format_datetime_uses_undefined_defaults():
    o = opts().format_datetime(["year"], to="DD/MM/YYYY")
    code = o["columnDefs"][0]["render"][JS_MARKER]
    assert code == 'DataTable.render.datetime(undefined, "DD/MM/YYYY", undefined, undefined)'


def test_orthogonal_nested_markers():
    o = opts().cols_render_orthogonal(
        ["year"],
        display=JS("function(d){return d+' cm';}"),
        sort=JS("function(d){return parseFloat(d);}"),
    )
    render = o["columnDefs"][0]["render"]
    assert render["display"][JS_MARKER].endswith("cm';}")
    assert render["sort"][JS_MARKER].startswith("function")


def test_cols_render_requires_js():
    with pytest.raises(TypeError):
        opts().cols_render(["year"], "function(){}")


def test_register_and_use_renderer():
    register_renderer("badge", JS("function(d){return '<b>'+d+'</b>';}"))
    o = opts().use_renderer(["name"], "badge")
    assert o["columnDefs"][0]["render"][JS_MARKER].startswith("function")


def test_use_unknown_renderer_raises():
    with pytest.raises(KeyError):
        opts().use_renderer(["name"], "missing")


# ---- buttons / language ----
def test_use_buttons_layout():
    o = opts().use_buttons(["copy", "csv"], position="topStart")
    assert o["buttons"] == ["copy", "csv"]
    assert o["layout"]["topStart"] == "buttons"


def test_language_url():
    o = opts().language(url="https://x/pt-BR.json")
    assert o["language"] == {"url": "https://x/pt-BR.json"}


# ---- integration with dt2() ----
def test_dt2_merges_options_and_kwargs():
    o = opts().cols_align(["year"], "center")
    w = dt2([{"name": "Ada", "field": "Math", "year": 1815}], options=o, pageLength=5)
    assert w.options["pageLength"] == 5
    assert w.options["columnDefs"] == [{"targets": 2, "className": "text-center"}]


def test_options_seeded_from_dataframe_like():
    # Options(data) derives names from a records list
    o = Options([{"name": "Ada", "year": 1815}]).order(("year", "asc"))
    assert o["order"] == [[1, "asc"]]
