import re
from pathlib import Path
from typing import Optional

from .git_history import GitHistoryExtractor
from .llm_client import LLMClient
from .models import ArchaeologyResult, CodeTarget


def parse_target(target_str: str) -> CodeTarget:
    """Parse 'path/file.py', 'path/file.py:42', or 'path/file.py:10-50'."""
    match = re.match(r"^(.+?)(?::(\d+)(?:-(\d+))?)?$", target_str)
    if not match:
        return CodeTarget(file_path=target_str)

    file_path = match.group(1)
    line_start: Optional[int] = int(match.group(2)) if match.group(2) else None
    line_end: Optional[int] = int(match.group(3)) if match.group(3) else line_start

    return CodeTarget(file_path=file_path, line_start=line_start, line_end=line_end)


class CodeAnalyzer:
    def __init__(
        self,
        repo_path: Path = Path("."),
        model: str = "gpt-4o",
        api_key: Optional[str] = None,
    ):
        self.extractor = GitHistoryExtractor(repo_path)
        self.llm = LLMClient(model=model, api_key=api_key)

    def analyze(self, target_str: str, depth: int = 50) -> ArchaeologyResult:
        target = parse_target(target_str)

        commits = self.extractor.get_commits_for_target(target, depth=depth)
        current_content = self.extractor.get_current_content(target)
        contributors = self.extractor.get_contributors(target.file_path)

        if not commits:
            return ArchaeologyResult(
                target=target,
                commits=[],
                narrative="No git history found for this target.",
                timeline_summary="No history available.",
                key_decisions=[],
                contributors=contributors,
            )

        narrative, timeline, decisions = self.llm.generate_narrative(
            target=target,
            commits=commits,
            current_content=current_content,
        )

        return ArchaeologyResult(
            target=target,
            commits=commits,
            narrative=narrative,
            timeline_summary=timeline,
            key_decisions=decisions,
            contributors=contributors,
            first_introduced=commits[-1].date if commits else None,
            last_modified=commits[0].date if commits else None,
            total_changes=len(commits),
        )
