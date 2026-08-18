from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path
import subprocess

from git_path_doctor.cli import EXIT_GIT_ERROR, main


class CliErrorTests(unittest.TestCase):
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
