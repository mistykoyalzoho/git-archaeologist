import os
from typing import Optional

try:
    from openai import OpenAI
    _OPENAI_AVAILABLE = True
except ImportError:
    _OPENAI_AVAILABLE = False

from .models import Commit, CodeTarget


SYSTEM_PROMPT = """\
You are an expert software historian and code archaeologist. Your job is to analyze
git history and explain WHY code exists — the decisions, incidents, constraints, and
context that shaped it — not just WHAT it does. Be concrete, reference specific commits
and dates, and surface non-obvious insights. Write like a senior engineer explaining
to a new team member.
"""


class LLMClient:
    def __init__(self, model: str = "gpt-4o", api_key: Optional[str] = None):
        if not _OPENAI_AVAILABLE:
            raise ImportError("openai package not installed. Run: pip install openai")
        self.model = model
        self.client = OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))

    def generate_narrative(
        self,
        target: CodeTarget,
        commits: list[Commit],
        current_content: str,
    ) -> tuple[str, str, list[str]]:
        """Returns (narrative, timeline_summary, key_decisions)."""
        commit_context = self._format_commits(commits)
        location = f"{target.file_path}"
        if target.line_start:
            location += f":{target.line_start}-{target.line_end}"

        prompt = f"""
Analyze the history of this code location: `{location}`

CURRENT CODE:
```
{current_content[:2000]}
```

GIT HISTORY ({len(commits)} commits):
{commit_context}

Provide:

1. **NARRATIVE** (3-5 paragraphs): Why does this code exist? What problem was it solving?
   What decisions shaped it? Reference specific commits, PRs, and dates.

2. **TIMELINE SUMMARY** (2-3 sentences): A crisp summary of the code's evolution arc.

3. **KEY DECISIONS** (bullet list, 3-7 items): The most important architectural or
   design decisions made, with brief justifications from the history.

Format your response exactly as:
NARRATIVE:
<narrative text>

TIMELINE:
<timeline text>

KEY DECISIONS:
- <decision 1>
- <decision 2>
...
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=2000,
        )

        return self._parse_response(response.choices[0].message.content or "")

    def _format_commits(self, commits: list[Commit]) -> str:
        parts = []
        for c in commits[:30]:
            pr_info = f" [PR #{c.pr_number}]" if c.pr_number else ""
            issues = f" fixes: {', '.join(f'#{i}' for i in c.issue_numbers)}" if c.issue_numbers else ""
            parts.append(
                f"[{c.sha}] {c.date.strftime('%Y-%m-%d')} {c.author}{pr_info}{issues}\n"
                f"  {c.message[:200]}\n"
                f"  Files: {', '.join(c.files_changed[:5])}"
            )
        return "\n\n".join(parts)

    def _parse_response(self, text: str) -> tuple[str, str, list[str]]:
        narrative = ""
        timeline = ""
        decisions: list[str] = []

        sections = text.split("\n\n")
        current = None
        buf: list[str] = []

        for line in text.splitlines():
            if line.startswith("NARRATIVE:"):
                current = "narrative"
                buf = []
            elif line.startswith("TIMELINE:"):
                if current == "narrative":
                    narrative = "\n".join(buf).strip()
                current = "timeline"
                buf = []
            elif line.startswith("KEY DECISIONS:"):
                if current == "timeline":
                    timeline = "\n".join(buf).strip()
                current = "decisions"
                buf = []
            elif current == "decisions" and line.startswith("- "):
                decisions.append(line[2:].strip())
            elif current:
                buf.append(line)

        if current == "timeline" and not timeline:
            timeline = "\n".join(buf).strip()
        elif current == "narrative" and not narrative:
            narrative = "\n".join(buf).strip()

        if not narrative:
            narrative = text

        return narrative, timeline, decisions
