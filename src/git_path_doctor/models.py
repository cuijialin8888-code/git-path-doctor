from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class IgnoreMatch:
    source: str
    line: int | None
    pattern: str
    path: str


@dataclass(frozen=True)
class StatusEntry:
    record_type: str
    path: str
    index_status: str = "."
    worktree_status: str = "."
    original_path: str | None = None


@dataclass(frozen=True)
class IndexEntry:
    path: str
    marker: str
    mode: str | None = None
    object_id: str | None = None
    stage: int = 0
    assume_unchanged: bool = False
    skip_worktree: bool = False


@dataclass(frozen=True)
class CommitInfo:
    short_id: str
    authored_at: str
    author: str
    subject: str


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    message: str
    evidence: str | None = None
    suggestion: str | None = None


@dataclass
class PathReport:
    input_path: str
    path: str
    absolute_path: str
    state: str
    summary: str
    exists: bool
    filesystem_kind: str
    tracked_entries: list[IndexEntry] = field(default_factory=list)
    status: list[StatusEntry] = field(default_factory=list)
    ignore_match: IgnoreMatch | None = None
    attributes: dict[str, str] = field(default_factory=dict)
    latest_commit: CommitInfo | None = None
    sparse_checkout: bool = False
    findings: list[Finding] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

@dataclass
class ScanReport:
    repository: str
    tracked_paths: int
    sparse_checkout: bool
    assume_unchanged: list[str]
    skip_worktree: list[str]
    conflicts: list[str]
    case_collisions: list[list[str]]
    findings: list[Finding]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
