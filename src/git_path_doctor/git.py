from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


class GitError(RuntimeError):
    """Raised when Git cannot provide evidence for a report."""

    def __init__(self, message: str, *, returncode: int | None = None) -> None:
        super().__init__(message)
        self.returncode = returncode


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: bytes
    stderr: bytes

    @property
    def stderr_text(self) -> str:
        return self.stderr.decode("utf-8", "replace").strip()


class GitRepository:
    """A small, read-only wrapper around the Git CLI."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    @classmethod
    def discover(cls, start: str | os.PathLike[str] = ".") -> "GitRepository":
        candidate = Path(start).expanduser().resolve()
        if candidate.is_file():
            candidate = candidate.parent
        result = cls._invoke(candidate, ("rev-parse", "--show-toplevel"))
        if result.returncode != 0:
            detail = result.stderr_text or "not inside a Git working tree"
            raise GitError(f"Could not find a Git repository from {candidate}: {detail}")
        root_text = result.stdout.decode("utf-8", "surrogateescape").strip()
        if not root_text:
            raise GitError("Git returned an empty repository root")
        return cls(Path(root_text))

    @staticmethod
    def _invoke(cwd: Path, args: Sequence[str], stdin: bytes | None = None) -> CommandResult:
        try:
            completed = subprocess.run(
                ["git", "-C", os.fspath(cwd), *args],
                input=stdin,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
        except FileNotFoundError as exc:
            raise GitError("Git is not installed or is not available on PATH") from exc
        except OSError as exc:
            raise GitError(f"Could not start Git: {exc}") from exc
        return CommandResult(completed.returncode, completed.stdout, completed.stderr)

    def run(
        self,
        *args: str,
        stdin: bytes | None = None,
        allowed_returncodes: tuple[int, ...] = (0,),
    ) -> CommandResult:
        result = self._invoke(self.root, args, stdin)
        if result.returncode not in allowed_returncodes:
            command = "git " + " ".join(args)
            detail = result.stderr_text or f"exit code {result.returncode}"
            raise GitError(f"{command} failed: {detail}", returncode=result.returncode)
        return result

    def relative_path(self, raw_path: str | os.PathLike[str]) -> tuple[Path, str]:
        path = Path(raw_path).expanduser()
        candidate = path if path.is_absolute() else self.root / path
        # Normalize '.', '..', and relative input without dereferencing the final
        # symlink. Git tracks the link path itself, even when its target is outside
        # the working tree.
        absolute = Path(os.path.abspath(candidate))
        try:
            relative = absolute.relative_to(self.root)
        except ValueError as exc:
            raise GitError(f"Path is outside the repository: {absolute}") from exc
        relative_text = relative.as_posix()
        return absolute, relative_text or "."
