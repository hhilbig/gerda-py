# gerda

Lightweight Python loader for the [German Election Database (GERDA)](https://www.german-elections.com).
Downloads and returns pandas DataFrames for German federal, state, local,
mayoral, Landrat, county, and European Parliament elections (1945–2026), plus boundary
crosswalks. Python port of the [gerda R package](https://github.com/hhilbig/gerda).

## Install

```bash
pip install gerda                 # base install (pandas)
pip install "gerda[polars]"       # adds polars output support
```

Requires Python 3.11+.

## Use

```python
import gerda

# List all 47 datasets with geography, years, boundary target, and formats
catalog = gerda.datasets()

# Load federal county-level results
df = gerda.load("federal_cty_harm")

# Load harmonized municipal data and convert to polars
df = gerda.load("federal_muni_harm_25", as_polars=True)

# Force a fresh download (bypass cache)
df = gerda.load("federal_cty_harm", refresh=True)

# State-election results by constituency (Wahlkreis)
ltw = gerda.load("ltw_wkr_unharm")

# County-executive (Landrat) candidates
landrat = gerda.load("landrat_candidates")

# Annual county-council seat composition on current boundaries
seats = gerda.load("county_council_seats")
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

## Dataset keys

The structured columns returned by `gerda.datasets()` can be used to select
datasets by election type, geographic level, years, boundary target, available
formats, and whether they contain candidate information.

- `federal_wkr_*`: federal constituencies, keyed by `wkr_nr` and election year;
  long files additionally identify vote type (`stimme`) and party.
- `ltw_wkr_*`: state constituencies, keyed by state, `wkr_nr`, and election
  year; long files additionally identify vote type and party.
- `landrat_unharm`: county-executive elections, identified by `ags`, election
  date, and round. `landrat_candidates` adds person-level candidates.
- `county_council_seats`: annual county seat composition on fixed current
  county boundaries, identified by county and year.
- `federal_cty_unharm`: use `county_code` and `election_year`. The legacy
  aliases `ags` and `year` remain through Python gerda 0.6 and will be removed
  in v0.7.

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

This package provides three workflows from the broader R package: `load`,
`datasets`, and `party_crosswalk`. The bundled INKAR / Zensus 2022 tables and
their merge helpers (`add_gerda_covariates`, `add_gerda_census`) are
intentionally **not** ported — Python users can do their own merges. If you
need them, use the R package.

## Citation

Heddesheimer, Sichart, Wiedemann, and Hilbig.
"German Elections Database (GERDA)."
*Scientific Data* (2025). [doi:10.1038/s41597-025-04811-5](https://doi.org/10.1038/s41597-025-04811-5)
