"""Encoded execution: commands that decode or download text and hand it straight to a shell.

Pipe-to-shell hides the real command from the reader: what you see is `base64 -d | bash` or
`curl ... | sh`, not what runs. ClawHavoc used a base64 one-liner as its lure (Unit 42,
https://unit42.paloaltonetworks.com/openclaw-ai-supply-chain-risk/). PowerShell's `-EncodedCommand`
and `iex (iwr ...)` are the Windows equivalents.

Blobs are decoded in memory only, and the decoded text is reported. Nothing is ever executed.
"""

from __future__ import annotations

import base64
import binascii
import gzip
import re
import zlib

from unpick.checks import Hit

RULE_ID = "RT-ENCODED-EXEC"
TITLE = "Encoded or piped execution"
SEVERITY = "high"
WHY = "Text is decoded or downloaded and run in one step, so the command that actually executes is not the one you read."
FALSE_POSITIVE = "Official installers sometimes use curl-pipe-to-shell from the vendor's own domain; read the script at that URL before deciding."

SHELL = r"(sudo\s+)?(ba|z|da|k)?sh\b|python3?\b|perl\b|ruby\b|node\b"
PIPES = [
    (re.compile(r"\bbase64\s+(-d|-D|--decode)\b.*\|\s*(" + SHELL + ")", re.I), "base64 decoded into a shell"),
    (re.compile(r"\|\s*base64\s+(-d|-D|--decode)\b.*\|\s*(" + SHELL + ")", re.I), "base64 decoded into a shell"),
    (re.compile(r"\b(curl|wget)\b[^|\n]*\|\s*(" + SHELL + ")", re.I), "download piped into a shell"),
    (re.compile(r"\b(sh|bash|zsh)\s+(-c\s+)?[\"']?\$\(\s*(curl|wget)\b", re.I), "shell runs a downloaded script"),
    (re.compile(r"\b(iex|invoke-expression)\b.{0,10}\(?\s*(iwr|irm|invoke-webrequest|invoke-restmethod|new-object\s+net\.webclient)", re.I), "PowerShell downloads and runs code"),
    (re.compile(r"\b(iwr|irm|invoke-webrequest|invoke-restmethod)\b[^|\n]*\|\s*(iex|invoke-expression)\b", re.I), "PowerShell downloads and runs code"),
    (re.compile(r"\binvoke-expression\b", re.I), "Invoke-Expression runs a string as code"),
    (re.compile(r"\bpowershell(\.exe)?\b.*\s-(e|ec|en|enc|enco|encodedcommand)\s+([A-Za-z0-9+/=]{8,})", re.I), "PowerShell encoded command"),
    (re.compile(r"\bdownloadstring\s*\(", re.I), "PowerShell DownloadString"),
]
B64 = re.compile(r"(?<![A-Za-z0-9+/=])[A-Za-z0-9+/]{24,}={0,2}(?![A-Za-z0-9+/=])")
HEX = re.compile(r"(?<![0-9A-Fa-f])(?:[0-9A-Fa-f]{2}){20,}(?![0-9A-Fa-f])")
DANGER = re.compile(
    r"\b(curl|wget|bash|sh -c|zsh|chmod \+x|nohup|osascript|powershell|iex|invoke-|/dev/tcp|nc -e|"
    r"rm -rf|crontab|launchctl|base64 -d|python -c|eval)\b|https?://",
    re.I,
)


def _printable(b: bytes) -> str | None:
    try:
        s = b.decode("utf-8")
    except UnicodeDecodeError:
        try:
            s = b.decode("utf-16-le")
        except UnicodeDecodeError:
            return None
    ok = sum(c.isprintable() or c in "\r\n\t" for c in s)
    return s if s and ok / len(s) > 0.9 else None


def decode_blob(blob: str, kind: str) -> str | None:
    """Decode a base64 or hex blob (and gzip/zlib inside it) to text, in memory. Never executed."""
    try:
        raw = base64.b64decode(blob + "=" * (-len(blob) % 4), validate=True) if kind == "base64" else bytes.fromhex(blob)
    except (binascii.Error, ValueError):
        return None
    for unpack in (gzip.decompress, zlib.decompress):
        try:
            raw = unpack(raw)
            break
        except (OSError, zlib.error, EOFError):
            pass
    return _printable(raw)


def _decode_ps(arg: str) -> str | None:
    try:
        return base64.b64decode(arg + "=" * (-len(arg) % 4)).decode("utf-16-le")
    except (binascii.Error, UnicodeDecodeError):
        return None


def run(doc):
    for n, line in enumerate(doc.lines, 1):
        reported = False
        for rx, label in PIPES:
            m = rx.search(line)
            if not m:
                continue
            extra = {"pattern": label}
            if "encoded command" in label:
                decoded = _decode_ps(m.group(m.lastindex))
                if decoded:
                    extra["decoded"] = decoded
            inline = B64.search(line)
            if inline and "base64" in label:
                decoded = decode_blob(inline.group(), "base64")
                if decoded:
                    extra["decoded"] = decoded
            msg = label + (f"; decodes to: {extra['decoded'][:120]!r}" if "decoded" in extra else "")
            yield Hit(n, msg, None, extra)
            reported = True
            break
        if reported:
            continue
        for rx, kind in ((B64, "base64"), (HEX, "hex")):
            for m in rx.finditer(line):
                decoded = decode_blob(m.group(), kind)
                if decoded and DANGER.search(decoded):
                    yield Hit(n, f"{kind} blob decodes to something that looks like a command: {decoded[:120]!r}",
                              "medium", {"encoding": kind, "decoded": decoded})
