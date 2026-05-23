"""Cache command: manage the podifyr disk cache."""

from __future__ import annotations

import typer

from podifyr.cli.display import console


def cache_clear(
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Skip confirmation prompt.",
    ),
) -> None:
    """Clear all cached data (parsed modules, generated scripts)."""
    from podifyr.cache import CacheManager
    from podifyr.config import get_settings

    settings = get_settings()
    cache = CacheManager(
        cache_dir=settings.cache.directory,
        ttl=settings.cache.ttl_seconds,
        enabled=True,  # Force enabled to clear
    )

    stats = cache.stats()
    entries = stats.get("entries", 0)

    if entries == 0:
        console.print("[dim]Cache is already empty.[/dim]")
        cache.close()
        return

    if not force:
        confirmed = typer.confirm(f"Clear {entries} cached entries?")
        if not confirmed:
            console.print("[dim]Cancelled.[/dim]")
            cache.close()
            raise typer.Exit()

    cleared = cache.clear()
    cache.close()
    console.print(f"[success]✓ Cleared {cleared} cache entries.[/success]")


def cache_stats() -> None:
    """Display cache usage statistics."""
    from rich.table import Table

    from podifyr.cache import CacheManager
    from podifyr.config import get_settings

    settings = get_settings()
    cache = CacheManager(
        cache_dir=settings.cache.directory,
        ttl=settings.cache.ttl_seconds,
        enabled=settings.cache.enabled,
    )

    stats = cache.stats()
    cache.close()

    table = Table(title="Cache Statistics", show_header=True)
    table.add_column("Metric", style="dim")
    table.add_column("Value", style="cyan")

    table.add_row("Enabled", "Yes" if stats.get("enabled") else "No")
    table.add_row("Entries", str(stats.get("entries", 0)))

    size_bytes = stats.get("size_bytes", 0)
    if size_bytes > 1_048_576:
        size_str = f"{size_bytes / 1_048_576:.1f} MB"
    elif size_bytes > 1024:
        size_str = f"{size_bytes / 1024:.1f} KB"
    else:
        size_str = f"{size_bytes} bytes"
    table.add_row("Size", size_str)

    table.add_row("Directory", stats.get("directory", "N/A"))
    table.add_row("TTL", f"{stats.get('ttl_seconds', 0)} seconds")

    console.print(table)
