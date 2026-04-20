"""Tests for src/gerda/_fuzzy.py and the load() error path that uses it."""

from __future__ import annotations

import pytest

from gerda import _fuzzy, catalog, load


@pytest.fixture
def names() -> list[str]:
    return catalog.names()


def test_typo_corrected(names):
    out = _fuzzy.suggest("municipal_harn", names)
    assert "municipal_harm" in out


def test_prefix_match_first(names):
    out = _fuzzy.suggest("federal_muni", names)
    assert out, "expected at least one suggestion"
    assert all(s.startswith("federal_muni") for s in out)


def test_state_unhar_suggests_state_unharm(names):
    out = _fuzzy.suggest("state_unhar", names)
    assert "state_unharm" in out


def test_unrelated_returns_empty_or_low_quality(names):
    out = _fuzzy.suggest("totally_unrelated_xyz", names)
    assert out == [] or "totally_unrelated_xyz" not in out


def test_load_unknown_name_raises_with_suggestion():
    with pytest.raises(KeyError, match="Did you mean"):
        load("municipal_harn")


def test_load_federal_muni_harm_deprecation_message():
    with pytest.raises(KeyError) as exc_info:
        load("federal_muni_harm")
    msg = str(exc_info.value)
    assert "federal_muni_harm_21" in msg
    assert "federal_muni_harm_25" in msg


def test_load_unknown_no_suggestion_path():
    with pytest.raises(KeyError, match="not found"):
        load("zzz_garbage_no_match")
