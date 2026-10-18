"""The judge: a model's opinion, used as one witness among several, never as the verdict.

The component under review is hostile input. Every tier gets the same treatment:
  * the file is wrapped in a delimited UNTRUSTED block and the prompt says nothing inside it is addressed to the judge;
  * the judge has no tools and no file access;
  * output must match schemas/judge.schema.json; invalid JSON is retried once, then recorded as a judge-failed finding;
  * temperature 0 (or the runtime's closest equivalent);
  * long files are chunked with overlap and merged by line.

Tier order: on-device first (Apple Foundation Models, then local runtimes), then hosted agent CLIs and API
keys, which send the full component to a provider and need per-session consent. Each tier is one file in
this folder that defines:

    NAME, KIND ("on-device" | "hosted"), PROVIDER (hosted only)
    detect() -> list[dict]          -- what is available: {"id": "<tier>:<model>", "model":..., "found_by":...}
    complete(model, prompt, schema) -> str   -- raw model text, expected to be JSON
"""

from __future__ import annotations

import importlib
import json
import pkgutil
import secrets
from dataclasses import dataclass, field

from unpick.finding import Finding, with_context
from unpick.resources import data_dir, load_json, schemas_dir

PROMPT_VERSION = "judge-v1"
CHUNK_LINES = 200
OVERLAP = 20
CATEGORIES = ["RT-UNICODE", "RT-PREREQ", "RT-ENCODED-EXEC", "RT-PASTE-HOST", "RT-SENSITIVE-PATH", "RT-SECRECY",
              "RT-TOOL-DESC", "RT-RULES-FILE", "RT-RENDER-DIVERGE", "RT-LOOKALIKE", "OTHER"]


@dataclass
class JudgeRun:
    findings: list[Finding] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    meta: dict = field(default_factory=dict)
    unavailable: bool = False


def tiers() -> dict:
    out = {}
    for info in pkgutil.iter_modules(__path__):
        if info.name.startswith("_"):
            continue
        mod = importlib.import_module(f"{__name__}.{info.name}")
        out[mod.NAME] = mod
    return out


ORDER = ["apple-fm", "ollama", "llamacpp", "lmstudio", "mlx", "openai-local", "foundry-local", "fallback",
         "claude-code", "codex", "gemini", "grok", "api"]


def detect_all() -> list[dict]:
    from unpick import consent

    rows = []
    mods = tiers()
    for name in ORDER + sorted(set(mods) - set(ORDER)):
        mod = mods.get(name)
        if not mod:
            continue
        for row in mod.detect():
            row.setdefault("tier", name)
            row.setdefault("kind", mod.KIND)
            row.setdefault("provider", getattr(mod, "PROVIDER", None))
            row["consent"] = "not needed" if mod.KIND == "on-device" else consent.status(row["provider"])
            row["adversarial"] = _reliability().get(row["id"])
            rows.append(row)
    return rows


def _reliability() -> dict:
    """Adversarial-corpus results per judge id, written by tests/benchmark.py (docs/BENCHMARK.md)."""
    try:
        return load_json("judge_reliability.json")
    except FileNotFoundError:
        return {}


def default_judge() -> str | None:
    for row in detect_all():
        if row["kind"] == "on-device" and row.get("usable", True):
            return row["id"]
    return None


def schema() -> dict:
    """The judge schema as runtimes take it: without $schema / $id, which some validators refuse
    (Claude Code's --json-schema rejects the draft 2020-12 meta-schema reference)."""
    sch = json.loads((schemas_dir() / "judge.schema.json").read_text(encoding="utf-8"))
    return {k: v for k, v in sch.items() if k not in ("$schema", "$id")}


def build_prompt(rel: str, lines: list[str], start: int) -> str:
    """Wrap the file as untrusted data. A random fence means the file cannot forge the closing marker."""
    template = (data_dir() / "prompts" / f"{PROMPT_VERSION}.txt").read_text(encoding="utf-8")
    fence = "UNTRUSTED-" + secrets.token_hex(8)
    numbered = "\n".join(f"{start + i:>5} | {l}" for i, l in enumerate(lines))
    return template.format(fence=fence, path=rel, content=numbered, categories=", ".join(CATEGORIES))


def _chunks(lines: list[str]):
    if len(lines) <= CHUNK_LINES:
        yield 1, lines
        return
    i = 0
    while i < len(lines):
        yield i + 1, lines[i:i + CHUNK_LINES]
        i += CHUNK_LINES - OVERLAP


def validate(obj) -> str | None:
    """Minimal structural check against judge.schema.json (no jsonschema dependency in core)."""
    if not isinstance(obj, dict):
        return "not an object"
    for key in ("suspicious", "explanation", "confidence"):
        if key not in obj:
            return f"missing {key}"
    if not isinstance(obj["suspicious"], list) or not isinstance(obj["explanation"], str):
        return "wrong types"
    c = obj["confidence"]
    if not isinstance(c, (int, float)) or not 0 <= c <= 1:
        return "confidence out of range"
    for s in obj["suspicious"]:
        if not isinstance(s, dict) or not isinstance(s.get("line"), int) or s.get("category") not in CATEGORIES:
            return "bad suspicious entry"
    return None


def _ask(mod, model: str, prompt: str):
    sch = schema()
    last = None
    for _ in range(2):  # one retry on invalid JSON
        try:
            raw = mod.complete(model, prompt, sch)
        except Exception as e:  # runtime errors become a judge-failed finding, never a crash
            return None, f"{type(e).__name__}: {e}"
        try:
            obj = json.loads(_strip_fences(raw))
        except (json.JSONDecodeError, TypeError) as e:
            last = f"invalid JSON: {e}"
            continue
        problem = validate(obj)
        if problem is None:
            return obj, None
        last = problem
    return None, last


def _strip_fences(raw: str) -> str:
    s = (raw or "").strip()
    if s.startswith("```"):
        s = s.split("\n", 1)[1] if "\n" in s else s
        s = s.rsplit("```", 1)[0]
    return s.strip()


def _severity(confidence: float) -> str:
    if confidence >= 0.8:
        return "high"
    return "medium" if confidence >= 0.5 else "low"


def run(judge_id: str, docs, consent=None) -> JudgeRun:
    from unpick import consent as consent_mod

    tier, _, model = judge_id.partition(":")
    mods = tiers()
    source = f"judge:{judge_id}"
    if tier not in mods:
        return JudgeRun(errors=[f"unknown judge tier {tier!r}"], meta={"kind": "judge", "source": source, "status": "unknown"}, unavailable=True)
    mod = mods[tier]
    provider = mod.provider_for(model) if hasattr(mod, "provider_for") else getattr(mod, "PROVIDER", None)
    meta = {"kind": "judge", "name": judge_id, "source": source, "on_device": mod.KIND == "on-device",
            "provider": provider, "prompt_version": PROMPT_VERSION, "unverified": getattr(mod, "UNVERIFIED", None)}
    avail = {r["id"]: r for r in mod.detect()}
    if not model:
        usable = [r for r in avail.values() if r.get("usable", True)]
        if not usable:
            return JudgeRun(meta={**meta, "status": "not available"}, unavailable=True)
        judge_id = usable[0]["id"]
        model = judge_id.partition(":")[2]
        source = meta["source"] = f"judge:{judge_id}"
    elif judge_id not in avail or not avail[judge_id].get("usable", True):
        reason = avail.get(judge_id, {}).get("reason", "not found on this machine")
        return JudgeRun(errors=[f"{judge_id}: {reason}"], meta={**meta, "status": "not available"}, unavailable=True)
    if mod.KIND == "hosted":
        ok = consent_mod.ensure(provider, ask=consent)
        meta["network"] = ok
        if not ok:
            return JudgeRun(errors=[f"no consent to send content to {provider}"], meta={**meta, "status": "declined"}, unavailable=True)
        meta["network_detail"] = f"full content of every scanned file sent to {provider}"
    else:
        meta["network"] = False

    out = JudgeRun(meta={**meta, "status": "ran"})
    for doc in docs:
        merged: dict[int, dict] = {}
        explanations, confs = [], []
        for start, chunk in _chunks(doc.lines):
            obj, err = _ask(mod, model, build_prompt(doc.rel, chunk, start))
            if err:
                out.findings.append(Finding(
                    rule_id="RT-JUDGE-FAILED", source=source, severity="info", path=doc.rel, line=0,
                    message=f"judge did not return valid output for lines {start}-{start + len(chunk) - 1}: {err}",
                    why="The judge's output could not be checked against the schema, so it is recorded instead of trusted.",
                    false_positive="This is a tooling failure, not evidence about the file.",
                ))
                continue
            explanations.append(obj["explanation"])
            confs.append(float(obj["confidence"]))
            for s in obj["suspicious"]:
                if 1 <= s["line"] <= len(doc.lines):
                    merged.setdefault(s["line"], s)
        conf = max(confs) if confs else 0.0
        for ln, s in sorted(merged.items()):
            matched, ctx = with_context(doc.lines, ln)
            out.findings.append(Finding(
                rule_id=s["category"] if s["category"] != "OTHER" else "RT-JUDGE", source=source,
                severity=_severity(conf),
                path=doc.rel, line=ln, message=str(s.get("reason", ""))[:300],
                why="A model read this file as untrusted data and flagged this passage; it is one witness, not a verdict.",
                false_positive="Models over-read security vocabulary in documentation; check the line against the built-in and scanner findings.",
                matched=matched, context=ctx,
                extra={"judge_explanation": " ".join(explanations)[:1500], "confidence": conf, "model": model},
            ))
    return out
