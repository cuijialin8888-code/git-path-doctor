# Path debugging workflow

Use `explain` for one surprising path and `scan` for repository-wide hidden state.

For one path, use `git-path-doctor explain .env src/app.py generated/output.bin`, `git-path-doctor --repo ../another-repo explain config/local.toml`, or add `--json` for machine-readable output.

Use `git-path-doctor scan`, `scan --json`, or `scan --fail-on error` when ordinary `git status` may hide assume-unchanged, skip-worktree, unresolved index, or case-collision state. Read state, disk and index evidence, matching ignore rules, attributes, flags, and history together.

`Next` is a review hint; the tool does not run it. An empty report means the selected checks found no finding, not that every repository problem is absent. The tool runs read-only Git queries and does not edit the index, working tree, attributes, ignore rules, or configuration.