"""Generate command: the primary podifyr workflow."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from podifyr.cli.display import (
    console,
    create_progress,
    print_banner,
    print_completion,
    print_error,
    print_graph_details,
    print_graph_summary,
    print_parse_summary,
    print_target_info,
)
from podifyr.core.constants import CHUNKS_SUBDIR, FINAL_OUTPUT_FILENAME, SCRIPT_FILENAME
from podifyr.logging import configure_logging, get_logger


logger = get_logger(__name__)


def generate(
    repo_path: Path = typer.Argument(
        ...,
        help="Path to the target Python repository to analyze.",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    output_dir: Path = typer.Option(
        Path("./podifyr_output"),
        "--output", "-o",
        help="Directory for generated output files.",
        resolve_path=True,
    ),
    api_key: Optional[str] = typer.Option(  # noqa: UP007
        None,
        "--api-key",
        help="OpenAI or Azure API key (overrides env/config).",
        envvar="OPENAI_API_KEY",
    ),
    tts_backend: Optional[str] = typer.Option(  # noqa: UP007
        None,
        "--tts-backend",
        help="TTS backend: 'edge' (free), 'openai', or 'elevenlabs'.",
    ),
    voice: Optional[str] = typer.Option(  # noqa: UP007
        None,
        "--voice",
        help="TTS voice (overrides config). OpenAI: alloy/echo/fable/onyx/nova/shimmer.",
    ),
    azure_endpoint: Optional[str] = typer.Option(  # noqa: UP007
        None,
        "--azure-endpoint",
        help="Azure OpenAI endpoint URL (enables Azure mode).",
        envvar="PODIFYR_AZURE_ENDPOINT",
    ),
    azure_deployment: Optional[str] = typer.Option(  # noqa: UP007
        None,
        "--azure-deployment",
        help="Azure chat model deployment name.",
        envvar="PODIFYR_AZURE_CHAT_DEPLOYMENT",
    ),
    skip_audio: bool = typer.Option(
        False,
        "--skip-audio",
        help="Generate script only, skip audio synthesis.",
    ),
    no_cache: bool = typer.Option(
        False,
        "--no-cache",
        help="Disable caching for this run.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose", "-V",
        help="Enable verbose debug logging.",
    ),
    concurrency: Optional[int] = typer.Option(  # noqa: UP007
        None,
        "--concurrency", "-c",
        help="Max concurrent TTS API requests (overrides config).",
        min=1,
        max=20,
    ),
    show_graph_details: bool = typer.Option(
        False,
        "--graph-details",
        help="Show detailed dependency graph metrics.",
    ),
) -> None:
    """Generate a podcast-style audio walkthrough of a Python repository.

    Analyzes the repository's AST, builds a dependency graph, generates a
    conversational script using AI agents, and synthesizes audio narration.
    """
    import os

    # Apply CLI overrides to environment before settings load
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
    if azure_endpoint:
        os.environ["PODIFYR_AZURE_ENABLED"] = "true"
        os.environ["PODIFYR_AZURE_ENDPOINT"] = azure_endpoint
    if azure_deployment:
        os.environ["PODIFYR_AZURE_CHAT_DEPLOYMENT"] = azure_deployment
    if api_key and azure_endpoint:
        os.environ["PODIFYR_AZURE_API_KEY"] = api_key
    if tts_backend:
        os.environ["PODIFYR_TTS_BACKEND"] = tts_backend

    # Configure logging
    log_level = "DEBUG" if verbose else "INFO"
    configure_logging(level=log_level)

    print_banner()
    print_target_info(str(repo_path), str(output_dir))

    # Setup output directories
    output_dir.mkdir(parents=True, exist_ok=True)
    chunks_dir = output_dir / CHUNKS_SUBDIR
    chunks_dir.mkdir(parents=True, exist_ok=True)

    # Initialize cache (reset settings to pick up CLI overrides)
    from podifyr.cache import CacheManager
    from podifyr.config import get_settings
    from podifyr.config.settings import reset_settings

    reset_settings()
    settings = get_settings()
    cache = CacheManager(
        cache_dir=settings.cache.directory,
        ttl=settings.cache.ttl_seconds,
        enabled=settings.cache.enabled and not no_cache,
    )

    try:
        _run_pipeline(
            repo_path=repo_path,
            output_dir=output_dir,
            chunks_dir=chunks_dir,
            cache=cache,
            voice=voice,
            skip_audio=skip_audio,
            concurrency=concurrency,
            show_graph_details=show_graph_details,
        )
    except KeyboardInterrupt:
        console.print("\n[warning]Interrupted by user.[/warning]")
        raise typer.Exit(code=130) from None
    finally:
        cache.close()


def _run_pipeline(
    *,
    repo_path: Path,
    output_dir: Path,
    chunks_dir: Path,
    cache: "CacheManager",
    voice: str | None,
    skip_audio: bool,
    concurrency: int | None,
    show_graph_details: bool,
) -> None:
    """Execute the full podifyr pipeline with progress tracking."""
    from podifyr.cache import CacheManager

    with create_progress() as progress:
        # ── Step 1: Parse AST ────────────────────────────────────────────
        task_parse = progress.add_task("[cyan]Parsing repository AST...", total=None)

        from podifyr.parsing import parse_directory

        parsed_modules = parse_directory(repo_path, cache=cache)
        progress.update(task_parse, total=1, completed=1)

        if not parsed_modules:
            print_error("No Python files found or all files failed to parse.")
            raise typer.Exit(code=1)

        print_parse_summary(
            file_count=len(parsed_modules),
            parsed_count=len(parsed_modules),
            errors=0,
        )

        # ── Step 2: Build Dependency Graph ───────────────────────────────
        task_graph = progress.add_task("[cyan]Building dependency graph...", total=1)

        from podifyr.graph import build_dependency_graph, get_topological_sort
        from podifyr.graph.analyzer import compute_graph_metrics

        dep_graph = build_dependency_graph(parsed_modules)
        reading_order = get_topological_sort(dep_graph)
        metrics = compute_graph_metrics(dep_graph)
        progress.update(task_graph, completed=1)

        print_graph_summary(metrics)
        if show_graph_details:
            print_graph_details(metrics)

        # ── Step 3: Generate Script ──────────────────────────────────────
        task_script = progress.add_task(
            "[cyan]Generating walkthrough script...",
            total=len(reading_order),
        )

        from podifyr.agents import generate_script_for_module
        from podifyr.utils.fs import normalize_module_path

        # Build module lookup
        module_lookup: dict[str, object] = {}
        for mod in parsed_modules:
            name = mod.module_name or normalize_module_path(mod.file_path)
            module_lookup[name] = mod

        script_chunks: list[str] = []
        script_module_names: list[str] = []

        for module_name in reading_order:
            metadata = module_lookup.get(module_name)
            if metadata is None:
                progress.advance(task_script)
                continue

            chunk = generate_script_for_module(metadata, dep_graph, cache=cache)  # type: ignore[arg-type]
            script_chunks.append(chunk)
            script_module_names.append(module_name)
            progress.advance(task_script)

        # Save script
        _save_script(output_dir / SCRIPT_FILENAME, script_module_names, script_chunks)
        console.print(f"  ✓ Script: [cyan]{output_dir / SCRIPT_FILENAME}[/cyan]")

        if skip_audio:
            console.print("\n[warning]Audio generation skipped (--skip-audio).[/warning]")
            print_completion(str(output_dir))
            return

        # ── Step 4: Synthesize Audio ─────────────────────────────────────
        task_audio = progress.add_task("[cyan]Synthesizing audio...", total=2)

        from podifyr.audio import generate_audio_chunks, stitch_audio

        try:
            audio_paths = generate_audio_chunks(
                script_chunks=script_chunks,
                output_dir=chunks_dir,
                voice=voice,
                max_concurrent=concurrency,
            )
            progress.advance(task_audio)
        except Exception as exc:
            print_error(str(exc))
            raise typer.Exit(code=1) from exc

        if not audio_paths:
            print_error("No audio chunks were generated successfully.")
            raise typer.Exit(code=1)

        # Stitch
        final_audio = output_dir / FINAL_OUTPUT_FILENAME
        success = stitch_audio(input_dir=chunks_dir, final_output_path=final_audio)
        progress.advance(task_audio)

        if success:
            print_completion(str(output_dir), audio_path=str(final_audio))
        else:
            console.print(
                "  [warning]Audio stitching failed. Individual chunks are in chunks/.[/warning]"
            )
            print_completion(str(output_dir))


def _save_script(path: Path, module_names: list[str], chunks: list[str]) -> None:
    """Save the generated script to a markdown file."""
    try:
        with path.open("w", encoding="utf-8") as f:
            f.write("# 🎙️ Architecture Walkthrough Script\n\n")
            f.write("*Generated by podifyr*\n\n---\n\n")

            for i, (name, chunk) in enumerate(zip(module_names, chunks), 1):
                f.write(f"## {i}. `{name}`\n\n")
                f.write(f"{chunk}\n\n---\n\n")
    except OSError as exc:
        logger.error("script_save_failed", error=str(exc))
