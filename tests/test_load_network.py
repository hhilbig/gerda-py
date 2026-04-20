"""Opt-in live-download smoke tests. Run with: uv run pytest -m network"""

from __future__ import annotations

import pandas as pd
import pytest

from gerda import load


pytestmark = pytest.mark.network


def test_live_download_federal_cty_harm():
    """Hit the real GitHub URL and confirm the dataset round-trips."""
    df = load("federal_cty_harm")
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    assert "county_code" in df.columns
    assert "election_year" in df.columns


def test_live_download_with_extension():
    df = load("federal_cty_harm.rds")
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
