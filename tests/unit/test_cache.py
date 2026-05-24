"""Unit tests for the cache module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from podifyr.cache import CacheManager


if TYPE_CHECKING:
    from pathlib import Path


class TestCacheManager:
    """Tests for the disk cache manager."""

    def test_cache_disabled(self, tmp_dir: Path) -> None:
        """Should operate as no-op when disabled."""
        cache = CacheManager(cache_dir=tmp_dir / "cache", enabled=False)

        cache.set_parsed_module("test.py", "content", {"key": "value"})
        result = cache.get_parsed_module("test.py", "content")

        assert result is None
        cache.close()

    def test_cache_set_and_get(self, tmp_dir: Path) -> None:
        """Should store and retrieve cached values."""
        cache = CacheManager(cache_dir=tmp_dir / "cache", ttl=3600, enabled=True)

        data = {"file_path": "test.py", "imports": [], "classes": []}
        cache.set_parsed_module("test.py", "source code content", data)

        result = cache.get_parsed_module("test.py", "source code content")
        assert result == data
        cache.close()

    def test_cache_invalidation_on_content_change(self, tmp_dir: Path) -> None:
        """Should miss when file content changes (hash-based invalidation)."""
        cache = CacheManager(cache_dir=tmp_dir / "cache", ttl=3600, enabled=True)

        data = {"file_path": "test.py", "imports": []}
        cache.set_parsed_module("test.py", "original content", data)

        # Different content should miss
        result = cache.get_parsed_module("test.py", "modified content")
        assert result is None
        cache.close()

    def test_cache_clear(self, tmp_dir: Path) -> None:
        """Should clear all entries."""
        cache = CacheManager(cache_dir=tmp_dir / "cache", ttl=3600, enabled=True)

        cache.set_parsed_module("a.py", "aaa", {"a": 1})
        cache.set_parsed_module("b.py", "bbb", {"b": 2})

        cleared = cache.clear()
        assert cleared == 2

        assert cache.get_parsed_module("a.py", "aaa") is None
        cache.close()

    def test_cache_stats(self, tmp_dir: Path) -> None:
        """Should return accurate statistics."""
        cache = CacheManager(cache_dir=tmp_dir / "cache", ttl=3600, enabled=True)

        cache.set_parsed_module("test.py", "content", {"data": True})
        stats = cache.stats()

        assert stats["enabled"] is True
        assert stats["entries"] == 1
        assert stats["size_bytes"] > 0
        cache.close()

    def test_cache_script_operations(self, tmp_dir: Path) -> None:
        """Should cache and retrieve script content."""
        cache = CacheManager(cache_dir=tmp_dir / "cache", ttl=3600, enabled=True)

        cache.set_script("app.main", "abc123", "This is a generated script.")
        result = cache.get_script("app.main", "abc123")

        assert result == "This is a generated script."
        cache.close()

    def test_cache_script_miss_on_hash_change(self, tmp_dir: Path) -> None:
        """Should miss script cache when metadata hash changes."""
        cache = CacheManager(cache_dir=tmp_dir / "cache", ttl=3600, enabled=True)

        cache.set_script("app.main", "hash1", "Script v1")
        result = cache.get_script("app.main", "hash2")

        assert result is None
        cache.close()
