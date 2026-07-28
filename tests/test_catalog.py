"""Tests for src/gerda/catalog.py."""

from __future__ import annotations

import json
import re
from importlib.resources import files
from pathlib import Path

import pandas as pd
import pytest

from gerda import catalog, datasets

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def test_catalog_has_47_entries():
    assert len(catalog.load_catalog()) == 47


def test_datasets_returns_dataframe():
    df = datasets()
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == [
        "data_name",
        "description",
        "election_type",
        "geographic_level",
        "year_start",
        "year_end",
        "boundary",
        "formats",
        "candidate_info",
    ]
    assert len(df) == 47


def test_every_url_is_well_formed():
    df = catalog.load_catalog()
    url_pattern = re.compile(
        r"^https://github\.com/awiedem/german_election_data/raw/refs/heads/main/data/.+\.(rds|csv)$"
    )
    for url in df["rds_url"]:
        assert url_pattern.match(url), url
    for url in df["csv_url"].dropna():
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


def test_recent_r_catalog_changes_are_present():
    expected = {
        "federal_wkr_unharm",
        "federal_wkr_unharm_long",
        "federal_wkr_2021_on_2025",
        "wkr_2021_to_2025_crosswalk",
        "ltw_wkr_unharm",
        "ltw_wkr_unharm_long",
        "landrat_unharm",
        "landrat_candidates",
        "county_council_seats",
    }
    assert expected <= set(catalog.names())
    assert "county_elec_harm_21" not in catalog.names()


def test_updated_municipal_metadata():
    entries = catalog.load_catalog().set_index("data_name")
    assert "1984-2026" in entries.loc["municipal_unharm", "description"]
    assert "1990-2026" in entries.loc["municipal_harm", "description"]
    assert "1990-2026" in entries.loc["municipal_harm_25", "description"]


def test_structured_metadata_for_new_families():
    entries = datasets().set_index("data_name")
    assert entries.loc["ltw_wkr_unharm", "geographic_level"] == "wahlkreis"
    assert entries.loc["landrat_candidates", "candidate_info"]
    assert entries.loc["landrat_candidates", "election_type"] == "landrat"
    assert entries.loc["county_council_seats", "boundary"] == "current"
    assert entries.loc["county_council_seats", "year_start"] == 2008


def test_rds_only_entries_do_not_advertise_csv():
    entry = catalog.find("crosswalk_ags_2023_to_2025")
    assert entry["formats"] == "rds"
    assert entry["rds_url"].endswith(".rds")
    assert entry["csv_url"] is None


def test_catalog_matches_r_0_8_1_snapshot():
    """Guard all names, descriptions, paths, and structured metadata."""
    packaged = json.loads(
        files("gerda").joinpath("_catalog.json").read_text(encoding="utf-8")
    )
    authoritative = json.loads(
        (FIXTURE_DIR / "r_catalog_0_8_1.json").read_text(encoding="utf-8")
    )
    assert packaged == authoritative
