# How Git Path Doctor works

Git Path Doctor is an evidence combiner, not a second Git implementation. It asks the installed Git executable for local repository facts and then applies a small, documented decision tree.

## Evidence sources

| Evidence | Git query | Used for |
| --- | --- | --- |
| Working-tree and index status | `git status --porcelain=v2 -z` | modified, staged, untracked, ignored, renamed, and unmerged states |
| Ignore provenance | `git check-ignore -v -z --no-index` | last matching pattern, source, and line, including paths already tracked |
| Index markers | `git ls-files -v -z` | assume-unchanged and skip-worktree flags |
| Index stages and modes | `git ls-files --stage -z` | conflicts, symlinks, submodules, and tracked state |
| Attributes | `git check-attr -z --all` | effective path attributes |
| Path history | `git log -1 --format=... -- PATH` | latest commit touching a path |
| Sparse mode | `git config --bool --get core.sparseCheckout` | distinguish expected sparse paths from manual skip-worktree use |

NUL-delimited output avoids ambiguity for spaces, tabs, quotes, Unicode, and most unusual path names. Pathspecs are passed in literal mode and paths outside the repository are rejected.

## State precedence

The high-level state is selected in this order:

1. unresolved index stages → `CONFLICT`;
2. tracked but absent without skip-worktree → `TRACKED_MISSING`;
3. staged changes → `STAGED`;
4. unstaged changes → `MODIFIED`;
5. tracked, omitted skip-worktree path → `SPARSE`;
6. other tracked path → `TRACKED`;
7. matching ignore rule → `IGNORED`;
8. existing path outside the index → `UNTRACKED`;
9. otherwise → `MISSING`.

Findings are independent of the high-level state. For example, a path can be `TRACKED` and also receive `ASSUME_UNCHANGED` and `TRACKED_DESPITE_IGNORE` findings.

## Repository scan

`scan` reads the full index once. It reports:

- lowercase `git ls-files -v` markers as assume-unchanged;
- `S` markers as skip-worktree;
- non-zero index stages as unresolved conflicts;
- groups of tracked paths that differ only by Unicode case folding.

The scan does not read every tracked file and does not run per-file history or attribute queries.

## Limitations

- Git Path Doctor explains the current local checkout, not remote repository state.
- Git version and platform behavior remain authoritative when they differ from the tool’s explanation.
- Case-fold collision reporting is conservative and may not exactly reproduce every filesystem’s locale-specific rules.
- The tool does not inspect file contents, LFS object availability, remote filters, hooks, or arbitrary external clean/smudge programs.
- A suggestion is not automatically safe for every workflow; review it before changing repository state.
