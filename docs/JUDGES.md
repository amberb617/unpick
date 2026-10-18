# Judges: a witness, not a jury

A judge is a language model that reads a file and says what it thinks the file would make an agent do.
It is useful because it can read intent in plain English, which pattern rules cannot. It is also the
easiest part of runthrough to fool, because the file it reads was written by the person you are worried
about. So runthrough treats a judge's opinion as one vote, shown with a judge badge, and never as the
reason on its own for calling something safe or unsafe.

## How the judge is protected from the file

- The file is wrapped in a block fenced by a random marker that changes every call, so the file cannot
  fake the end of the block. The prompt says nothing inside the block is addressed to the judge.
- The judge has no tools and no file access. Agent CLIs that cannot be confirmed to run with zero tools
  (Codex CLI, Grok CLI) are never used as judges.
- The answer must match a fixed JSON schema: suspicious lines with a category, one paragraph of
  explanation, and a confidence. An answer that does not fit is retried once and then recorded as a
  failed judgement, never trusted.
- Temperature 0, so the same file gives the same answer.
- An adversarial corpus (tests/adversarial) plants real problems in files that also tell the judge to
  report nothing. A judge that misses any planted line is marked unreliable in docs/BENCHMARK.md.

## Why on-device comes first

An on-device judge sends nothing anywhere. A hosted judge sends the full text of every scanned file to a
company, which is a real cost when the file is a private rules file or an unreleased skill. So
`--judge auto` only ever picks an on-device judge, and every hosted judge asks for consent each session,
naming the provider and saying the full content will be sent.

## What the results say so far

The Apple Intelligence judge flagged planted problems in three of four adversarial files and missed a
base64-to-shell line in the fourth, where a hidden note told it the line was safe. The built-in checks
caught all four. That is the point: no single witness is enough.
