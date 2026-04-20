# gerda

Lightweight Python loader for the [German Election Database (GERDA)](https://www.german-elections.com).
Downloads and returns pandas DataFrames for German federal, state, local,
mayoral, county, and European Parliament elections (1953–2025), plus boundary
crosswalks. Python port of the [gerda R package](https://github.com/hhilbig/gerda).

## Install

```bash
pip install git+https://github.com/hhilbig/gerda-py
pip install "gerda[polars] @ git+https://github.com/hhilbig/gerda-py"
```

A PyPI release is planned; once published, `pip install gerda` will work.

Requires Python 3.11+.

## Use

```python
import gerda

# List all 39 datasets
gerda.datasets()

# Load federal county-level results
df = gerda.load("federal_cty_harm")

# Load harmonized municipal data and convert to polars
df = gerda.load("federal_muni_harm_25", as_polars=True)

# Force a fresh download (bypass cache)
df = gerda.load("federal_cty_harm", refresh=True)
```

Files are downloaded from the [GERDA data repository](https://github.com/awiedem/german_election_data)
and cached in a platform-specific user cache directory: `~/.cache/gerda/` on
Linux, `~/Library/Caches/gerda/` on macOS, `%LOCALAPPDATA%\gerda\Cache\gerda`
on Windows. The exact path is available at runtime:

```python
from gerda.cache import cache_dir
print(cache_dir())
```

Cached files keep their original dataset names (e.g. `federal_cty_harm.rds`),
so it's safe to inspect or prune the cache by hand. RDS files are read with
[`pyreadr`](https://github.com/ofajardo/pyreadr); column dtypes (notably
string AGS codes with leading zeros) are preserved automatically.

## Party crosswalk

Map GERDA party names to ParlGov attributes:

```python
import gerda

gerda.party_crosswalk(["cdu", "spd", "linke_pds"], "left_right")
# 0    6.2503
# 1    3.6451
# 2    1.2152
# dtype: float64

gerda.party_crosswalk(["cdu", "afd"], "family_name_short")
# 0      chr
# 1    right
```

See `gerda.crosswalk.destinations()` for the full list of 21 destination
columns (party names, family, ideology scales, identifiers).

## Scope

This package wraps three of the R package's nine functions: `load`,
`datasets`, and `party_crosswalk`. The bundled INKAR / Zensus 2022 tables and
their merge helpers (`add_gerda_covariates`, `add_gerda_census`) are
intentionally **not** ported — Python users can do their own merges. If you
need them, use the R package.

## Citation

Heddesheimer, Sichart, Wiedemann, and Hilbig.
"German Elections Database (GERDA)."
*Scientific Data* (2025). [doi:10.1038/s41597-025-04811-5](https://doi.org/10.1038/s41597-025-04811-5)
