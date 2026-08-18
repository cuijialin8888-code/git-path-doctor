from __future__ import annotations

import os
from pathlib import Path

from .git import GitRepository
from .models import (
    CommitInfo,
    Finding,
    IgnoreMatch,
    IndexEntry,
    PathReport,
    ScanReport,
    StatusEntry,
)


def _decode(value: bytes) -> str:
    return value.decode("utf-8", "surrogateescape")


def _split_nul(value: bytes) -> list[str]:
    return [_decode(part) for part in value.split(b"\0") if part]


def _parse_stage_entries(value: bytes) -> dict[tuple[str, int], tuple[str, str]]:
    entries: dict[tuple[str, int], tuple[str, str]] = {}
    for record in _split_nul(value):
        metadata, separator, path = record.partition("\t")
        if not separator:
            continue
        fields = metadata.split()
        if len(fields) != 3:
            continue
        mode, object_id, stage_text = fields
        try:
            stage = int(stage_text)
        except ValueError:
            continue
        entries[(path, stage)] = (mode, object_id)
    return entries


def _parse_index_entries(verbose: bytes, staged: bytes) -> list[IndexEntry]:
    stage_data = _parse_stage_entries(staged)
    entries: list[IndexEntry] = []
    for record in _split_nul(verbose):
        if len(record) < 3 or record[1] != " ":
            continue
        marker, path = record[0], record[2:]
        matching_stages = sorted(
            (stage, data) for (entry_path, stage), data in stage_data.items() if entry_path == path
        ) or [(0, (None, None))]
        for stage, (mode, object_id) in matching_stages:
            entries.append(
                IndexEntry(
                    path=path,
                    marker=marker,
                    mode=mode,
                    object_id=object_id,
                    stage=stage,
                    assume_unchanged=marker.islower(),
                    skip_worktree=marker.upper() == "S",
                )
            )
    return entries


def _parse_status(value: bytes) -> list[StatusEntry]:
    raw = _split_nul(value)
    entries: list[StatusEntry] = []
    index = 0
    while index < len(raw):
        record = raw[index]
        record_type = record[:1]
        if record_type == "1":
            fields = record.split(" ", 8)
            if len(fields) == 9:
                xy = fields[1]
                entries.append(StatusEntry("ordinary", fields[8], xy[0], xy[1]))
        elif record_type == "2":
            fields = record.split(" ", 9)
            original = raw[index + 1] if index + 1 < len(raw) else None
            if len(fields) == 10:
                xy = fields[1]
                entries.append(StatusEntry("renamed", fields[9], xy[0], xy[1], original))
            index += 1
        elif record_type == "u":
            fields = record.split(" ", 10)
            if len(fields) == 11:
                xy = fields[1]
                entries.append(StatusEntry("unmerged", fields[10], xy[0], xy[1]))
        elif record_type == "?":
            entries.append(StatusEntry("untracked", record[2:]))
        elif record_type == "!":
            entries.append(StatusEntry("ignored", record[2:]))
        index += 1
    return entries


def _parse_ignore_match(value: bytes) -> IgnoreMatch | None:
    fields = _split_nul(value)
    if len(fields) < 4:
        return None
    source, line_text, pattern, path = fields[-4:]
    try:
        line = int(line_text)
    except ValueError:
        line = None
    return IgnoreMatch(source, line, pattern, path)


def _parse_attributes(value: bytes) -> dict[str, str]:
    fields = _split_nul(value)
    attributes: dict[str, str] = {}
    for index in range(0, len(fields) - 2, 3):
        _path, name, state = fields[index : index + 3]
        attributes[name] = state
    return attributes


def _parse_commit(value: bytes) -> CommitInfo | None:
    fields = _split_nul(value)
    if len(fields) < 4:
        return None
    return CommitInfo(fields[0], fields[1], fields[2], fields[3])


def _filesystem_kind(path: Path) -> str:
    if path.is_symlink():
        return "symlink"
    if path.is_file():
        return "file"
    if path.is_dir():
        return "directory"
    return "missing"


def _bool_config(repository: GitRepository, name: str) -> bool:
    result = repository.run("config", "--bool", "--get", name, allowed_returncodes=(0, 1, 5))
    return _decode(result.stdout).strip().lower() == "true"


def _derive_state(
    *, exists: bool, entries: list[IndexEntry], status: list[StatusEntry], ignored: bool
) -> tuple[str, str]:
    if any(item.record_type == "unmerged" for item in status) or any(item.stage > 0 for item in entries):
        return "CONFLICT", "The path has unresolved merge entries in the Git index."
    if entries:
        if not exists and not any(item.skip_worktree for item in entries):
            return "TRACKED_MISSING", "The path is tracked but missing from the working tree."
        if any(item.index_status not in (".", " ") for item in status):
            return "STAGED", "The path has changes staged in the Git index."
        if any(item.worktree_status not in (".", " ") for item in status):
            return "MODIFIED", "The tracked path has unstaged working-tree changes."
        if any(item.skip_worktree for item in entries) and not exists:
            return "SPARSE", "The tracked path is omitted from this working tree by an index flag."
        return "TRACKED", "The path is tracked and Git reports no ordinary content change."
    if ignored or any(item.record_type == "ignored" for item in status):
        return "IGNORED", "An ignore rule excludes this untracked path."
    if exists:
        return "UNTRACKED", "The path exists but is not tracked or ignored by Git."
    return "MISSING", "The path does not exist and is not tracked in the current index."


def analyze_path(repository: GitRepository, raw_path: str) -> PathReport:
    absolute, relative = repository.relative_path(raw_path)
    verbose = repository.run("--literal-pathspecs", "ls-files", "-v", "-z", "--", relative).stdout
    staged = repository.run("--literal-pathspecs", "ls-files", "--stage", "-z", "--", relative).stdout
    entries = _parse_index_entries(verbose, staged)
    status = _parse_status(
        repository.run(
            "--literal-pathspecs",
            "status",
            "--porcelain=v2",
            "-z",
            "--untracked-files=all",
            "--ignored=matching",
            "--",
            relative,
        ).stdout
    )
    ignore_result = repository.run(
        "check-ignore",
        "-v",
        "-z",
        "--stdin",
        "--no-index",
        stdin=relative.encode("utf-8", "surrogateescape") + b"\0",
        allowed_returncodes=(0, 1),
    )
    ignore_match = _parse_ignore_match(ignore_result.stdout)
    attributes = _parse_attributes(
        repository.run("--literal-pathspecs", "check-attr", "-z", "--all", "--", relative).stdout
    )
    latest_commit = _parse_commit(
        repository.run(
            "--literal-pathspecs",
            "log",
            "-1",
            "--format=%h%x00%aI%x00%an%x00%s%x00",
            "--",
            relative,
        ).stdout
    )
    exists = absolute.exists() or absolute.is_symlink()
    sparse_checkout = _bool_config(repository, "core.sparseCheckout")
    ignore_excludes = bool(ignore_match and not ignore_match.pattern.startswith("!"))
    state, summary = _derive_state(
        exists=exists, entries=entries, status=status, ignored=ignore_excludes
    )
    findings: list[Finding] = []

    if any(item.assume_unchanged for item in entries):
        findings.append(
            Finding(
                "warning",
                "ASSUME_UNCHANGED",
                "The index marks this path assume-unchanged, so working-tree edits can be hidden from normal status output.",
                "A lowercase marker was returned by git ls-files -v.",
                f"Inspect the file, then use: git update-index --no-assume-unchanged -- {relative}",
            )
        )
    if any(item.skip_worktree for item in entries):
        suggestion = (
            "Use git sparse-checkout list/set/reapply to change the sparse specification."
            if sparse_checkout
            else f"If this flag was set manually, use: git update-index --no-skip-worktree -- {relative}"
        )
        findings.append(
            Finding(
                "info" if sparse_checkout else "warning",
                "SKIP_WORKTREE",
                "The index marks this path skip-worktree.",
                "Git ls-files -v returned marker S.",
                suggestion,
            )
        )
    if ignore_match and ignore_excludes and entries:
        location = ignore_match.source
        if ignore_match.line is not None:
            location += f":{ignore_match.line}"
        findings.append(
            Finding(
                "info",
                "TRACKED_DESPITE_IGNORE",
                "An ignore rule matches this path, but ignore rules do not stop Git tracking files already in the index.",
                f"{location} matches pattern {ignore_match.pattern!r}.",
                "Keep it tracked, or review git rm --cached before changing repository state.",
            )
        )
    if state == "IGNORED" and ignore_match:
        location = ignore_match.source
        if ignore_match.line is not None:
            location += f":{ignore_match.line}"
        findings.append(
            Finding(
                "info",
                "IGNORE_RULE",
                f"The last matching ignore rule is {ignore_match.pattern!r}.",
                location,
                "Edit the rule if it is wrong, or use git add -f only when tracking the file is intentional.",
            )
        )
    if ignore_match and not ignore_excludes:
        location = ignore_match.source
        if ignore_match.line is not None:
            location += f":{ignore_match.line}"
        findings.append(
            Finding(
                "info",
                "NEGATED_IGNORE_RULE",
                f"The rule {ignore_match.pattern!r} re-includes this path.",
                location,
                "No change is needed unless the re-inclusion was accidental.",
            )
        )
    if state == "CONFLICT":
        findings.append(
            Finding(
                "error",
                "UNMERGED_INDEX",
                "Git has multiple index stages for this path.",
                "One or more stage 1/2/3 entries are present.",
                "Resolve the file, then stage the resolved content with git add.",
            )
        )
    if state == "TRACKED_MISSING":
        findings.append(
            Finding(
                "warning",
                "MISSING_TRACKED_FILE",
                "The index tracks this path but it is absent from disk.",
                "The path is in git ls-files and is not marked skip-worktree.",
                f"Restore it with git restore -- {relative}, or stage the deletion if it was intentional.",
            )
        )
    if any(item.mode == "160000" for item in entries):
        findings.append(
            Finding(
                "info",
                "GITLINK",
                "The path is a submodule entry, not a normal tracked directory.",
                "Index mode is 160000.",
                "Use git submodule status and git submodule update when diagnosing its contents.",
            )
        )
    if any(item.mode == "120000" for item in entries):
        findings.append(
            Finding(
                "info",
                "SYMLINK",
                "Git stores this path as a symbolic link.",
                "Index mode is 120000.",
                "Check core.symlinks if checkout behavior differs across platforms.",
            )
        )

    return PathReport(
        input_path=raw_path,
        path=relative,
        absolute_path=os.fspath(absolute),
        state=state,
        summary=summary,
        exists=exists,
        filesystem_kind=_filesystem_kind(absolute),
        tracked_entries=entries,
        status=status,
        ignore_match=ignore_match,
        attributes=attributes,
        latest_commit=latest_commit,
        sparse_checkout=sparse_checkout,
        findings=findings,
    )


def _case_collisions(paths: list[str]) -> list[list[str]]:
    groups: dict[str, list[str]] = {}
    for path in paths:
        groups.setdefault(path.casefold(), []).append(path)
    return [sorted(group) for group in groups.values() if len(set(group)) > 1]


def scan_repository(repository: GitRepository) -> ScanReport:
    verbose = repository.run("ls-files", "-v", "-z").stdout
    staged = repository.run("ls-files", "--stage", "-z").stdout
    entries = _parse_index_entries(verbose, staged)
    paths = sorted({entry.path for entry in entries})
    assume_unchanged = sorted({entry.path for entry in entries if entry.assume_unchanged})
    skip_worktree = sorted({entry.path for entry in entries if entry.skip_worktree})
    conflicts = sorted({entry.path for entry in entries if entry.stage > 0})
    collisions = _case_collisions(paths)
    sparse_checkout = _bool_config(repository, "core.sparseCheckout")
    findings: list[Finding] = []
    if assume_unchanged:
        findings.append(
            Finding(
                "warning",
                "ASSUME_UNCHANGED_PATHS",
                f"{len(assume_unchanged)} path(s) can hide working-tree edits from normal status output.",
                suggestion="Review each path before clearing its index flag.",
            )
        )
    if skip_worktree and not sparse_checkout:
        findings.append(
            Finding(
                "warning",
                "MANUAL_SKIP_WORKTREE_PATHS",
                f"{len(skip_worktree)} path(s) are skip-worktree while sparse checkout is disabled.",
                suggestion="Review whether these flags were set manually and are still needed.",
            )
        )
    elif skip_worktree:
        findings.append(
            Finding(
                "info",
                "SPARSE_PATHS",
                f"{len(skip_worktree)} tracked path(s) are outside the current sparse working set.",
            )
        )
    if conflicts:
        findings.append(
            Finding(
                "error",
                "UNRESOLVED_CONFLICTS",
                f"{len(conflicts)} path(s) have unresolved index stages.",
                suggestion="Resolve each conflict and stage the result.",
            )
        )
    if collisions:
        findings.append(
            Finding(
                "error",
                "CASE_COLLISIONS",
                f"{len(collisions)} case-insensitive path collision group(s) exist in the index.",
                suggestion="Rename colliding paths on a case-sensitive filesystem or via an intermediate name.",
            )
        )
    if not findings:
        findings.append(Finding("info", "NO_HIDDEN_INDEX_STATE", "No surprising index flags or conflicts were found."))
    return ScanReport(
        repository=os.fspath(repository.root),
        tracked_paths=len(paths),
        sparse_checkout=sparse_checkout,
        assume_unchanged=assume_unchanged,
        skip_worktree=skip_worktree,
        conflicts=conflicts,
        case_collisions=collisions,
        findings=findings,
    )
