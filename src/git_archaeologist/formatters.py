import json
from datetime import datetime

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich import box

from .models import ArchaeologyResult


class RichFormatter:
    def __init__(self, console: Console):
        self.console = console

    def render(self, result: ArchaeologyResult, format: str = "rich") -> None:
        if format == "json":
            self._render_json(result)
        elif format == "markdown":
            self._render_markdown(result)
        else:
            self._render_rich(result)

    def _render_rich(self, result: ArchaeologyResult) -> None:
        c = self.console
        target = result.target
        location = target.file_path
        if target.line_start:
            location += f":{target.line_start}"
            if target.line_end and target.line_end != target.line_start:
                location += f"-{target.line_end}"

        c.print()
        c.print(
            Panel(
                f"[bold cyan]{location}[/bold cyan]",
                title="[bold yellow]git-archaeologist[/bold yellow]",
                subtitle=f"{result.total_changes} commits analyzed",
                border_style="yellow",
            )
        )

        if result.timeline_summary:
            c.print()
            c.print(Rule("[bold]Timeline[/bold]", style="dim"))
            c.print(f"  [dim]{result.timeline_summary}[/dim]")

        if result.narrative:
            c.print()
            c.print(Rule("[bold]Historical Narrative[/bold]", style="blue"))
            c.print(Markdown(result.narrative))

        if result.key_decisions:
            c.print()
            c.print(Rule("[bold]Key Decisions[/bold]", style="green"))
            for decision in result.key_decisions:
                c.print(f"  [green]▸[/green] {decision}")

        if result.contributors:
            c.print()
            c.print(Rule("[bold]Contributors[/bold]", style="dim"))
            c.print(f"  {', '.join(result.contributors[:8])}")

        if result.first_introduced or result.last_modified:
            c.print()
            table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
            table.add_column(style="dim")
            table.add_column()
            if result.first_introduced:
                table.add_row("First introduced", result.first_introduced.strftime("%Y-%m-%d"))
            if result.last_modified:
                table.add_row("Last modified", result.last_modified.strftime("%Y-%m-%d"))
            table.add_row("Total commits", str(result.total_changes))
            c.print(table)

        c.print()

    def _render_markdown(self, result: ArchaeologyResult) -> None:
        target = result.target
        location = target.file_path
        if target.line_start:
            location += f":{target.line_start}"

        lines = [
            f"# Code Archaeology: `{location}`",
            "",
            f"**{result.total_changes} commits analyzed** · "
            f"First introduced: {result.first_introduced.strftime('%Y-%m-%d') if result.first_introduced else 'unknown'} · "
            f"Last modified: {result.last_modified.strftime('%Y-%m-%d') if result.last_modified else 'unknown'}",
            "",
            "## Timeline",
            "",
            result.timeline_summary or "_No timeline available._",
            "",
            "## Historical Narrative",
            "",
            result.narrative or "_No narrative available._",
            "",
        ]

        if result.key_decisions:
            lines += ["## Key Decisions", ""]
            for d in result.key_decisions:
                lines.append(f"- {d}")
            lines.append("")

        if result.contributors:
            lines += ["## Contributors", "", ", ".join(result.contributors[:8]), ""]

        self.console.print("\n".join(lines))

    def _render_json(self, result: ArchaeologyResult) -> None:
        data = {
            "target": {
                "file": result.target.file_path,
                "line_start": result.target.line_start,
                "line_end": result.target.line_end,
            },
            "narrative": result.narrative,
            "timeline_summary": result.timeline_summary,
            "key_decisions": result.key_decisions,
            "contributors": result.contributors,
            "stats": {
                "total_commits": result.total_changes,
                "first_introduced": result.first_introduced.isoformat() if result.first_introduced else None,
                "last_modified": result.last_modified.isoformat() if result.last_modified else None,
            },
            "commits": [
                {
                    "sha": c.sha,
                    "author": c.author,
                    "date": c.date.isoformat(),
                    "message": c.message,
                    "pr_number": c.pr_number,
                    "issue_numbers": c.issue_numbers,
                }
                for c in result.commits
            ],
        }
        self.console.print(json.dumps(data, indent=2))
