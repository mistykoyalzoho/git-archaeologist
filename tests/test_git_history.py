import subprocess
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from git_archaeologist.git_history import GitHistoryExtractor
from git_archaeologist.models import CodeTarget


@pytest.fixture
def extractor(tmp_path):
    return GitHistoryExtractor(tmp_path)


def test_parse_target_file_only():
    from git_archaeologist.analyzer import parse_target
    t = parse_target("src/auth.py")
    assert t.file_path == "src/auth.py"
    assert t.line_start is None
    assert t.line_end is None


def test_parse_target_single_line():
    from git_archaeologist.analyzer import parse_target
    t = parse_target("src/auth.py:42")
    assert t.file_path == "src/auth.py"
    assert t.line_start == 42
    assert t.line_end == 42


def test_parse_target_line_range():
    from git_archaeologist.analyzer import parse_target
    t = parse_target("src/auth.py:10-80")
    assert t.file_path == "src/auth.py"
    assert t.line_start == 10
    assert t.line_end == 80


def test_extract_pr_info(extractor):
    subject = "Merge pull request #123 from feature/auth"
    pr_num, pr_title, _ = extractor._extract_pr_info(subject, "")
    assert pr_num == 123


def test_extract_pr_info_parenthetical(extractor):
    subject = "Add token refresh logic (#456)"
    pr_num, _, _ = extractor._extract_pr_info(subject, "")
    assert pr_num == 456


def test_extract_issue_numbers(extractor):
    text = "Fix null pointer exception, closes #789 and fixes #101"
    issues = extractor._extract_issue_numbers(text)
    assert 789 in issues
    assert 101 in issues


def test_extract_issue_numbers_empty(extractor):
    issues = extractor._extract_issue_numbers("No issues here")
    assert issues == []


def test_get_commits_empty_repo(extractor):
    with patch.object(extractor, "_run", return_value=""):
        target = CodeTarget(file_path="src/nonexistent.py")
        commits = extractor.get_commits_for_target(target)
        assert commits == []


def test_get_contributors(extractor):
    with patch.object(extractor, "_run", return_value="Alice\nBob\nAlice\nAlice"):
        contributors = extractor.get_contributors("src/auth.py")
        assert contributors[0] == "Alice"
        assert "Bob" in contributors


def test_get_current_content_missing_file(extractor):
    target = CodeTarget(file_path="does/not/exist.py")
    assert extractor.get_current_content(target) == ""


def test_get_current_content_line_range(tmp_path):
    f = tmp_path / "example.py"
    f.write_text("\n".join(f"line {i}" for i in range(1, 21)))
    extractor = GitHistoryExtractor(tmp_path)
    target = CodeTarget(file_path="example.py", line_start=5, line_end=10)
    content = extractor.get_current_content(target)
    assert "line 5" in content
    assert "line 10" in content
    assert "line 11" not in content
