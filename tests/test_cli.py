from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
import json
from pathlib import Path
import subprocess

from git_path_doctor.cli import EXIT_GIT_ERROR, main


class CliErrorTests(unittest.TestCase):
    def test_explain_gate_is_opt_in_and_preserves_json(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            (root / "hidden.txt").write_text("data", encoding="utf-8")
            subprocess.run(["git", "add", "hidden.txt"], cwd=root, check=True)
            subprocess.run(["git", "-c", "user.name=Tests", "-c", "user.email=tests@example.invalid", "commit", "-qm", "fixture"], cwd=root, check=True)
            subprocess.run(["git", "update-index", "--assume-unchanged", "hidden.txt"], cwd=root, check=True)
            args = ["--repo", str(root), "explain", "hidden.txt", "--format", "json"]
            before = (root / ".git" / "index").read_bytes()
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(args), 0)
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                self.assertEqual(main([*args, "--fail-on", "warning"]), 10)
            json.loads(stdout.getvalue())
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main([*args, "--fail-on", "error"]), 0)
            self.assertEqual((root / ".git" / "index").read_bytes(), before)

    def test_non_repository_is_a_clean_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = main(["--repo", temporary, "scan"])
        self.assertEqual(code, EXIT_GIT_ERROR)
        self.assertIn("Could not find a Git repository", stderr.getvalue())

    def test_outside_path_is_a_clean_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = main(["--repo", str(root), "explain", str(root.parent)])
        self.assertEqual(code, EXIT_GIT_ERROR)
        self.assertIn("outside the repository", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
