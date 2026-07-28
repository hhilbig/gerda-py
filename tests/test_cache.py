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
    for _ in range(cache._MAX_ATTEMPTS):
        responses.add(responses.GET, url, status=404)

    with pytest.raises(RuntimeError, match="after 3 attempts"):
        cache.cached_download(url)
    assert len(responses.calls) == 3


@responses.activate
def test_transient_failure_is_retried(tmp_cache, monkeypatch):
    url = "https://example.com/retry.rds"
    monkeypatch.setattr(cache.time, "sleep", lambda _: None)
    responses.add(responses.GET, url, status=503)
    responses.add(responses.GET, url, body=b"valid-rds", status=200)

    path = cache.cached_download(url)

    assert path.read_bytes() == b"valid-rds"
    assert len(responses.calls) == 2


@responses.activate
def test_lfs_pointer_is_rejected_and_not_cached(tmp_cache, monkeypatch):
    url = "https://example.com/pointer.rds"
    monkeypatch.setattr(cache.time, "sleep", lambda _: None)
    pointer = (
        b"version https://git-lfs.github.com/spec/v1\n"
        b"oid sha256:abc\nsize 123\n"
    )
    for _ in range(cache._MAX_ATTEMPTS):
        responses.add(responses.GET, url, body=pointer, status=200)

    with pytest.raises(RuntimeError, match="valid dataset"):
        cache.cached_download(url)

    assert not cache._cache_path(url).exists()
    assert not cache._cache_path(url).with_suffix(".rds.part").exists()


def test_cache_path_uses_readable_basename(tmp_cache):
    p = cache._cache_path(
        "https://github.com/awiedem/german_election_data/raw/refs/heads/main/data/"
        "federal_elections/county_level/final/federal_cty_harm.rds"
    )
    assert p.name == "federal_cty_harm.rds"


def test_cache_path_strips_query_string(tmp_cache):
    base = (
        "https://github.com/awiedem/german_election_data/raw/refs/heads/main/data/"
        "federal_elections/county_level/final/federal_cty_harm.rds"
    )
    p1 = cache._cache_path(base)
    p2 = cache._cache_path(base + "?download=")
    assert p1 == p2
    assert p1.name == "federal_cty_harm.rds"


def test_cache_path_falls_back_for_extensionless_url(tmp_cache):
    p = cache._cache_path("https://example.com/no-extension")
    assert p.suffix == ".bin"
    assert len(p.stem) == 40  # sha1 hex digest length


def test_cache_dir_is_creatable():
    # default cache dir should be writable on this platform
    d = cache.cache_dir()
    assert isinstance(d, Path)
    assert d.exists()
