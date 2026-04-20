"""Local file cache for downloaded GERDA datasets."""

from __future__ import annotations

import hashlib
from pathlib import Path

import requests
from platformdirs import user_cache_dir

_TIMEOUT_SECONDS = 300


def cache_dir() -> Path:
    path = Path(user_cache_dir("gerda"))
    path.mkdir(parents=True, exist_ok=True)
    return path


def _cache_path(url: str) -> Path:
    suffix = Path(url.split("?", 1)[0]).suffix or ".bin"
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()
    return cache_dir() / f"{digest}{suffix}"


def cached_download(url: str, *, refresh: bool = False, verbose: bool = False) -> Path:
    """Download `url` to the cache and return the local path.

    Re-uses the existing file unless `refresh=True`.
    """
    path = _cache_path(url)
    if path.exists() and not refresh:
        if verbose:
            print(f"[gerda] cache hit: {path}")
        return path

    if verbose:
        print(f"[gerda] downloading {url}")
    with requests.get(url, stream=True, timeout=_TIMEOUT_SECONDS) as response:
        response.raise_for_status()
        tmp = path.with_suffix(path.suffix + ".part")
        with open(tmp, "wb") as fh:
            for chunk in response.iter_content(chunk_size=1 << 16):
                if chunk:
                    fh.write(chunk)
        tmp.replace(path)
    return path
