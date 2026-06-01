from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Commit:
    sha: str
    author: str
    date: datetime
    message: str
    diff: str
    files_changed: list[str]
    pr_number: Optional[int] = None
    pr_title: Optional[str] = None
    pr_body: Optional[str] = None
    issue_numbers: list[int] = field(default_factory=list)


@dataclass
class CodeTarget:
    file_path: str
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    symbol_name: Optional[str] = None


@dataclass
class ArchaeologyResult:
    target: CodeTarget
    commits: list[Commit]
    narrative: str
    timeline_summary: str
    key_decisions: list[str]
    contributors: list[str]
    first_introduced: Optional[datetime] = None
    last_modified: Optional[datetime] = None
    total_changes: int = 0
