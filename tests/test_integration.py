from __future__ import annotations

import contextlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from git_path_doctor.analyze import _case_collisions, analyze_path, scan_repository
from git_path_doctor.cli import EXIT_OK, main
from git_path_doctor.git import GitError, GitRepository


class GitFixture:
    def __init__(self) -> None:
        self._temporary = tempfile.TemporaryDirectory()
        self.root = Path(self._temporary.name)
        self.git("init", "-q")
        self.git("config", "user.name", "Test User")
        self.git("config", "user.email", "test@example.invalid")

    def close(self) -> None:
        self._temporary.cleanup()

    def git(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args],
            cwd=self.root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )

    def write(self, relative: str, content: str) -> Path:
        target = self.root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return target

    def commit_all(self, message: str = "fixture") -> None:
        self.git("add", "-A")
        self.git("commit", "-q", "-m", message)


class PathAnalysisTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = GitFixture()
        self.repository = GitRepository.discover(self.fixture.root)

    def tearDown(self) -> None:
        self.fixture.close()

    def test_ignored_path_reports_rule_and_line(self) -> None:
        self.fixture.write(".gitignore", "*.log\n")
        self.fixture.commit_all()
        self.fixture.write("debug.log", "not tracked\n")

        report = analyze_path(self.repository, "debug.log")

        self.assertEqual(report.state, "IGNORED")
        self.assertIsNotNone(report.ignore_match)
        assert report.ignore_match is not None
        self.assertEqual(report.ignore_match.pattern, "*.log")
        self.assertEqual(report.ignore_match.line, 1)
        self.assertIn("IGNORE_RULE", {finding.code for finding in report.findings})

    def test_tracked_file_can_still_match_ignore_rule(self) -> None:
        self.fixture.write(".gitignore", "*.env\n")
        self.fixture.write("sample.env", "SAFE_PLACEHOLDER=1\n")
        self.fixture.git("add", ".gitignore")
        self.fixture.git("add", "-f", "sample.env")
        self.fixture.git("commit", "-q", "-m", "tracked ignored fixture")

        report = analyze_path(self.repository, "sample.env")

        self.assertEqual(report.state, "TRACKED")
        self.assertIn("TRACKED_DESPITE_IGNORE", {finding.code for finding in report.findings})

    def test_negated_ignore_rule_reincludes_path(self) -> None:
        self.fixture.write(".gitignore", "*.log\n!keep.log\n")
        self.fixture.commit_all()
        self.fixture.write("keep.log", "visible to Git\n")

        report = analyze_path(self.repository, "keep.log")

        self.assertEqual(report.state, "UNTRACKED")
        self.assertIsNotNone(report.ignore_match)
        assert report.ignore_match is not None
        self.assertEqual(report.ignore_match.pattern, "!keep.log")
        self.assertIn("NEGATED_IGNORE_RULE", {finding.code for finding in report.findings})

    def test_literal_pathspec_characters_are_not_treated_as_patterns(self) -> None:
        self.fixture.write("name[1].txt", "literal\n")
        self.fixture.commit_all()

        report = analyze_path(self.repository, "name[1].txt")

        self.assertEqual(report.state, "TRACKED")
        self.assertEqual({entry.path for entry in report.tracked_entries}, {"name[1].txt"})

    def test_modified_then_staged_state(self) -> None:
        self.fixture.write("notes.txt", "one\n")
        self.fixture.commit_all()
        self.fixture.write("notes.txt", "two\n")

        modified = analyze_path(self.repository, "notes.txt")
        self.assertEqual(modified.state, "MODIFIED")

        self.fixture.git("add", "notes.txt")
        staged = analyze_path(self.repository, "notes.txt")
        self.assertEqual(staged.state, "STAGED")

    def test_assume_unchanged_is_visible_even_when_status_is_quiet(self) -> None:
        self.fixture.write("local.cfg", "before\n")
        self.fixture.commit_all()
        self.fixture.git("update-index", "--assume-unchanged", "local.cfg")
        self.fixture.write("local.cfg", "after\n")

        report = analyze_path(self.repository, "local.cfg")

        self.assertEqual(report.state, "TRACKED")
        self.assertIn("ASSUME_UNCHANGED", {finding.code for finding in report.findings})

    def test_missing_tracked_file_has_safe_next_step(self) -> None:
        target = self.fixture.write("tracked.txt", "content\n")
        self.fixture.commit_all()
        target.unlink()

        report = analyze_path(self.repository, "tracked.txt")

        self.assertEqual(report.state, "TRACKED_MISSING")
        finding = next(item for item in report.findings if item.code == "MISSING_TRACKED_FILE")
        self.assertIn("git restore", finding.suggestion or "")

    def test_scan_finds_hidden_index_flags(self) -> None:
        self.fixture.write("assumed.txt", "a\n")
        self.fixture.write("skipped.txt", "b\n")
        self.fixture.commit_all()
        self.fixture.git("update-index", "--assume-unchanged", "assumed.txt")
        self.fixture.git("update-index", "--skip-worktree", "skipped.txt")

        report = scan_repository(self.repository)

        self.assertEqual(report.assume_unchanged, ["assumed.txt"])
        self.assertEqual(report.skip_worktree, ["skipped.txt"])
        self.assertIn("MANUAL_SKIP_WORKTREE_PATHS", {finding.code for finding in report.findings})

    def test_rejects_path_outside_repository(self) -> None:
        outside = self.fixture.root.parent / "outside.txt"
        with self.assertRaises(GitError):
            analyze_path(self.repository, str(outside))


class ParserAndCliTests(unittest.TestCase):
    def test_case_collisions_group_only_distinct_spellings(self) -> None:
        self.assertEqual(
            _case_collisions(["src/App.py", "src/app.py", "README.md"]),
            [["src/App.py", "src/app.py"]],
        )

    def test_json_cli_has_versioned_envelope(self) -> None:
        fixture = GitFixture()
        try:
            fixture.write("tracked.txt", "content\n")
            fixture.commit_all()
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = main(["--repo", str(fixture.root), "explain", "tracked.txt", "--json"])
            payload = json.loads(output.getvalue())
            self.assertEqual(code, EXIT_OK)
            self.assertEqual(payload["tool"], "git-path-doctor")
            self.assertEqual(payload["version"], "0.1.0")
            self.assertEqual(payload["paths"][0]["state"], "TRACKED")
        finally:
            fixture.close()


if __name__ == "__main__":
    unittest.main()
