#!/bin/sh
# Runs the three macOS/Linux handout commands from docs/HANDOUT-COMMANDS.md on demo sample A and checks
# that each one finds the planted problem. Usage: sh tests/handout/handout.sh demo/sample-a
set -u
cd "$1"
echo "== $(uname -s) $(uname -m), $(bash --version | head -1)"
echo '--- 1 reveal hidden characters'
LC_ALL=C cat -v SKILL.md | grep -n 'M-' > /tmp/h1 ; cut -c1-58 /tmp/h1
echo '--- 2 invisible Unicode'
bash -c "LC_ALL=C grep -nE \$'\\xe2\\x80[\\x8b-\\x8f\\xaa-\\xae]|\\xf3\\xa0' SKILL.md" > /tmp/h2 ; LC_ALL=C cut -c1-40 /tmp/h2
echo '--- 3 red-flag words'
grep -niE \
 'prereq|\| *(ba)?sh|base64|\.ssh|\.env|tell the user' \
 SKILL.md > /tmp/h3 ; cut -c1-58 /tmp/h3
grep -q '^24:' /tmp/h1 && grep -q '^24:' /tmp/h2 && grep -q '^12:' /tmp/h3 && grep -q '^17:' /tmp/h3 && echo OK
