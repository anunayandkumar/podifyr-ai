"""Cache manager: disk-based caching with content-hash invalidation for expensive operations."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import platformdirs
from diskcache import Cache

from podifyr.core.constants import (
    APP_NAME,
    CACHE_NAMESPACE_AUDIO,
    CACHE_NAMESPACE_PARSE,
    CACHE_NAMESPACE_SCRIPT,
    DEFAULT_CACHE_TTL_SECONDS,
)
from podifyr.logging import get_logger


logger = get_logger(__name__)


class CacheManager:
    """Manages disk-based caching with content-hash invalidation.

    Uses diskcache for thread-safe, persistent key-value storage.
    Cache keys are content-hashed to automatically invalidate when source changes.
    """

    def __init__(
        self,
        cache_dir: Path | None = None,
        ttl: int = DEFAULT_CACHE_TTL_SECONDS,
        enabled: bool = True,
    ) -> None:
        self._enabled = enabled
        self._ttl = ttl

        if cache_dir is None:
            cache_dir = Path(platformdirs.user_cache_dir(APP_NAME))

        self._cache_dir = cache_dir

        if self._enabled:
            self._cache_dir.mkdir(parents=True, exist_ok=True)
            self._cache = Cache(str(self._cache_dir))
            logger.info("cache_initialized", directory=str(self._cache_dir), ttl=ttl)
        else:
            self._cache = None
            logger.info("cache_disabled")

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def cache_dir(self) -> Path:
        return self._cache_dir

    @staticmethod
    def _compute_hash(content: str) -> str:
        """Compute a SHA-256 hash of content for cache key generation."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]

    def _make_key(self, namespace: str, identifier: str, content_hash: str) -> str:
        """Construct a namespaced cache key."""
        return f"{namespace}:{identifier}:{content_hash}"

    def get_parsed_module(self, file_path: str, file_content: str) -> dict[str, Any] | None:
        """Retrieve cached parse result for a file.

        Args:
            file_path: Path to the file (used as identifier).
            file_content: Current file content (used for hash-based invalidation).

        Returns:
            Cached parse result dict, or None on miss.
        """
        if not self._enabled or self._cache is None:
            return None

        content_hash = self._compute_hash(file_content)
        key = self._make_key(CACHE_NAMESPACE_PARSE, file_path, content_hash)

        try:
            result = self._cache.get(key)
            if result is not None:
                logger.debug("cache_hit", namespace="parse", file=file_path)
                return json.loads(result)  # type: ignore[no-any-return]
        except Exception as exc:  # noqa: BLE001
            logger.warning("cache_read_error", error=str(exc))

        return None

    def set_parsed_module(self, file_path: str, file_content: str, data: dict[str, Any]) -> None:
        """Store a parse result in the cache.

        Args:
            file_path: Path to the file.
            file_content: Current file content (for hash generation).
            data: Parse result to cache.
        """
        if not self._enabled or self._cache is None:
            return

        content_hash = self._compute_hash(file_content)
        key = self._make_key(CACHE_NAMESPACE_PARSE, file_path, content_hash)

        try:
            self._cache.set(key, json.dumps(data), expire=self._ttl)
            logger.debug("cache_set", namespace="parse", file=file_path)
        except Exception as exc:  # noqa: BLE001
            logger.warning("cache_write_error", error=str(exc))

    def get_script(self, module_name: str, metadata_hash: str) -> str | None:
        """Retrieve cached script for a module."""
        if not self._enabled or self._cache is None:
            return None

        key = self._make_key(CACHE_NAMESPACE_SCRIPT, module_name, metadata_hash)

        try:
            result = self._cache.get(key)
            if result is not None:
                logger.debug("cache_hit", namespace="script", module=module_name)
                return str(result)
        except Exception as exc:  # noqa: BLE001
            logger.warning("cache_read_error", error=str(exc))

        return None

    def set_script(self, module_name: str, metadata_hash: str, script: str) -> None:
        """Store a generated script in the cache."""
        if not self._enabled or self._cache is None:
            return

        key = self._make_key(CACHE_NAMESPACE_SCRIPT, module_name, metadata_hash)

        try:
            self._cache.set(key, script, expire=self._ttl)
            logger.debug("cache_set", namespace="script", module=module_name)
        except Exception as exc:  # noqa: BLE001
            logger.warning("cache_write_error", error=str(exc))

    def clear(self) -> int:
        """Clear all cached entries.

        Returns:
            Number of entries cleared.
        """
        if not self._enabled or self._cache is None:
            return 0

        try:
            count = len(self._cache)
            self._cache.clear()
            logger.info("cache_cleared", entries=count)
            return count
        except Exception as exc:  # noqa: BLE001
            logger.error("cache_clear_error", error=str(exc))
            return 0

    def stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        if not self._enabled or self._cache is None:
            return {"enabled": False, "entries": 0, "size_bytes": 0}

        try:
            return {
                "enabled": True,
                "entries": len(self._cache),
                "size_bytes": self._cache.volume(),
                "directory": str(self._cache_dir),
                "ttl_seconds": self._ttl,
            }
        except Exception as exc:  # noqa: BLE001
            logger.warning("cache_stats_error", error=str(exc))
            return {"enabled": True, "entries": -1, "error": str(exc)}

    def close(self) -> None:
        """Close the cache connection."""
        if self._cache is not None:
            try:
                self._cache.close()
            except Exception:  # noqa: BLE001
                pass
