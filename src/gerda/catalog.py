"""Dataset catalog: list of 39 GERDA datasets with their GitHub paths."""

from __future__ import annotations

import json
from functools import cache
from importlib.resources import files

import pandas as pd

_BASE_URL = "https://github.com/awiedem/german_election_data/raw/refs/heads/main/data/"


@cache
def _entries() -> list[dict[str, str]]:
    raw = files("gerda").joinpath("_catalog.json").read_text(encoding="utf-8")
    return json.loads(raw)


@cache
def load_catalog() -> pd.DataFrame:
    rows = []
    for entry in _entries():
        rows.append(
            {
                "data_name": entry["name"],
                "description": entry["description"],
                "rds_url": f"{_BASE_URL}{entry['path']}.rds",
                "csv_url": f"{_BASE_URL}{entry['path']}.csv",
            }
        )
    return pd.DataFrame(rows)


def datasets() -> pd.DataFrame:
    """Return a DataFrame listing all available GERDA datasets."""
    return load_catalog()[["data_name", "description"]].copy()


def names() -> list[str]:
    return [entry["name"] for entry in _entries()]


def find(name: str) -> dict[str, str]:
    """Return the catalog entry for `name`. Raises KeyError if unknown."""
    for entry in _entries():
        if entry["name"] == name:
            return {
                "name": entry["name"],
                "description": entry["description"],
                "rds_url": f"{_BASE_URL}{entry['path']}.rds",
                "csv_url": f"{_BASE_URL}{entry['path']}.csv",
            }
    raise KeyError(name)
