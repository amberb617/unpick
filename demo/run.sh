#!/bin/sh
# Reproduces slides 18, 19 and B2 of "The Devil Wears Markdown". Makes no network calls.
# Set RT_BACKENDS=installed to add every installed offline scanner, e.g. RT_BACKENDS=installed ./run.sh
set -u
cd "$(dirname "$0")"
B="${RT_BACKENDS:+--backends $RT_BACKENDS}"
pause() { printf '\n[enter] '; read -r _ || true; }

echo "== Slide 18: sample A. Rendered, it looks clean. Raw, it does not. =="
unpick raw sample-a/SKILL.md
pause
unpick scan sample-a --no-decisions $B
pause

echo "== Slide 19: sample B. A flag is a question, not a verdict. =="
unpick scan sample-b --no-decisions $B
pause
unpick decide --rule RT-SENSITIVE-PATH --file SKILL.md accept --note "benign: the skill warns against committing secrets" --decisions-file .unpick/demo-decisions.json
unpick scan sample-b --decisions .unpick/demo-decisions.json $B
pause

echo "== Slide B2: a poisoned MCP tool description, read without starting any server =="
unpick scan tools.json --no-decisions $B
