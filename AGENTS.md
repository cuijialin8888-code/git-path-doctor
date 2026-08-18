# Repository instructions

- Keep every diagnostic read-only; suggestions may describe commands but the tool must never execute a mutating Git command.
- Treat Git output as authoritative evidence. Do not reimplement ignore or attribute matching.
- Use NUL-delimited Git output for path-bearing commands and literal pathspec handling for user paths.
- Add a disposable local-repository integration test for each new state or parser branch.
- Preserve the zero-runtime-dependency boundary unless a maintainer explicitly approves a change.
- Run `python -m unittest discover -s tests -v` and `python -m compileall -q src tests` before submitting.
