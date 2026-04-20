"""Tests for src/gerda/catalog.py."""

from __future__ import annotations

import re

import pandas as pd
import pytest

from gerda import catalog, datasets


def test_catalog_has_39_entries():
    assert len(catalog.load_catalog()) == 39


def test_datasets_returns_dataframe():
    df = datasets()
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ["data_name", "description"]
    assert len(df) == 39


def test_every_url_is_well_formed():
    df = catalog.load_catalog()
    url_pattern = re.compile(
        r"^https://github\.com/awiedem/german_election_data/raw/refs/heads/main/data/.+\.(rds|csv)$"
    )
    for url in df["rds_url"]:
        assert url_pattern.match(url), url
    for url in df["csv_url"]:
        assert url_pattern.match(url), url


def test_unique_names():
    names = catalog.names()
    assert len(names) == len(set(names))


def test_find_known_dataset():
    entry = catalog.find("federal_muni_harm_25")
    assert entry["name"] == "federal_muni_harm_25"
    assert entry["rds_url"].endswith("federal_muni_harm_25.rds")
    assert "2025" in entry["description"]


def test_find_unknown_raises():
    with pytest.raises(KeyError):
        catalog.find("not_a_real_dataset")
