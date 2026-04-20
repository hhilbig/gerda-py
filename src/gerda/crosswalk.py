"""gerda.party_crosswalk — map GERDA party names to ParlGov attributes."""

from __future__ import annotations

from collections.abc import Iterable
from functools import cache
from importlib.resources import files

import pandas as pd


@cache
def _lookup() -> pd.DataFrame:
    path = files("gerda").joinpath("_data/party_crosswalk.parquet")
    with path.open("rb") as fh:
        return pd.read_parquet(fh)


def _available_destinations() -> list[str]:
    return [c for c in _lookup().columns if c != "party_gerda"]


def party_crosswalk(party_gerda: Iterable[str | None], destination: str) -> pd.Series:
    """Map GERDA party names to a column of ParlGov's view_party.

    Parameters
    ----------
    party_gerda
        Iterable of GERDA party names (lowercase, underscores). Unknown names
        return NA.
    destination
        Target column. See ``party_crosswalk.destinations()`` for options.

    Returns
    -------
    pandas.Series with one entry per input, dtype matching `destination`.
    """
    lt = _lookup()
    available = _available_destinations()

    if not isinstance(destination, str):
        raise TypeError(
            f"destination must be a single string. Available: {', '.join(available)}"
        )
    if destination not in available:
        raise ValueError(
            f"'{destination}' is not a valid destination. Available: {', '.join(available)}"
        )

    if isinstance(party_gerda, str):
        raise TypeError(
            "party_gerda must be a sequence of strings (e.g. list, tuple, or pd.Series), "
            "not a single string. Wrap a single name in a list: ['cdu']."
        )

    keys = pd.Series(list(party_gerda), dtype="object")
    for value in keys:
        if value is not None and not isinstance(value, str) and not pd.isna(value):
            raise TypeError(
                f"party_gerda must contain strings or None; got {type(value).__name__}: {value!r}"
            )
    mapping = dict(zip(lt["party_gerda"], lt[destination]))
    return keys.map(mapping)


def destinations() -> list[str]:
    """List the available destination columns for ``party_crosswalk``."""
    return _available_destinations()
