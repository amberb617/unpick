"""Fallback judge: a small open model that runs in-process on CPU, on Windows, Linux and macOS.

For machines with no other on-device model (no Apple Intelligence, no Ollama or LM Studio). unpick
does not ship model weights; `unpick judges install fallback --online` downloads ONE pinned file,
checks its SHA-256 before first use, and refuses to load anything that does not match.

Model: IBM Granite 4.1 3B Instruct, Apache-2.0, Q4_K_M GGUF published by IBM
(huggingface.co/ibm-granite/granite-4.1-3b-GGUF @ab47014). GGUF is a data format, not pickled code.
Runtime: llama-cpp-python >= 0.3.17 (the first release with the fix for CVE-2026-27940, a model-file
parser bug leading to code execution); the tested version is 0.3.36. Prebuilt CPU wheels exist for
Windows x64, Linux x64/arm64 and macOS arm64; Intel Macs and Windows on Arm compile from source.
Output is constrained with response_format {"type": "json_object", "schema": ...} at temperature 0, and
still validated, because llama-cpp-python silently falls back to plain JSON when a schema cannot be
turned into a grammar. Verified in docs/verified/fallback-judge.md.
"""

from __future__ import annotations

import hashlib
import importlib.util
import urllib.request
from pathlib import Path

NAME = "fallback"
KIND = "on-device"
REPO = "ibm-granite/granite-4.1-3b-GGUF"
REVISION = "ab4701481089b58a082ef63cc1cee738887293ff"
FILE = "granite-4.1-3b-Q4_K_M.gguf"
SIZE = 2_099_501_664
SHA256 = "662b0626cd58f443baea23559b469df6576a81d349649c59413b36a9fb32eb29"
URL = f"https://huggingface.co/{REPO}/resolve/{REVISION}/{FILE}"
MIN_RUNTIME = (0, 3, 17)
MODEL = Path.home() / ".unpick" / "models" / FILE
VERIFIED_MARK = MODEL.with_suffix(".sha256-ok")
RUNTIME = "llama-cpp-python==0.3.36"
WHEEL_INDEX = "https://abetlen.github.io/llama-cpp-python/whl/cpu"
# The macOS arm64 wheels on that index (0.3.34-0.3.36) are corrupt zip files even though they match
# GitHub's published digests (checked 2026-10-18), so macOS builds from source with the Xcode tools;
# Windows x64 and Linux x64/arm64 wheels were verified intact.
INSTALL_RUNTIME = f"{RUNTIME} --extra-index-url {WHEEL_INDEX} --only-binary=llama-cpp-python"
UNVERIFIED = "end-to-end JSON-schema run with this model not yet recorded; see docs/BENCHMARK.md"

_llm = None


def _runtime_version() -> tuple[int, ...] | None:
    if not importlib.util.find_spec("llama_cpp"):
        return None
    from importlib.metadata import version
    try:
        return tuple(int(x) for x in version("llama-cpp-python").split(".")[:3])
    except ValueError:
        return (0, 0, 0)


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verified() -> bool:
    """True only if the model file is present and its SHA-256 matches the pin (cached after the first check)."""
    if not MODEL.is_file() or MODEL.stat().st_size != SIZE:
        return False
    if VERIFIED_MARK.is_file() and VERIFIED_MARK.stat().st_mtime >= MODEL.stat().st_mtime:
        return True
    if _sha256(MODEL) != SHA256:
        return False
    VERIFIED_MARK.write_text(SHA256, encoding="utf-8")
    return True


def detect() -> list[dict]:
    rt = _runtime_version()
    row = {"id": "fallback:granite-4.1-3b", "model": f"{REPO}/{FILE}", "found_by": str(MODEL)}
    if rt is None and not MODEL.exists():
        return []
    if rt is None:
        return [{**row, "usable": False, "reason": f"install the runtime: pip install {INSTALL_RUNTIME}"}]
    if rt < MIN_RUNTIME:
        return [{**row, "usable": False, "reason": f"llama-cpp-python {'.'.join(map(str, rt))} is older than 0.3.17 (CVE-2026-27940)"}]
    if not MODEL.exists():
        return [{**row, "usable": False, "reason": "model not downloaded: unpick judges install fallback --online"}]
    if not verified():
        return [{**row, "usable": False, "reason": "model file does not match the pinned SHA-256; delete it and reinstall"}]
    return [row]


def runtime_argv() -> list[str]:
    """pip command for this OS: prebuilt CPU wheel on Windows and Linux, source build on macOS."""
    import platform
    import sys
    base = [sys.executable, "-m", "pip", "install", RUNTIME]
    if platform.system() == "Darwin":
        return base + ["--no-binary=llama-cpp-python"]
    return base + ["--extra-index-url", WHEEL_INDEX, "--only-binary=llama-cpp-python"]


def install_runtime() -> tuple[int, str]:
    """Install llama-cpp-python into unpick's own environment. Downloads from PyPI/GitHub; callers require --online."""
    import subprocess
    rt = _runtime_version()
    if rt is not None and rt >= MIN_RUNTIME:
        return 0, "runtime already installed"
    p = subprocess.run(runtime_argv(), capture_output=True, text=True)
    return p.returncode, (p.stdout + p.stderr)[-1500:]


def install(progress=None) -> str:
    """Download the pinned model (about 2.1 GB from huggingface.co) and verify it. Callers require --online."""
    MODEL.parent.mkdir(parents=True, exist_ok=True)
    part = MODEL.with_suffix(".part")
    h = hashlib.sha256()
    with urllib.request.urlopen(URL, timeout=60) as r, part.open("wb") as out:  # noqa: S310 - fixed pinned URL
        while chunk := r.read(1 << 20):
            out.write(chunk)
            h.update(chunk)
            if progress:
                progress(out.tell(), SIZE)
    if h.hexdigest() != SHA256:
        part.unlink(missing_ok=True)
        raise RuntimeError("downloaded file does not match the pinned SHA-256; nothing was installed")
    part.replace(MODEL)
    VERIFIED_MARK.write_text(SHA256, encoding="utf-8")
    return str(MODEL)


def complete(model: str, prompt: str, schema: dict) -> str:
    global _llm
    if not verified():
        raise RuntimeError("fallback model missing or not verified")
    if _llm is None:
        from llama_cpp import Llama
        _llm = Llama(model_path=str(MODEL), n_ctx=8192, verbose=False)
    out = _llm.create_chat_completion(messages=[{"role": "user", "content": prompt}], temperature=0.0,
                                      response_format={"type": "json_object", "schema": schema})
    return out["choices"][0]["message"]["content"]
