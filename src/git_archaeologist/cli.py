from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from .analyzer import CodeAnalyzer
from .formatters import RichFormatter

app = typer.Typer(
    name="git-arch",
    help="[bold yellow]git-archaeologist[/bold yellow] — Uncover WHY your code exists using AI",
    rich_markup_mode="rich",
    no_args_is_help=True,
)
console = Console()
err_console = Console(stderr=True)


def _make_analyzer(repo: Path, model: str, api_key: Optional[str]) -> CodeAnalyzer:
    try:
        return CodeAnalyzer(repo_path=repo, model=model, api_key=api_key)
    except ImportError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def why(
    target: str = typer.Argument(
        ...,
        help="File path or file:line or file:start-end (e.g. src/auth.py:42 or src/auth.py:10-50)",
        metavar="TARGET",
    ),
    repo: Path = typer.Option(Path("."), "--repo", "-r", help="Repository root path"),
    depth: int = typer.Option(50, "--depth", "-d", help="Max commits to analyze", min=1, max=500),
    format: str = typer.Option(
        "rich", "--format", "-f", help="Output format: rich | markdown | json"
    ),
    model: str = typer.Option("gpt-4o", "--model", "-m", help="OpenAI model"),
    api_key: Optional[str] = typer.Option(None, "--api-key", envvar="OPENAI_API_KEY", help="OpenAI API key"),
):
    """
    Explain WHY a piece of code exists by tracing its full git history.

    Examples:\n
      git-arch why src/auth/tokens.py\n
      git-arch why src/auth/tokens.py:42\n
      git-arch why src/auth/tokens.py:10-80 --depth 100\n
      git-arch why src/auth/tokens.py --format json | jq .narrative
    """
    analyzer = _make_analyzer(repo, model, api_key)

    with console.status(f"[bold yellow]Excavating history for [cyan]{target}[/cyan]...[/bold yellow]"):
        try:
            result = analyzer.analyze(target, depth=depth)
        except Exception as e:
            err_console.print(f"[red]Analysis failed:[/red] {e}")
            raise typer.Exit(1)

    formatter = RichFormatter(console)
    formatter.render(result, format=format)


@app.command()
def timeline(
    file: str = typer.Argument(..., help="File path to trace"),
    repo: Path = typer.Option(Path("."), "--repo", "-r", help="Repository root path"),
    depth: int = typer.Option(100, "--depth", "-d", help="Max commits"),
    model: str = typer.Option("gpt-4o", "--model", "-m", help="OpenAI model"),
    api_key: Optional[str] = typer.Option(None, "--api-key", envvar="OPENAI_API_KEY"),
):
    """
    Show an AI-narrated timeline of a file's full evolution arc.
    """
    analyzer = _make_analyzer(repo, model, api_key)

    with console.status(f"[bold yellow]Building timeline for [cyan]{file}[/cyan]...[/bold yellow]"):
        try:
            result = analyzer.analyze(file, depth=depth)
        except Exception as e:
            err_console.print(f"[red]Failed:[/red] {e}")
            raise typer.Exit(1)

    formatter = RichFormatter(console)
    console.rule("[bold]File Evolution Timeline[/bold]")
    console.print(f"\n[bold]{result.timeline_summary}[/bold]\n")
    formatter.render(result, format="rich")


@app.callback(invoke_without_command=True)
def version_callback(
    version: bool = typer.Option(False, "--version", "-v", is_eager=True, help="Show version"),
):
    if version:
        from . import __version__
        console.print(f"git-archaeologist {__version__}")
        raise typer.Exit()


def main() -> None:
    app()


if __name__ == "__main__":
    main()
