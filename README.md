# Git Path Doctor

[![CI](https://github.com/cuijialin8888-code/git-path-doctor/actions/workflows/ci.yml/badge.svg)](https://github.com/cuijialin8888-code/git-path-doctor/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/cuijialin8888-code/git-path-doctor)](https://github.com/cuijialin8888-code/git-path-doctor/releases/latest)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**When Git says nothing, ask why.**

Git Path Doctor explains why a path is tracked, ignored, missing, hidden from `git status`, or behaving differently across machines. It turns several low-level Git queries into one readable, evidence-backed report.

```console
$ git-path-doctor explain build/debug.log
Path:  build/debug.log
State: IGNORED
Why:   An ignore rule excludes this untracked path.
Disk:  file
Index: not tracked
Ignore: .gitignore:14 -> *.log
Findings:
  [INFO] The last matching ignore rule is '*.log'.
    Evidence: .gitignore:14
    Next: Edit the rule if it is wrong, or use git add -f only when tracking the file is intentional.
```

[中文说明](README.zh-CN.md)

## Why this exists

Git already has excellent plumbing commands, but the answer to “why is this file acting like that?” is often split across:

- `git status --porcelain=v2`
- `git check-ignore -v`
- `git check-attr`
- `git ls-files -v --stage`
- sparse-checkout configuration and index flags
- path history

Git Path Doctor runs those commands read-only and explains how the evidence fits together. It is useful when:

- `git add` appears to ignore a file;
- a tracked file also matches `.gitignore`;
- edits disappear from ordinary `git status` output;
- a sparse checkout omits a tracked path;
- a file is tracked on one machine but troublesome on another;
- a merge leaves non-obvious index stages;
- a repository contains paths that collide on case-insensitive filesystems.

## Quick start

Python 3.10 or newer and Git are required. The scanner has no runtime Python dependencies and makes no network requests.

```bash
python -m pip install "git-path-doctor @ git+https://github.com/cuijialin8888-code/git-path-doctor.git@v0.1.0"
git-path-doctor explain path/to/file
```

For an isolated install, use `pipx`:

```bash
pipx install "git+https://github.com/cuijialin8888-code/git-path-doctor.git@v0.1.0"
```

From a source checkout:

```bash
python -m pip install -e .
git-path-doctor --help
```

## Commands

### Explain one or more paths

```bash
git-path-doctor explain .env src/app.py generated/output.bin
git-path-doctor --repo ../another-repo explain config/local.toml
git-path-doctor explain src/app.py --json
```

For each path, the report includes:

- an overall state such as `TRACKED`, `MODIFIED`, `STAGED`, `IGNORED`, `SPARSE`, `CONFLICT`, or `TRACKED_MISSING`;
- the last matching ignore rule, source file, and line number;
- index mode and stage entries;
- `assume-unchanged` and `skip-worktree` flags;
- Git attributes such as `text`, `eol`, `filter`, and `linguist-*` when present;
- the latest path commit;
- evidence and a conservative next step for surprising states.

Commands shown under `Next` are suggestions only. Git Path Doctor never runs them.

### Scan a repository for hidden state

```bash
git-path-doctor scan
git-path-doctor scan --json
git-path-doctor scan --fail-on error
```

`scan` inventories the states most likely to make a checkout misleading:

- assume-unchanged paths;
- skip-worktree paths outside normal sparse-checkout use;
- unresolved index stages;
- case-insensitive path collisions.

The default is informational and exits `0`. For CI, `--fail-on warning` or `--fail-on error` returns `10` when a finding reaches the chosen severity.

## What it does not do

Git Path Doctor does not:

- edit `.gitignore`, `.gitattributes`, the index, or working-tree files;
- clear flags, restore files, stage changes, or resolve conflicts;
- replace `git status`, a merge tool, Git LFS, or a full repository health scanner;
- claim that an empty report proves a repository has no Git problem;
- read remotes, upload telemetry, or require an account.

The scope is intentionally narrow: explain local path state with Git’s own evidence.

## Exit codes

| Code | Meaning |
| ---: | --- |
| `0` | Report completed; findings are informational unless a threshold was requested |
| `2` | Invalid command-line usage |
| `3` | Git was unavailable, the repository/path was invalid, or a required Git query failed |
| `10` | `scan --fail-on ...` reached the requested severity |

## JSON output

JSON includes the tool version, repository root, normalized paths, raw evidence fields, findings, and suggestions. Field names are additive within the `0.x` series; consumers should ignore unknown fields.

See [how it works](docs/how-it-works.md) and the [JSON report reference](docs/report-schema.md).

## Safety and privacy

- Every Git operation is read-only.
- Paths must stay inside the discovered working tree.
- Path arguments are passed with literal pathspec handling.
- File contents, diffs, environment variables, credentials, and remotes are not read.
- No telemetry and no network access.

See [SECURITY.md](SECURITY.md) for the security boundary and disclosure process.

## Development

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
python -m compileall -q src tests
```

The integration tests create disposable local Git repositories and cover ignored, tracked-but-ignored, modified, staged, missing, assume-unchanged, and skip-worktree paths. They do not access the network.

Contributions are welcome. Start with [CONTRIBUTING.md](CONTRIBUTING.md) and an issue describing the Git behavior you want the tool to explain.

## License

MIT
