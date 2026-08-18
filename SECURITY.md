# Security policy

## Supported versions

The latest tagged release receives security fixes.

## Reporting a vulnerability

Please use GitHub’s private vulnerability reporting for this repository. Do not open a public issue containing an exploit, credential, or sensitive repository path.

## Security boundary

Git Path Doctor is a local diagnostic tool, not a sandbox or malware scanner.

Normal operation:

- launches the installed `git` executable with read-only subcommands;
- reads Git-produced metadata about paths, the index, attributes, ignore rules, configuration, and history;
- does not read file contents or diffs;
- does not contact remotes or other network services;
- does not modify the working tree, index, configuration, hooks, or ignore files.

A compromised `git` executable, malicious Git wrapper, or hostile repository configuration that changes Git’s own command behavior is outside this tool’s trust boundary. Run untrusted repositories in an appropriate operating-system sandbox.
