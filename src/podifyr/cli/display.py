"""Rich display utilities for CLI output."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.table import Table
from rich.theme import Theme

from podifyr import __version__
from podifyr.graph.models import GraphMetrics


# Custom theme for consistent branding
PODIFYR_THEME = Theme(
    {
        "info": "cyan",
        "success": "green",
        "warning": "yellow",
        "error": "red bold",
        "highlight": "magenta",
        "module": "blue bold",
    }
)

console = Console(theme=PODIFYR_THEME)


def print_banner() -> None:
    """Print the podifyr startup banner."""
    console.print(
        Panel.fit(
            f"[bold blue]podifyr-ai[/bold blue] v{__version__}\n"
            "[dim]AI-powered podcast-style architecture walkthroughs[/dim]",
            title="🎙️  Podifyr-AI",
            border_style="blue",
        )
    )


def print_target_info(repo_path: str, output_dir: str) -> None:
    """Display target repository and output directory info."""
    console.print(f"  [dim]Target:[/dim]  [cyan]{repo_path}[/cyan]")
    console.print(f"  [dim]Output:[/dim]  [cyan]{output_dir}[/cyan]")
    console.print()


def print_parse_summary(file_count: int, parsed_count: int, errors: int) -> None:
    """Display parsing results summary."""
    if errors > 0:
        console.print(
            f"  ✓ Parsed [success]{parsed_count}[/success]/{file_count} files "
            f"([warning]{errors} errors[/warning])"
        )
    else:
        console.print(f"  ✓ Parsed [success]{parsed_count}[/success] modules")


def print_graph_summary(metrics: GraphMetrics) -> None:
    """Display dependency graph summary."""
    parts = [
        f"[success]{metrics.node_count}[/success] nodes",
        f"[success]{metrics.edge_count}[/success] edges",
    ]
    if metrics.has_cycles:
        parts.append("[warning]cycles detected[/warning]")

    console.print(f"  ✓ Graph: {', '.join(parts)}")


def print_graph_details(metrics: GraphMetrics) -> None:
    """Display detailed graph metrics in a table."""
    table = Table(title="Dependency Graph Metrics", show_header=True)
    table.add_column("Metric", style="dim")
    table.add_column("Value", style="cyan")

    table.add_row("Nodes", str(metrics.node_count))
    table.add_row("Edges", str(metrics.edge_count))
    table.add_row("Density", f"{metrics.density:.4f}")
    table.add_row("Connected Components", str(metrics.connected_components))
    table.add_row("Has Cycles", "Yes ⚠️" if metrics.has_cycles else "No ✓")
    table.add_row("Longest Path", str(metrics.longest_path_length))

    if metrics.most_depended_on:
        table.add_row("Most Depended On", ", ".join(metrics.most_depended_on[:3]))
    if metrics.most_dependencies:
        table.add_row("Most Dependencies", ", ".join(metrics.most_dependencies[:3]))

    console.print(table)


def print_completion(output_dir: str, audio_path: str | None = None) -> None:
    """Display completion message."""
    console.print()
    if audio_path:
        console.print(f"  🎧 Audio: [cyan]{audio_path}[/cyan]")
    console.print(f"\n[bold success]✨ Done![/bold success] Output: [cyan]{output_dir}[/cyan]\n")


def print_error(message: str) -> None:
    """Display an error message."""
    console.print(f"[error]Error:[/error] {message}")


def create_progress() -> Progress:
    """Create a configured rich Progress instance for the pipeline."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=30),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
        transient=False,
    )
