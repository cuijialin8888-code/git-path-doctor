# Contributing

Thanks for helping Git Path Doctor explain Git more accurately.

## Before opening a change

Open an issue with:

- the surprising Git behavior;
- the smallest commands that reproduce it;
- Git version and operating system;
- expected and actual Git Path Doctor output;
- whether the behavior involves sparse checkout, submodules, attributes, or unusual path names.

Do not include repository secrets, private paths, or confidential file contents.

## Development

```bash
git clone https://github.com/cuijialin8888-code/git-path-doctor.git
cd git-path-doctor
python -m pip install -e .
python -m unittest discover -s tests -v
python -m compileall -q src tests
```

The project targets Python 3.10+ and uses only the standard library at runtime. Please avoid adding a dependency when a small, readable standard-library implementation is sufficient.

## Routine maintenance

- Keep GitHub Actions on verified immutable commit pins and confirm public CI before treating a workflow change as accepted.
- Preserve Git as the evidence source for path state; do not replace its ignore or attribute behavior with heuristics during maintenance.
- Keep path-bearing probes literal and read-only, including for sparse checkouts, linked worktrees, and unusual filenames.

## Pull requests

- Keep behavior read-only.
- Add a disposable-repository test for every new Git state or parser branch.
- Preserve NUL-delimited Git output where path names are involved.
- Document new finding codes and exit behavior.
- Keep suggestions conservative and clearly separate from actions.
