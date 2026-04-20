"""Tests for src/gerda/crosswalk.py."""

from __future__ import annotations

import math

import pandas as pd
import pytest

from gerda import party_crosswalk
from gerda.crosswalk import _lookup, destinations


def test_lookup_loads():
    lt = _lookup()
    assert isinstance(lt, pd.DataFrame)
    assert "party_gerda" in lt.columns
    assert len(lt) > 0


def test_destinations_has_21_options():
    """Mirrors the R docs: 21 destination columns excluding party_gerda."""
    assert len(destinations()) == 21
    assert "party_gerda" not in destinations()


def test_left_right_known_values():
    """R README: party_crosswalk(c("cdu","spd","linke_pds",NA), "left_right")."""
    out = party_crosswalk(["cdu", "spd", "linke_pds", None], "left_right")
    assert out.iloc[0] == pytest.approx(6.2503, abs=1e-4)
    assert out.iloc[1] == pytest.approx(3.6451, abs=1e-4)
    assert out.iloc[2] == pytest.approx(1.2152, abs=1e-4)
    assert math.isnan(out.iloc[3])


def test_family_name_short():
    """R README: party_crosswalk(c("cdu","afd"), "family_name_short")."""
    out = party_crosswalk(["cdu", "afd"], "family_name_short")
    assert out.iloc[0] == "chr"
    assert out.iloc[1] == "right"


def test_unknown_party_returns_nan_numeric():
    out = party_crosswalk(["cdu", "this_is_not_a_party"], "left_right")
    assert out.iloc[0] == pytest.approx(6.2503, abs=1e-4)
    assert math.isnan(out.iloc[1])


def test_unknown_party_returns_na_string():
    out = party_crosswalk(["cdu", "totally_fake"], "family_name_short")
    assert out.iloc[0] == "chr"
    assert pd.isna(out.iloc[1])


def test_invalid_destination_raises():
    with pytest.raises(ValueError, match="not a valid destination"):
        party_crosswalk(["cdu"], "not_a_real_column")


def test_destination_must_be_string():
    with pytest.raises(TypeError):
        party_crosswalk(["cdu"], ["left_right"])


def test_single_string_input_rejected():
    """party_crosswalk('cdu', ...) should error, not silently iterate over chars."""
    with pytest.raises(TypeError, match="sequence of strings"):
        party_crosswalk("cdu", "left_right")


def test_non_string_element_rejected():
    with pytest.raises(TypeError, match="strings or None"):
        party_crosswalk([1, 2, 3], "left_right")


def test_empty_input():
    out = party_crosswalk([], "left_right")
    assert isinstance(out, pd.Series)
    assert len(out) == 0


def test_returns_pd_series():
    out = party_crosswalk(["cdu"], "party_name_short")
    assert isinstance(out, pd.Series)
