"""Opt-in live-download smoke tests. Run with: uv run pytest -m network"""

from __future__ import annotations

import pandas as pd
import pytest

from gerda import cache, load


pytestmark = pytest.mark.network

NEW_DATASETS = [
    ("federal_wkr_unharm", {"election_year", "wkr_nr"}),
    ("federal_wkr_unharm_long", {"election_year", "wkr_nr", "party"}),
    ("federal_wkr_2021_on_2025", {"wkr_nr", "state"}),
    ("wkr_2021_to_2025_crosswalk", {"wkr_nr", "state"}),
    ("ltw_wkr_unharm", {"state", "election_year", "wkr_nr"}),
    ("ltw_wkr_unharm_long", {"state", "election_year", "wkr_nr", "party"}),
    ("landrat_unharm", {"ags", "election_date"}),
    ("landrat_candidates", {"ags", "candidate_name"}),
    ("county_council_seats", {"county", "year"}),
]


@pytest.fixture
def network_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(cache, "cache_dir", lambda: tmp_path)
    return tmp_path


def test_live_download_federal_cty_harm(network_cache):
    """Hit the real GitHub URL and confirm the dataset round-trips."""
    df = load("federal_cty_harm")
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    assert "county_code" in df.columns
    assert "election_year" in df.columns


def test_live_download_with_extension(network_cache):
    df = load("federal_cty_harm.rds")
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0


@pytest.mark.parametrize(("name", "expected_columns"), NEW_DATASETS)
def test_new_dataset_is_live_and_readable(name, expected_columns, network_cache):
    df = load(name, refresh=True)
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert expected_columns <= set(df.columns)
