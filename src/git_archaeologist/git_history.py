import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import Commit, CodeTarget


class GitHistoryExtractor:
    def __init__(self, repo_path: Path):
        self.repo_path = Path(repo_path).resolve()

    def _run(self, *args: str, check: bool = True) -> str:
        result = subprocess.run(
            ["git", *args],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=check,
        )
        return result.stdout.strip()

    def get_commits_for_target(self, target: CodeTarget, depth: int = 50) -> list[Commit]:
        """Fetch commits that touched the target file/lines."""
        log_args = [
            "log",
            f"-{depth}",
            "--pretty=format:%H||%an||%ad||%s||%b",
            "--date=iso-strict",
            "--follow",
        ]

        if target.line_start and target.line_end:
            log_args += [f"-L{target.line_start},{target.line_end}:{target.file_path}"]
        else:
            log_args += ["--", target.file_path]

        raw = self._run(*log_args, check=False)
        if not raw:
            return []

        commits = []
        for line in raw.splitlines():
            parts = line.split("||", 4)
            if len(parts) < 4:
                continue
            sha, author, date_str, subject = parts[0], parts[1], parts[2], parts[3]
            body = parts[4] if len(parts) > 4 else ""

            try:
                date = datetime.fromisoformat(date_str)
            except ValueError:
                continue

            diff = self._get_diff_for_file(sha, target.file_path)
            files = self._get_files_changed(sha)
            pr_number, pr_title, pr_body = self._extract_pr_info(subject, body)
            issue_numbers = self._extract_issue_numbers(subject + " " + body)

            commits.append(
                Commit(
                    sha=sha[:12],
                    author=author,
                    date=date,
                    message=f"{subject}\n{body}".strip(),
                    diff=diff[:4000],
                    files_changed=files,
                    pr_number=pr_number,
                    pr_title=pr_title,
                    pr_body=pr_body[:1000] if pr_body else None,
                    issue_numbers=issue_numbers,
                )
            )

        return commits

    def _get_diff_for_file(self, sha: str, file_path: str) -> str:
        return self._run("show", "--stat", "-p", sha, "--", file_path, check=False)

    def _get_files_changed(self, sha: str) -> list[str]:
        raw = self._run("diff-tree", "--no-commit-id", "-r", "--name-only", sha, check=False)
        return raw.splitlines()

    def _extract_pr_info(
        self, subject: str, body: str
    ) -> tuple[Optional[int], Optional[str], Optional[str]]:
        pr_match = re.search(r"\(#(\d+)\)|\bPR[- ]#?(\d+)\b|Merge pull request #(\d+)", subject + body)
        if pr_match:
            num = int(next(g for g in pr_match.groups() if g))
            return num, subject, body
        return None, None, None

    def _extract_issue_numbers(self, text: str) -> list[int]:
        matches = re.findall(r"(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#(\d+)", text, re.IGNORECASE)
        refs = re.findall(r"#(\d+)", text)
        return list({int(n) for n in matches + refs})

    def get_current_content(self, target: CodeTarget) -> str:
        file_path = self.repo_path / target.file_path
        if not file_path.exists():
            return ""
        text = file_path.read_text(errors="replace")
        if target.line_start and target.line_end:
            lines = text.splitlines()
            return "\n".join(lines[target.line_start - 1 : target.line_end])
        return text[:3000]

    def get_contributors(self, file_path: str) -> list[str]:
        raw = self._run("log", "--follow", "--pretty=%an", "--", file_path, check=False)
        seen: dict[str, int] = {}
        for name in raw.splitlines():
            seen[name] = seen.get(name, 0) + 1
        return sorted(seen, key=lambda n: -seen[n])
