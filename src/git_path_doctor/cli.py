from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence

from . import __version__
from .analyze import analyze_path, scan_repository
from .git import GitError, GitRepository
from .models import Finding, PathReport, ScanReport


EXIT_OK = 0
EXIT_USAGE = 2
EXIT_GIT_ERROR = 3
EXIT_FINDING = 10


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="git-path-doctor",
        description="Explain why paths are tracked, ignored, hidden, or behaving strangely in Git.",
    )
    parser.add_argument("--repo", default=".", help="Repository or a path inside it (default: current directory).")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    explain = subparsers.add_parser("explain", help="Explain Git's state for one or more paths.")
    explain.add_argument("paths", nargs="+", help="Repository-relative paths to explain.")
    explain.add_argument("--json", action="store_true", help="Emit a stable JSON report.")

    scan = subparsers.add_parser("scan", help="Find hidden index flags, conflicts, and case collisions.")
    scan.add_argument("--json", action="store_true", help="Emit a stable JSON report.")
    scan.add_argument(
        "--fail-on",
        choices=("never", "warning", "error"),
        default="never",
        help="Return exit code 10 at or above this severity (default: never).",
    )
    return parser


def _finding_label(finding: Finding) -> str:
    return {"error": "ERROR", "warning": "WARN", "info": "INFO"}.get(
        finding.severity, finding.severity.upper()
    )


def _print_finding(finding: Finding, *, indent: str = "  ") -> None:
    print(f"{indent}[{_finding_label(finding)}] {finding.message}")
    if finding.evidence:
        print(f"{indent}  Evidence: {finding.evidence}")
    if finding.suggestion:
        print(f"{indent}  Next: {finding.suggestion}")


def _print_path_report(report: PathReport) -> None:
    print(f"Path:  {report.path}")
    print(f"State: {report.state}")
    print(f"Why:   {report.summary}")
    print(f"Disk:  {report.filesystem_kind}")
    if report.tracked_entries:
        modes = sorted({entry.mode for entry in report.tracked_entries if entry.mode})
        print(f"Index: {len(report.tracked_entries)} entr{'y' if len(report.tracked_entries) == 1 else 'ies'}", end="")
        if modes:
            print(f" (mode {', '.join(modes)})")
        else:
            print()
    else:
        print("Index: not tracked")
    if report.ignore_match:
        location = report.ignore_match.source
        if report.ignore_match.line is not None:
            location += f":{report.ignore_match.line}"
        print(f"Ignore: {location} -> {report.ignore_match.pattern}")
    if report.attributes:
        values = ", ".join(f"{name}={state}" for name, state in sorted(report.attributes.items()))
        print(f"Attrs: {values}")
    if report.latest_commit:
        commit = report.latest_commit
        print(f"Last:  {commit.short_id} {commit.subject} ({commit.author}, {commit.authored_at})")
    if report.findings:
        print("Findings:")
        for finding in report.findings:
            _print_finding(finding)


def _print_scan_report(report: ScanReport) -> None:
    print("Git Path Doctor scan")
    print(f"Repository:       {report.repository}")
    print(f"Tracked paths:    {report.tracked_paths}")
    print(f"Sparse checkout:  {'enabled' if report.sparse_checkout else 'disabled'}")
    print(f"Assume-unchanged: {len(report.assume_unchanged)}")
    print(f"Skip-worktree:    {len(report.skip_worktree)}")
    print(f"Conflicts:        {len(report.conflicts)}")
    print(f"Case collisions:  {len(report.case_collisions)}")
    print("Findings:")
    for finding in report.findings:
        _print_finding(finding)
    detail_groups = (
        ("Assume-unchanged paths", report.assume_unchanged),
        ("Skip-worktree paths", report.skip_worktree),
        ("Unresolved paths", report.conflicts),
    )
    for title, paths in detail_groups:
        if paths:
            print(f"{title}:")
            for path in paths:
                print(f"  - {path}")
    if report.case_collisions:
        print("Case collision groups:")
        for group in report.case_collisions:
            print("  - " + " | ".join(group))


def _should_fail(report: ScanReport, threshold: str) -> bool:
    if threshold == "never":
        return False
    ranks = {"info": 0, "warning": 1, "error": 2}
    wanted = ranks[threshold]
    return any(ranks.get(finding.severity, 0) >= wanted for finding in report.findings)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        repository = GitRepository.discover(args.repo)
        if args.command == "explain":
            reports = [analyze_path(repository, path) for path in args.paths]
            if args.json:
                print(
                    json.dumps(
                        {
                            "tool": "git-path-doctor",
                            "version": __version__,
                            "repository": str(repository.root),
                            "paths": [report.to_dict() for report in reports],
                        },
                        indent=2,
                        ensure_ascii=False,
                    )
                )
            else:
                for index, report in enumerate(reports):
                    if index:
                        print()
                    _print_path_report(report)
            return EXIT_OK
        if args.command == "scan":
            report = scan_repository(repository)
            if args.json:
                payload = report.to_dict()
                payload.update({"tool": "git-path-doctor", "version": __version__})
                print(json.dumps(payload, indent=2, ensure_ascii=False))
            else:
                _print_scan_report(report)
            return EXIT_FINDING if _should_fail(report, args.fail_on) else EXIT_OK
    except GitError as exc:
        print(f"git-path-doctor: {exc}", file=sys.stderr)
        return EXIT_GIT_ERROR
    return EXIT_USAGE


if __name__ == "__main__":
    raise SystemExit(main())
