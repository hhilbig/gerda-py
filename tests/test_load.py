"""Tests for src/gerda/load.py."""

from __future__ import annotations

import warnings
from pathlib import Path

import pandas as pd
import pytest
import responses

import gerda.load as load_module
from gerda import cache
from gerda.catalog import find
from gerda.load import load

FIXTURE_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def tmp_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(cache, "cache_dir", lambda: tmp_path)
    return tmp_path


@pytest.fixture
def fixture_bytes() -> bytes:
    return (FIXTURE_DIR / "federal_cty_unharm_tiny.rds").read_bytes()


def _serve(name: str, payload: bytes) -> str:
    url = find(name)["rds_url"]
    responses.add(responses.GET, url, body=payload, status=200)
    return url


@responses.activate
def test_strip_extension_does_not_break_load(tmp_cache, fixture_bytes):
    _serve("federal_cty_unharm", fixture_bytes)
    df = load("federal_cty_unharm.rds")
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 3


@responses.activate
def test_load_returns_pandas_dataframe(tmp_cache, fixture_bytes):
    _serve("federal_cty_harm", fixture_bytes)
    df = load("federal_cty_harm")
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 3


@responses.activate
def test_ags_codes_preserved_as_strings(tmp_cache, fixture_bytes):
    """The whole reason we use pyreadr+RDS instead of CSV: leading zeros stick."""
    _serve("federal_cty_unharm", fixture_bytes)
    df = load("federal_cty_unharm")
    assert df["ags"].tolist() == ["01001", "01002", "01003"]
    # pyreadr may return either the legacy object dtype or the new pandas StringDtype;
    # both are valid as long as values stay as strings (not coerced to ints).
    assert pd.api.types.is_string_dtype(df["ags"]) or df["ags"].dtype == object


@responses.activate
def test_federal_cty_unharm_adds_aliases(tmp_cache, fixture_bytes):
    """Schema normalization: ags -> county_code, year -> election_year."""
    _serve("federal_cty_unharm", fixture_bytes)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        df = load("federal_cty_unharm")

    assert "county_code" in df.columns
    assert "election_year" in df.columns
    assert df["county_code"].tolist() == df["ags"].tolist()
    deprecations = [w for w in caught if issubclass(w.category, DeprecationWarning)]
    assert any("federal_cty_unharm" in str(w.message) for w in deprecations)


@responses.activate
def test_other_dataset_not_aliased(tmp_cache, fixture_bytes):
    _serve("federal_cty_harm", fixture_bytes)
    df = load("federal_cty_harm")
    assert "county_code" not in df.columns
    assert "election_year" not in df.columns


@responses.activate
def test_cache_hit_on_second_call(tmp_cache, fixture_bytes):
    _serve("federal_cty_harm", fixture_bytes)
    load("federal_cty_harm")
    load("federal_cty_harm")
    assert len(responses.calls) == 1


def test_invalid_name_type():
    with pytest.raises(TypeError):
        load(None)
    with pytest.raises(TypeError):
        load("")


@responses.activate
def test_as_polars_missing_dep_raises(tmp_cache, fixture_bytes, monkeypatch):
    """When polars is not importable, as_polars=True raises an informative ImportError."""
    import builtins
    import sys

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "polars":
            raise ImportError("polars is not installed (simulated)")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    sys.modules.pop("polars", None)

    _serve("federal_cty_harm", fixture_bytes)
    with pytest.raises(ImportError, match=r"gerda\[polars\]"):
        load("federal_cty_harm", as_polars=True)
