"""gerda.load — fetch a GERDA dataset by name."""

from __future__ import annotations

import warnings
from typing import Any

import pandas as pd

from gerda import _fuzzy, catalog, cache

_DEPRECATED_FEDERAL_MUNI_HARM_MSG = (
    "The dataset 'federal_muni_harm' has been replaced with two boundary-specific versions:\n"
    "  - 'federal_muni_harm_21': harmonized to 2021 boundaries\n"
    "  - 'federal_muni_harm_25': harmonized to 2025 boundaries\n"
    "Pick one of these. See gerda.datasets() for the full list."
)


def load(
    name: str,
    *,
    refresh: bool = False,
    as_polars: bool = False,
    verbose: bool = False,
) -> Any:
    """Load a GERDA dataset by name.

    Parameters
    ----------
    name
        Dataset name (see ``gerda.datasets()``). A trailing ``.rds`` or ``.csv``
        is stripped if present.
    refresh
        If True, bypass the local cache and re-download from GitHub.
    as_polars
        If True, return a ``polars.DataFrame`` instead of pandas. Requires the
        ``polars`` extra (``pip install gerda[polars]``).
    verbose
        Emit progress messages.
    """
    if not isinstance(name, str) or not name:
        raise TypeError("name must be a non-empty string")

    name = _strip_extension(name, verbose=verbose)

    if name == "federal_muni_harm":
        raise KeyError(_DEPRECATED_FEDERAL_MUNI_HARM_MSG)

    try:
        entry = catalog.find(name)
    except KeyError:
        suggestions = _fuzzy.suggest(name, catalog.names())
        if suggestions:
            hint = " or ".join(f"'{s}'" for s in suggestions[:2])
            raise KeyError(
                f"Dataset '{name}' not found. Did you mean: {hint}? "
                f"See gerda.datasets() for the full list."
            ) from None
        raise KeyError(
            f"Dataset '{name}' not found. See gerda.datasets() for the full list."
        ) from None

    local_path = cache.cached_download(entry["rds_url"], refresh=refresh, verbose=verbose)
    df = _read_rds(local_path)
    df = _normalize_schema(name, df)

    if as_polars:
        return _to_polars(df)
    return df


def _strip_extension(name: str, *, verbose: bool) -> str:
    # Match R's case-sensitive substring check (load_gerda_web.R:61-69):
    # only literal lowercase ".rds"/".csv" suffixes are stripped.
    if len(name) > 4 and name[-4:] in (".rds", ".csv"):
        if verbose:
            print(f"[gerda] dropping file extension from '{name}'")
        return name[:-4]
    return name


def _read_rds(path) -> pd.DataFrame:
    # Lazy import: pyreadr loads a C extension (~200ms). Keeping it out of
    # `import gerda` makes the package cheap to import in notebooks.
    import pyreadr

    result = pyreadr.read_r(str(path))
    if not result:
        raise RuntimeError(f"pyreadr returned no objects from {path}")
    # GERDA RDS files contain a single object; take the first.
    return next(iter(result.values()))


def _normalize_schema(name: str, df: pd.DataFrame) -> pd.DataFrame:
    """Port of load_gerda_web.R:332-350 — federal_cty_unharm column aliases."""
    if name != "federal_cty_unharm":
        return df

    added = False
    if "ags" in df.columns and "county_code" not in df.columns:
        df = df.assign(county_code=df["ags"])
        added = True
    if "year" in df.columns and "election_year" not in df.columns:
        df = df.assign(election_year=df["year"])
        added = True
    if added:
        warnings.warn(
            "'federal_cty_unharm' now exposes 'county_code' and 'election_year' to match "
            "other county-level datasets. The upstream 'ags' and 'year' columns remain for "
            "backwards compatibility but will be removed in v0.7.",
            DeprecationWarning,
            stacklevel=3,
        )
    return df


def _to_polars(df: pd.DataFrame):
    try:
        import polars as pl
    except ImportError as exc:
        raise ImportError(
            "polars is required for as_polars=True. Install with: pip install gerda[polars]"
        ) from exc
    return pl.from_pandas(df)
