from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from git_archaeologist.analyzer import CodeAnalyzer
from git_archaeologist.models import ArchaeologyResult, CodeTarget, Commit


def make_commit(sha="abc123", author="Alice", days_ago=10, message="feat: add thing"):
    return Commit(
        sha=sha,
        author=author,
        date=datetime(2024, 1, 1, tzinfo=timezone.utc),
        message=message,
        diff="+ def foo(): pass",
        files_changed=["src/auth.py"],
    )


def test_analyze_no_history(tmp_path):
    analyzer = CodeAnalyzer(repo_path=tmp_path)
    with (
        patch.object(analyzer.extractor, "get_commits_for_target", return_value=[]),
        patch.object(analyzer.extractor, "get_current_content", return_value=""),
        patch.object(analyzer.extractor, "get_contributors", return_value=[]),
    ):
        result = analyzer.analyze("src/auth.py")

    assert isinstance(result, ArchaeologyResult)
    assert result.total_changes == 0
    assert "No git history" in result.narrative


def test_analyze_with_history(tmp_path):
    analyzer = CodeAnalyzer(repo_path=tmp_path)
    commits = [make_commit("aaa"), make_commit("bbb", days_ago=20)]

    mock_llm = MagicMock()
    mock_llm.generate_narrative.return_value = (
        "This code was introduced to handle auth.",
        "Evolved from simple to complex over 2 years.",
        ["Chose HMAC over MD5 for security"],
    )
    analyzer.llm = mock_llm

    with (
        patch.object(analyzer.extractor, "get_commits_for_target", return_value=commits),
        patch.object(analyzer.extractor, "get_current_content", return_value="def verify(): pass"),
        patch.object(analyzer.extractor, "get_contributors", return_value=["Alice"]),
    ):
        result = analyzer.analyze("src/auth.py")

    assert result.total_changes == 2
    assert result.narrative == "This code was introduced to handle auth."
    assert "Chose HMAC" in result.key_decisions[0]
    assert result.contributors == ["Alice"]


def test_llm_parse_response_well_formed():
    from git_archaeologist.llm_client import LLMClient
    client = MagicMock(spec=LLMClient)
    client._parse_response = LLMClient._parse_response.__get__(client)

    response = """NARRATIVE:
This function was introduced in 2021 to fix a critical auth bug.
It replaced a weaker MD5-based implementation.

TIMELINE:
Simple auth in 2020, major rewrite in 2021 after CVE, stable since.

KEY DECISIONS:
- Switched from MD5 to HMAC-SHA256 after CVE-2021-1234
- Added rate limiting after brute-force incidents
"""
    narrative, timeline, decisions = client._parse_response(response)
    assert "HMAC" in narrative
    assert "CVE" in timeline
    assert len(decisions) == 2
    assert "HMAC-SHA256" in decisions[0]
