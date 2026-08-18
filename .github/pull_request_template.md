## What changed

<!-- Describe the user-visible explanation or diagnostic change. -->

## Why

<!-- Link the issue or document the surprising Git behavior. -->

## Evidence and safety

- [ ] Uses read-only Git commands only
- [ ] Preserves literal, NUL-delimited path handling where applicable
- [ ] Adds or updates a disposable-repository test
- [ ] Documents new states, findings, or exit behavior

## Checks

- [ ] `python -m unittest discover -s tests -v`
- [ ] `python -m compileall -q src tests`
