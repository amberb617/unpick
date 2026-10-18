"""Regenerate docs/BENCHMARK.md.

    python tests/benchmark.py [--backends installed]

Measures, on vendored corpora only (no network):
  * false-positive rate per built-in rule and per backend on the benign corpus (tests/fixtures/benign);
  * detection and false-positive rate on Cisco skill-scanner's labelled eval fixtures (tests/fixtures/cisco-evals);
  * judge reliability on the adversarial corpus, from recordings in tests/fixtures/judges.

A file counts as "flagged" by a source when that source reports at least one finding of severity
medium or high in it. Low and info findings are questions worth a glance, not alarms.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import date
from pathlib import Path

from unpick import scan
from unpick.checks import all_checks

HERE = Path(__file__).resolve().parent
BENIGN = HERE / "fixtures" / "benign"
CISCO = HERE / "fixtures" / "cisco-evals"
JUDGES = HERE / "fixtures" / "judges"
OUT = HERE.parent / "docs" / "BENCHMARK.md"
ALARM = {"medium", "high"}


def _flagged(findings, key) -> dict[str, set[str]]:
    out = defaultdict(set)
    for f in findings:
        if f.severity in ALARM:
            out[key(f)].add(f.path.split("/")[0] if "/" in f.path else f.path)
    return out


def benign_rates(backends):
    files = [p for p in sorted(BENIGN.rglob("*.md")) if p.name != "SOURCES.md"]
    by_rule, by_source = defaultdict(set), defaultdict(set)
    sources = {"builtin"}
    for p in files:
        res = scan.scan(p, backends=backends, decision_files=[])
        sources |= set(res.sources)
        for f in res.findings:
            if f.severity in ALARM:
                by_source[f.source].add(p)
                if f.source == "builtin":
                    by_rule[f.rule_id].add(p)
    return len(files), by_rule, by_source, sorted(sources)


def cisco_rates(backends):
    rows = []
    for exp in sorted(CISCO.rglob("_expected.json")):
        meta = json.loads(exp.read_text(encoding="utf-8"))
        res = scan.scan(exp.parent, backends=backends, decision_files=[])
        hit = defaultdict(bool)
        for f in res.findings:
            if f.severity in ALARM and f.path != "_expected.json":
                hit[f.source] = True
        rows.append((meta.get("case_id", exp.parent.name), meta.get("package_label", "?"), dict(hit), res.sources))
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--backends", default="")
    args = ap.parse_args()
    from unpick import backends as be
    names = [r["name"] for r in be.describe() if r["installed"] and not r["needs_online"]] if args.backends == "installed" else [
        b for b in args.backends.split(",") if b]

    n, by_rule, by_source, sources = benign_rates(names)
    cisco = cisco_rates(names)
    lines = [
        "# Benchmark", "",
        f"Generated {date.today().isoformat()} by `python tests/benchmark.py{' --backends installed' if names else ''}`. "
        "Offline; vendored corpora only. A file is *flagged* by a source when it reports at least one medium or "
        "high finding there. Small corpora: read these as directions, not as precise rates.", "",
        "## False positives on real benign files", "",
        f"{n} files: Apache-2.0 skills from anthropics/skills and MIT instruction files from github/awesome-copilot "
        "(tests/fixtures/benign/SOURCES.md).", "",
        "| source | files flagged | rate |", "|---|---|---|",
    ]
    for s in sources:
        k = len(by_source.get(s, ()))
        lines.append(f"| {s} | {k} of {n} | {k / n:.0%} |")
    lines += ["", "### Per built-in rule", "", "| rule | files flagged | rate |", "|---|---|---|"]
    for mod in all_checks():
        k = len(by_rule.get(mod.RULE_ID, ()))
        lines.append(f"| {mod.RULE_ID} | {k} of {n} | {k / n:.0%} |")

    labels = sorted({r[1] for r in cisco})
    all_sources = sorted({s for r in cisco for s in r[3]})
    lines += ["", "## Cisco skill-scanner labelled eval fixtures", "",
              f"{len(cisco)} cases from cisco-ai-defense/skill-scanner @8554b11 (tests/fixtures/cisco-evals/NOTICE.md). "
              "For malicious cases the rate is detection; for benign cases it is false positives.", "",
              "| source | " + " | ".join(labels) + " |", "|---|" + "---|" * len(labels)]
    for s in all_sources:
        cells = []
        for lab in labels:
            cases = [r for r in cisco if r[1] == lab and s in r[3]]
            k = sum(r[2].get(s, False) for r in cases)
            cells.append(f"{k} of {len(cases)}" if cases else "-")
        lines.append(f"| {s} | " + " | ".join(cells) + " |")

    lines += ["", "## Judges on the adversarial corpus", "",
              "Each corpus file plants a problem and tells the judge to report nothing (tests/adversarial). "
              "A tier is **unreliable** if it misses any planted line.", "",
              "| judge | recorded | reliable | missed |", "|---|---|---|---|"]
    for rec_path in sorted(JUDGES.glob("*.json")):
        rec = json.loads(rec_path.read_text(encoding="utf-8"))
        missed = "; ".join(f"{k} line {v['missed']}" for k, v in rec["results"].items() if v["missed"]) or "none"
        lines.append(f"| {rec['judge']} | {rec['date']} | {'yes' if rec['reliable'] else '**unreliable**'} | {missed} |")
    lines += ["", "Hosted judges (Claude Code, Gemini CLI, API keys) have not been recorded: recording sends the corpus to "
              "the provider, so run `python tests/adversarial/eval.py <judge-id>` yourself and commit the result. "
              "Codex CLI and Grok CLI are never used as judges (they cannot be confirmed to run with zero tools).", ""]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(OUT.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
