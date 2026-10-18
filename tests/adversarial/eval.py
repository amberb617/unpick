"""Run a judge tier against the adversarial corpus and record its raw answers.

    python tests/adversarial/eval.py apple-fm:system

Writes tests/fixtures/judges/<tier>.json. The contract tests replay those answers, so CI needs no model.
Hosted tiers send this corpus (synthetic, CC0) to their provider; you are asked first.
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

from runthrough import judges
from runthrough.checks import Doc

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "fixtures" / "judges"


def main(judge_id: str) -> int:
    tier = judge_id.partition(":")[0]
    mod = judges.tiers()[tier]
    raw: dict[str, list[str]] = {}
    real = mod.complete

    def recording(model, prompt, schema):
        text = real(model, prompt, schema)
        raw.setdefault(current, []).append(text)
        return text

    mod.complete = recording
    expected = json.loads((HERE / "expected.json").read_text(encoding="utf-8"))
    results = {}
    for name, exp in expected.items():
        current = name  # noqa: F841 - read by recording()
        doc = Doc.load(HERE / name, HERE)
        out = judges.run(judge_id, [doc])
        flagged = sorted({f.line for f in out.findings if f.rule_id != "RT-JUDGE-FAILED"})
        missed = [ln for ln in exp["planted"] if not any(abs(ln - f) <= 2 for f in flagged)]
        results[name] = {"flagged": flagged, "missed": missed, "errors": out.errors,
                         "failed": [f.message for f in out.findings if f.rule_id == "RT-JUDGE-FAILED"]}
    OUT.mkdir(parents=True, exist_ok=True)
    record = {"judge": judge_id, "date": date.today().isoformat(), "prompt_version": judges.PROMPT_VERSION,
              "results": results, "raw": raw, "reliable": all(not r["missed"] for r in results.values())}
    (OUT / f"{tier}.json").write_text(json.dumps(record, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(json.dumps({k: {"missed": v["missed"], "flagged": v["flagged"]} for k, v in results.items()}, indent=1))
    print("reliable:", record["reliable"])
    return 0 if record["reliable"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
