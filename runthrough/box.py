"""A no-network box: step 4 of the five-minute triage ("first run in a box"), applied to the scanners
themselves and, in phase 3, to the component under review.

Order of preference:
  1. Anthropic sandbox-runtime (`srt`, macOS and Linux): network denied, writes denied, credential folders
     unreadable. Settings format verified against anthropics/sandbox-runtime@626a596.
  2. Docker: `docker run --network none` with the target mounted read-only, in an image that has the tool.
     For scanner backends the image is built once by `runthrough backends install <name> --docker --online`.
  3. Otherwise refuse, clearly. runthrough never pretends something was boxed.
"""

from __future__ import annotations

import json
import platform
import shutil
import subprocess
import tempfile
from pathlib import Path

TIMEOUT = 600
CONTAINER_TARGET = "/work/target"
DENY_READ = ["~/.ssh", "~/.aws", "~/.azure", "~/.config/gcloud", "~/.config/gh", "~/.gnupg", "~/.kube",
             "~/.docker", "~/.netrc", "~/.npmrc", "~/.pypirc", "~/.git-credentials", "~/Library/Keychains",
             "~/Library/Application Support/Google/Chrome", "~/Library/Application Support/Firefox",
             "~/.mozilla", "~/.config/google-chrome", "~/.runthrough/consent.json"]


class NoBox(RuntimeError):
    pass


def available() -> str | None:
    if shutil.which("srt") and platform.system() in ("Darwin", "Linux"):
        return "srt"
    if shutil.which("docker"):
        return "docker"
    return None


def srt_settings() -> dict:
    return {"network": {"allowedDomains": [], "deniedDomains": []},
            "filesystem": {"denyRead": DENY_READ, "allowWrite": [], "denyWrite": []}}


def docker_image(tool: str) -> str:
    return f"runthrough-box/{tool}"


def _docker_has(image: str) -> bool:
    p = subprocess.run(["docker", "image", "inspect", image], capture_output=True)
    return p.returncode == 0


def run(argv: list[str], read_only: list[Path], tool: str | None = None) -> subprocess.CompletedProcess:
    kind = available()
    if kind == "srt":
        with tempfile.TemporaryDirectory() as d:
            settings = Path(d) / "srt-settings.json"
            settings.write_text(json.dumps(srt_settings()), encoding="utf-8")
            return subprocess.run(["srt", "--settings", str(settings), *argv], capture_output=True, text=True,
                                  timeout=TIMEOUT, encoding="utf-8", errors="replace")
    if kind == "docker":
        image = docker_image(tool or Path(argv[0]).name)
        if not _docker_has(image):
            raise NoBox(f"no Docker image {image}; build it once with: runthrough backends install {tool or argv[0]} --docker --online")
        target = read_only[0]
        host = str(target)
        inner = [a.replace(host, CONTAINER_TARGET) for a in argv]
        cmd = ["docker", "run", "--rm", "--network", "none", "--read-only", "--tmpfs", "/tmp",
               "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
               "-v", f"{host}:{CONTAINER_TARGET}:ro", image, *inner]
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT, encoding="utf-8", errors="replace")
        p.stdout = p.stdout.replace(CONTAINER_TARGET, host)  # report host paths, not container paths
        return p
    raise NoBox("no box available: install Anthropic sandbox-runtime (srt, macOS/Linux) or Docker, or run without --boxed")


def dockerfile(pip_spec: str) -> str:
    return (f"FROM python:3.12-slim\nRUN pip install --no-cache-dir '{pip_spec}'\n"
            "RUN useradd -m box\nUSER box\nWORKDIR /work\n")


def build_image(tool: str, pip_spec: str) -> tuple[int, str]:
    """Build the image for a backend. This downloads from Docker Hub and PyPI; callers require --online."""
    with tempfile.TemporaryDirectory() as d:
        Path(d, "Dockerfile").write_text(dockerfile(pip_spec), encoding="utf-8")
        p = subprocess.run(["docker", "build", "-t", docker_image(tool), d], capture_output=True, text=True)
        return p.returncode, (p.stdout + p.stderr)[-2000:]
