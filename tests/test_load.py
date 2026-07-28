"""Tests for src/gerda/load.py."""

from __future__ import annotations

import importlib
from pathlib import Path

import pandas as pd
import pytest
import responses

from gerda import cache
from gerda.catalog import find
from gerda.load import load

FIXTURE_DIR = Path(__file__).parent / "fixtures"
load_module = importlib.import_module("gerda.load")


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
    with pytest.warns(FutureWarning):
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
def test_county_codes_preserved_as_strings(tmp_cache, fixture_bytes):
    """The whole reason we use pyreadr+RDS instead of CSV: leading zeros stick."""
    _serve("federal_cty_unharm", fixture_bytes)
    with pytest.warns(FutureWarning):
        df = load("federal_cty_unharm")
    assert df["county_code"].tolist() == ["01001", "01002", "01003"]
    # pyreadr may return either the legacy object dtype or the new pandas StringDtype;
    # both are valid as long as values stay as strings (not coerced to ints).
    assert (
        pd.api.types.is_string_dtype(df["county_code"])
        or df["county_code"].dtype == object
    )


@responses.activate
def test_federal_cty_unharm_adds_canonical_aliases(tmp_cache, fixture_bytes):
    """Canonical names coexist with legacy names through Python v0.6."""
    _serve("federal_cty_unharm", fixture_bytes)
    with pytest.warns(FutureWarning, match="removed in v0.7"):
        df = load("federal_cty_unharm")

    assert "county_code" in df.columns
    assert "election_year" in df.columns
    assert "ags" in df.columns
    assert "year" in df.columns
    assert df["county_code"].tolist() == ["01001", "01002", "01003"]


def test_federal_cty_unharm_preserves_both_existing_schemas():
    df = pd.DataFrame(
        {
            "ags": ["01001"],
            "county_code": ["01001"],
            "year": [2021],
            "election_year": [2021],
        }
    )
    normalized = load_module._normalize_schema("federal_cty_unharm", df)
    assert list(normalized.columns) == [
        "ags",
        "county_code",
        "year",
        "election_year",
    ]


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


@responses.activate
def test_unreadable_cached_rds_is_redownloaded(tmp_cache, fixture_bytes):
    cached = tmp_cache / "federal_cty_harm.rds"
    cached.write_bytes(b"not an rds file")
    _serve("federal_cty_harm", fixture_bytes)

    df = load("federal_cty_harm")

    assert len(df) == 3
    assert cached.read_bytes() == fixture_bytes
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
