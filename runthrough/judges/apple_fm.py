"""Apple Intelligence via the Foundation Models framework: on-device, nothing leaves the Mac.

Needs macOS 26 or later on Apple silicon with Apple Intelligence turned on. runthrough ships a tiny Swift
command-line shim (shims/apple-fm/main.swift) and builds it with swiftc on first use. The session is
created with no tools and uses greedy sampling; the output is constrained by guided generation.
Verified in docs/VERIFIED.md. In testing the model invented line numbers, so treat it as a weak witness.
"""

from __future__ import annotations

import json
import platform
import shutil
import subprocess
from pathlib import Path

NAME = "apple-fm"
KIND = "on-device"
_PKG = Path(__file__).resolve().parents[1]
SRC = next((p for p in (_PKG / "_shims" / "apple-fm" / "main.swift", _PKG.parent / "shims" / "apple-fm" / "main.swift")
            if p.exists()), _PKG.parent / "shims" / "apple-fm" / "main.swift")
BIN = Path.home() / ".runthrough" / "bin" / "apple-fm"
BUILD = ["xcrun", "swiftc", "-O", "-parse-as-library", "-target", "arm64-apple-macosx26.0"]


def _macos_ok() -> tuple[bool, str]:
    if platform.system() != "Darwin":
        return False, "not macOS"
    if platform.machine() != "arm64":
        return False, "needs Apple silicon"
    major = int((platform.mac_ver()[0] or "0").split(".")[0])
    if major < 26:
        return False, f"needs macOS 26 or later (found {platform.mac_ver()[0]})"
    return True, ""


def build() -> tuple[bool, str]:
    if BIN.exists() and SRC.exists() and BIN.stat().st_mtime >= SRC.stat().st_mtime:
        return True, ""
    if not SRC.exists():
        return False, "shim source not found in this install"
    if not shutil.which("xcrun"):
        return False, "swiftc not found (install the Xcode command line tools)"
    BIN.parent.mkdir(parents=True, exist_ok=True)
    p = subprocess.run(BUILD + [str(SRC), "-o", str(BIN)], capture_output=True, text=True)
    return (p.returncode == 0, p.stderr.strip()[-300:])


def detect() -> list[dict]:
    ok, why = _macos_ok()
    if not ok:
        return []
    row = {"id": "apple-fm:system", "model": "SystemLanguageModel.default", "found_by": "macOS 26+ on Apple silicon"}
    built, err = build()
    if not built:
        return [{**row, "usable": False, "reason": err}]
    return [row]


def complete(model: str, prompt: str, schema: dict) -> str:
    p = subprocess.run([str(BIN)], input=json.dumps({"prompt": prompt, "schema": schema}),
                       capture_output=True, text=True, timeout=600)
    if p.returncode == 2:
        raise RuntimeError(f"Apple Intelligence unavailable: {p.stderr.strip()}")
    if p.returncode != 0:
        raise RuntimeError(p.stderr.strip()[-300:])
    return p.stdout
