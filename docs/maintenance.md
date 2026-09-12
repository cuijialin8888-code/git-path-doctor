# Maintenance checklist

Keep Git Path Doctor read-only, local, and evidence-backed.

## Routine checks

- Do not edit the index, working tree, attributes, ignore rules, or repository configuration.
- Preserve the distinction between tracked, ignored, missing, sparse, conflict, and hidden index states.
- Add disposable-repository fixtures for new Git behavior and keep path-boundary checks covered.
- For releases, validate the package and the public CI result on the exact commit.

## Review log

- 2026-09-12: reviewed public `main`, open Issues/PRs, and recent Actions; no open Issues/PRs were present, and the latest main-branch CI run (`34178257247`) completed successfully.
