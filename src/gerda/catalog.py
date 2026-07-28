"""Dataset catalog: list of 47 GERDA datasets with their GitHub paths."""

from __future__ import annotations

import json
from functools import cache
from importlib.resources import files
from typing import Any

import pandas as pd

_BASE_URL = "https://github.com/awiedem/german_election_data/raw/refs/heads/main/data/"


_METADATA_COLUMNS = [
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


@cache
def _entries() -> list[dict[str, Any]]:
    raw = files("gerda").joinpath("_catalog.json").read_text(encoding="utf-8")
    return json.loads(raw)


@cache
def load_catalog() -> pd.DataFrame:
    rows = []
    for entry in _entries():
        formats = entry["formats"].split(",")
        rows.append({
            "data_name": entry["name"],
            "description": entry["description"],
            "election_type": entry["election_type"],
            "geographic_level": entry["geographic_level"],
            "year_start": entry["year_start"],
            "year_end": entry["year_end"],
            "boundary": entry["boundary"],
            "formats": entry["formats"],
            "candidate_info": entry["candidate_info"],
            "rds_url": (
                f"{_BASE_URL}{entry['path']}.rds" if "rds" in formats else None
            ),
            "csv_url": (
                f"{_BASE_URL}{entry['path']}.csv" if "csv" in formats else None
            ),
        })
    return pd.DataFrame(rows)


def datasets() -> pd.DataFrame:
    """Return available datasets and structured selection metadata."""
    return load_catalog()[_METADATA_COLUMNS].copy()


def names() -> list[str]:
    return [entry["name"] for entry in _entries()]


def find(name: str) -> dict[str, Any]:
    """Return the catalog entry for `name`. Raises KeyError if unknown."""
    for entry in _entries():
        if entry["name"] == name:
            formats = entry["formats"].split(",")
            result = dict(entry)
            result["rds_url"] = (
                f"{_BASE_URL}{entry['path']}.rds" if "rds" in formats else None
            )
            result["csv_url"] = (
                f"{_BASE_URL}{entry['path']}.csv" if "csv" in formats else None
            )
            return result
    raise KeyError(name)
