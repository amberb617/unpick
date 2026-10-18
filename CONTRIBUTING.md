# Contributing

The code is meant to be read by a curious non-expert: short modules, one check per file, one scanner
adapter per file, one judge tier per file, each with a docstring that explains the attack or tool and
cites a public write-up.

Before a pull request: `pytest`, `ruff check unpick tests`, and `unpick scan .` (it must stay clean;
see tests/test_dogfood.py). If you add a network call anywhere, add it to the README table
"When data leaves your machine" in the same change.

## Add a built-in check

Create `unpick/checks/<name>.py` with `RULE_ID`, `TITLE`, `SEVERITY`, `WHY` (one sentence: why it
fires), `FALSE_POSITIVE` (one sentence: when it is wrong), optional `applies(doc)`, and `run(doc)`
yielding `Hit(line, message, severity=None, extra={})`. Add a positive and a negative case to
tests/test_checks.py. Put pattern lists in `data/` with a source comment on every entry.

## Add a scanner backend

Create `unpick/backends/<name>.py` defining `NAME, MAINTAINER, LICENSE, HOMEPAGE, TESTED_VERSION,
INSTALL, NETWORK, NEEDS_ONLINE`, `applies(target)`, `version()`, `command(target)` and
`parse(stdout, target)`. Use the scanner's offline mode only. Record its real output on a defanged input
under `tests/fixtures/backends/<name>/` (input, output.json, meta.json with argv, version, date) and add it
to tests/test_backends_contract.py, so CI never needs the scanner installed. Add each flag and behaviour
you rely on to docs/VERIFIED.md with the commit you checked.

## Add a judge tier

Create `unpick/judges/<name>.py` defining `NAME`, `KIND` ("on-device" or "hosted"), `PROVIDER` for
hosted tiers, `detect()` and `complete(model, prompt, schema)`. A hosted tier must run with zero tools;
if that cannot be confirmed, `detect()` returns it with `usable: False` and the reason. Run
`python tests/adversarial/eval.py <tier>:<model>` and commit the recording under tests/fixtures/judges/.
