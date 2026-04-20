"""Tests for src/gerda/cache.py."""

from __future__ import annotations

from pathlib import Path

import pytest
import responses

from gerda import cache


@pytest.fixture
def tmp_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(cache, "cache_dir", lambda: tmp_path)
    return tmp_path


@responses.activate
def test_cached_download_writes_file(tmp_cache):
    url = "https://example.com/data.rds"
    payload = b"\x1f\x8b\x08\x00fake-rds-bytes"
    responses.add(responses.GET, url, body=payload, status=200)

    path = cache.cached_download(url)

    assert path.exists()
    assert path.read_bytes() == payload
    assert path.parent == tmp_cache


@responses.activate
def test_second_call_hits_cache(tmp_cache):
    url = "https://example.com/cached.rds"
    payload = b"hello"
    responses.add(responses.GET, url, body=payload, status=200)

    first = cache.cached_download(url)
    # If a second HTTP call happened, responses would fail (registry is single-use).
    second = cache.cached_download(url)

    assert first == second
    assert len(responses.calls) == 1


@responses.activate
def test_refresh_bypasses_cache(tmp_cache):
    url = "https://example.com/refresh.rds"
    responses.add(responses.GET, url, body=b"v1", status=200)
    responses.add(responses.GET, url, body=b"v2", status=200)

    cache.cached_download(url)
    path = cache.cached_download(url, refresh=True)

    assert path.read_bytes() == b"v2"
    assert len(responses.calls) == 2


@responses.activate
def test_http_error_raises(tmp_cache):
    url = "https://example.com/missing.rds"
    responses.add(responses.GET, url, status=404)

    import requests

    with pytest.raises(requests.HTTPError):
        cache.cached_download(url)


def test_cache_path_includes_extension(tmp_cache):
    p1 = cache._cache_path("https://example.com/foo.rds")
    p2 = cache._cache_path("https://example.com/foo.rds?download=")
    assert p1.suffix == ".rds"
    assert p2.suffix == ".rds"
    # Different URLs (with vs without query) hash to different files
    assert p1 != p2


def test_cache_dir_is_creatable():
    # default cache dir should be writable on this platform
    d = cache.cache_dir()
    assert isinstance(d, Path)
    assert d.exists()
