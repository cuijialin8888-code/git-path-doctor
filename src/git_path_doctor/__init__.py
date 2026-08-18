"""Git Path Doctor public package interface."""

from .analyze import analyze_path, scan_repository
from .git import GitError, GitRepository

__all__ = ["GitError", "GitRepository", "analyze_path", "scan_repository"]
__version__ = "0.1.0"
