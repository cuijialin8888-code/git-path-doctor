from __future__ import annotations

import json
from collections.abc import Iterable
from typing import Any

from . import __version__
from .models import Finding, PathReport, ScanReport


SARIF_SCHEMA = "https://json.schemastore.org/sarif-2.1.0.json"
_LEVELS = {"info": "note", "warning": "warning", "error": "error"}


def render_explain(reports: Iterable[PathReport], format_name: str, repository: str) -> str:
    reports = list(reports)
    if format_name == "json":
        return json.dumps(
            {
                "tool": "git-path-doctor",
                "version": __version__,
                "repository": repository,
                "paths": [report.to_dict() for report in reports],
            },
            indent=2,
            ensure_ascii=False,
        ) + "\n"
    if format_name == "sarif":
        findings = ((report, finding) for report in reports for finding in report.findings)
        return _sarif(
            repository,
            findings,
            {"mode": "explain", "paths": [report.path for report in reports]},
        )
    raise ValueError(f"unsupported explain format: {format_name}")


def render_scan(report: ScanReport, format_name: str) -> str:
    if format_name == "json":
        payload = report.to_dict()
        payload.update({"tool": "git-path-doctor", "version": __version__})
        return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    if format_name == "sarif":
        findings = ((None, finding) for finding in report.findings)
        return _sarif(
            report.repository,
            findings,
            {
                "mode": "scan",
                "trackedPaths": report.tracked_paths,
                "sparseCheckout": report.sparse_checkout,
            },
        )
    raise ValueError(f"unsupported scan format: {format_name}")


def _sarif(
    repository: str,
    findings: Iterable[tuple[PathReport | None, Finding]],
    properties: dict[str, Any],
) -> str:
    pairs = list(findings)
    unique_rules: dict[str, Finding] = {}
    for _, finding in pairs:
        unique_rules.setdefault(finding.code, finding)
    rules = [
        {
            "id": code,
            "name": finding.code,
            "shortDescription": {"text": finding.message},
            "help": {"text": finding.suggestion or finding.message},
            "defaultConfiguration": {"level": _LEVELS.get(finding.severity, "note")},
        }
        for code, finding in sorted(unique_rules.items())
    ]
    results: list[dict[str, Any]] = []
    for report, finding in pairs:
        result: dict[str, Any] = {
            "ruleId": finding.code,
            "level": _LEVELS.get(finding.severity, "note"),
            "message": {"text": finding.message},
            "properties": {
                "evidence": finding.evidence,
                "suggestion": finding.suggestion,
                "repository": repository,
                **({"pathState": report.state} if report else {}),
            },
        }
        if report:
            result["locations"] = [
                {"physicalLocation": {"artifactLocation": {"uri": report.path.replace("\\", "/")}}}
            ]
        results.append(result)
    payload = {
        "$schema": SARIF_SCHEMA,
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "git-path-doctor",
                        "version": __version__,
                        "informationUri": "https://github.com/cuijialin8888-code/git-path-doctor",
                        "rules": rules,
                    }
                },
                "invocations": [{"executionSuccessful": True, "properties": {"readOnly": True}}],
                "results": results,
                "properties": {"repository": repository, "readOnly": True, **properties},
            }
        ],
    }
    return json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
