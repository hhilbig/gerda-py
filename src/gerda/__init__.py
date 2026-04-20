"""GERDA: German Election Database — lightweight Python loader."""

from gerda.catalog import datasets
from gerda.crosswalk import party_crosswalk
from gerda.load import load

__all__ = ["load", "datasets", "party_crosswalk"]
__version__ = "0.1.0"
