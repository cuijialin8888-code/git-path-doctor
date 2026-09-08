from __future__ import annotations

import re
import unittest
from pathlib import Path

from git_path_doctor import __version__


ROOT = Path(__file__).resolve().parents[1]


class RepositoryQualityTests(unittest.TestCase):
    def test_release_version_is_synchronized(self) -> None:
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn(f'version = "{__version__}"', pyproject)
        self.assertIn(f"## [{__version__}]", changelog)
        self.assertIn(f"@v{__version__}", readme)

    def test_local_markdown_links_exist(self) -> None:
        markdown_link = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
        html_link = re.compile(r'(?:href|src)="([^"]+)"')
        missing: list[str] = []

        for document in ROOT.rglob("*.md"):
            text = document.read_text(encoding="utf-8")
            targets = markdown_link.findall(text) + html_link.findall(text)
            for target in targets:
                target = target.strip().strip("<>").split("#", 1)[0]
                if not target or "://" in target or target.startswith(("mailto:", "#")):
                    continue
                if not (document.parent / target).resolve().exists():
                    missing.append(f"{document.relative_to(ROOT)} -> {target}")

        self.assertEqual([], missing)

    def test_workflow_actions_are_immutably_pinned(self) -> None:
        workflows = sorted((ROOT / ".github" / "workflows").glob("*.yml"))
        workflows += sorted((ROOT / ".github" / "workflows").glob("*.yaml"))
        self.assertTrue(workflows)

        unpinned: list[str] = []
        for workflow in workflows:
            for line_number, line in enumerate(workflow.read_text(encoding="utf-8").splitlines(), 1):
                match = re.search(r"uses:\s*([^\s#]+)", line)
                if not match or match.group(1).startswith("./"):
                    continue
                reference = match.group(1).rsplit("@", 1)[-1]
                if not re.fullmatch(r"[0-9a-f]{40}", reference):
                    relative = workflow.relative_to(ROOT)
                    unpinned.append(f"{relative}:{line_number} {match.group(1)}")

        self.assertEqual([], unpinned)


if __name__ == "__main__":
    raise SystemExit(unittest.main())
