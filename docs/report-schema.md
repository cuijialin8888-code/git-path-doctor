# JSON report reference

Use `git-path-doctor explain PATH --json` or `git-path-doctor scan --json` for automation.

## Explain envelope

```json
{
  "tool": "git-path-doctor",
  "version": "0.1.0",
  "repository": "/repo",
  "paths": [
    {
      "input_path": "debug.log",
      "path": "debug.log",
      "absolute_path": "/repo/debug.log",
      "state": "IGNORED",
      "summary": "An ignore rule excludes this untracked path.",
      "exists": true,
      "filesystem_kind": "file",
      "tracked_entries": [],
      "status": [],
      "ignore_match": {
        "source": ".gitignore",
        "line": 14,
        "pattern": "*.log",
        "path": "debug.log"
      },
      "attributes": {},
      "latest_commit": null,
      "sparse_checkout": false,
      "findings": []
    }
  ]
}
```

## Finding fields

| Field | Meaning |
| --- | --- |
| `severity` | `info`, `warning`, or `error` |
| `code` | Stable machine-readable identifier |
| `message` | Human-readable explanation |
| `evidence` | Optional supporting fact from Git |
| `suggestion` | Optional next step; never executed by the tool |

## Compatibility

During the `0.x` series, new fields and finding codes may be added in minor releases. Existing field meanings will not change without a changelog entry. Consumers should ignore unknown fields and finding codes.
