# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A lightweight Python port of the [gerda R package](https://github.com/hhilbig/gerda).
Three public functions:

- `gerda.load(name, *, refresh=False, as_polars=False, verbose=False)` — fetch a dataset, return a pandas (or polars) DataFrame.
- `gerda.datasets()` — return a DataFrame listing all available datasets.
- `gerda.party_crosswalk(party_gerda, destination)` — map GERDA party names to ParlGov attributes.

Out of scope: `add_gerda_covariates`, `add_gerda_census`, the bundled INKAR / Zensus tables, codebook getters, CSV format. Users do their own merges in pandas.

## Related repositories (must stay consistent)

- **R package** at `/Users/hanno/Documents/GitHub/gerda` — the API spec; this Python port mirrors its behaviour for `load_gerda_web`, `gerda_data_list`, and `party_crosswalk`. Schema changes there have implications here.
- **Data repository** at `/Users/hanno/Documents/GitHub/german_election_data` (hosted as `awiedem/german_election_data`) — source of truth for every downloadable dataset. The `data/*/final/` tree is the contract; `_catalog.json` here mirrors that tree.
- **Project website** at `/Users/hanno/Documents/GitHub/awiedem.github.io` — user-facing docs; if Python API changes, check `r-package.md` / `usage_notes.md` for cross-references.

When the R package's data dictionary in `R/load_gerda_web.R:76-207` changes (datasets added, paths renamed), `src/gerda/_catalog.json` must be updated to match. There is currently no automated audit.

## Build & test commands

- **Install + lock:** `uv sync`
- **Run all offline tests:** `uv run pytest`
- **Run a single test file:** `uv run pytest tests/test_load.py`
- **Run a single test:** `uv run pytest tests/test_load.py::test_strip_extension`
- **Run network tests (live downloads):** `uv run pytest -m network`
- **Smoke check:** `uv run python -c "import gerda; print(gerda.datasets().head())"`
- **Build wheel + sdist:** `uv build`
- **Publish to PyPI:** `uv publish` (only after manual review; do not auto-publish)

## Architecture

| File | Purpose |
|------|---------|
| `src/gerda/__init__.py` | Re-exports `load`, `datasets`, `party_crosswalk` |
| `src/gerda/catalog.py` | Reads `_catalog.json`, exposes `datasets()`, `find()`, `names()` |
| `src/gerda/_catalog.json` | 39-entry dataset dictionary (mirrors R's `entries` list) |
| `src/gerda/_fuzzy.py` | rapidfuzz-based typo suggestions, prefix-priority |
| `src/gerda/cache.py` | platformdirs-backed download cache (`~/.cache/gerda/`) |
| `src/gerda/load.py` | The `load()` entry point: lookup → cache → pyreadr → schema fix |
| `src/gerda/crosswalk.py` | Reads `_data/party_crosswalk.parquet`, exposes `party_crosswalk()` |
| `src/gerda/_data/party_crosswalk.parquet` | Bundled lookup table extracted once from the R package's `R/sysdata.rda` |

Data flow: `gerda.load(name)` → catalog lookup → if unknown, fuzzy suggestions raise `KeyError` with `Did you mean...` → otherwise cache hit or HTTP download → pyreadr parses RDS → schema normalization for `federal_cty_unharm` → optional polars cast.

## One-time data extraction

The party crosswalk lookup table is extracted from the R package's `R/sysdata.rda`. To regenerate `src/gerda/_data/party_crosswalk.parquet`:

```bash
cd /Users/hanno/Documents/GitHub/gerda
Rscript -e '
load("R/sysdata.rda")
arrow::write_parquet(
  lookup_table,
  "../gerda-py/src/gerda/_data/party_crosswalk.parquet"
)
'
```

This needs to be re-run whenever the upstream lookup table changes.

## Conventions

- **API style:** Pythonic, namespaced (`gerda.load`, not `load_gerda_web`).
- **Error handling:** raise. No `on_error="warn"` switch; users wrap in try/except.
- **File format:** RDS only via `pyreadr`. CSV is intentionally not supported — RDS preserves dtypes (notably string AGS codes with leading zeros).
- **Caching:** files keyed by `sha1(url)`; refresh via `refresh=True`.
- **Polars:** optional dep behind `gerda[polars]`. Import lazily inside `_to_polars()` so the base install never imports polars.
- **Internal modules:** prefix with `_` (e.g. `_fuzzy.py`, `_catalog.json`, `_data/`). Public surface is exactly the three exports in `__init__.py`.
- **Dataset names:** lowercase, underscores, no extension. The loader strips `.rds`/`.csv` if a user passes one.

## Important gotchas

- **AGS codes are strings.** `"01001"` not `1001`. The reason RDS-via-pyreadr beats CSV-via-pandas is automatic dtype preservation. If you ever switch to CSV, you must re-impose dtypes manually.
- **`federal_cty_unharm` schema alias.** The upstream file ships `ags`/`year`; we add `county_code`/`election_year` aliases with a `DeprecationWarning` flagged for v0.7 removal. Mirrors R behaviour.
- **`federal_muni_harm` is removed.** Users get a `KeyError` pointing them at `_21` and `_25` variants. Mirrors R.
- **Catalog drift.** Every time `R/load_gerda_web.R` adds or renames a dataset, `_catalog.json` must be updated. A future enhancement could fetch the upstream catalog at build time.
