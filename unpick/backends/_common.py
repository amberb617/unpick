"""Small helpers shared by backend adapters."""

from __future__ import annotations

from pathlib import Path

from unpick.finding import Finding

SEV = {"critical": "high", "high": "high", "medium": "medium", "moderate": "medium", "low": "low",
       "info": "info", "informational": "info", "safe": "info", "none": "info"}


def sev(value) -> str:
    return SEV.get(str(value or "").lower(), "medium")


def finding(source: str, rule: str, severity, path: str, line: int, message: str, why: str, fp: str,
            original_rule_id=None, original_message=None, extra=None) -> Finding:
    return Finding(rule_id=f"{source}:{rule}", source=f"backend:{source}", severity=sev(severity), path=path,
                   line=int(line or 0), message=message, why=why, false_positive=fp,
                   original_rule_id=original_rule_id or rule, original_message=original_message or message,
                   extra=extra or {})


def offset_to_line(path: Path, offset: int) -> int:
    try:
        return path.read_bytes()[:offset].count(b"\n") + 1
    except OSError:
        return 0
