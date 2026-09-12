# Changelog

All notable changes to this project are documented here.

## [Unreleased]

### Added

- A path debugging workflow separating single-path explanation from repository-wide hidden-state scanning.

## [0.1.0] - 2026-08-18

### Added

- `explain` reports for tracked, modified, staged, ignored, sparse, conflicting, untracked, and missing paths.
- Evidence for ignore provenance, Git attributes, index modes/stages, hidden index flags, and latest path history.
- Repository-wide `scan` for assume-unchanged, skip-worktree, unresolved stages, and case collisions.
- Human-readable and JSON output.
- Configurable CI exit threshold for repository scans.
- Cross-platform integration tests using disposable Git repositories.

[0.1.0]: https://github.com/cuijialin8888-code/git-path-doctor/releases/tag/v0.1.0
