# Slides: what each one shows and how to reproduce it

Generated 2026-10-19 by `python tests/slides.py` from unpick 0.2.0 at commit `7cd13e1f064a518651f4033db37a26dfdf320ccb`.
Screenshots are 2x PNGs (3840x2160 for full screens) in docs/screenshots/. The demo kit is regenerated
fresh with `unpick demo`; no personal paths appear.

| slide | what it shows | reproduce | screenshot |
|---|---|---|---|
| 17 | Run the check where it can't hurt you: every source that ran, its version, local, network none | `unpick ui`, Scan screen, `sample-a`, Installed scanners on | screenshots/slide-17.png |
| 18 | Sample A rendered vs raw: the three planted lines, the hidden sentence decoded | `unpick raw demo/sample-a/SKILL.md` or the Scan screen | screenshots/slide-18.png |
| 19 | Sample B: a flag is a question, accepted with a note | `unpick scan demo/sample-b`, then `unpick decide <id> accept --note ...` | screenshots/slide-19.png |
| 23 | Reading the raw bytes with no install (macOS / Linux; PowerShell in docs/HANDOUT-COMMANDS.md) | the three commands in docs/HANDOUT-COMMANDS.md | screenshots/slide-23.png |
| 25 | Free, open source, offline-capable: maintainer, licence and network behaviour of each scanner | `unpick backends`, or the Settings screen | screenshots/slide-25.png |
| B2 | A poisoned MCP tool description read without starting any server | `unpick scan demo/tools.json --backends installed` | screenshots/slide-B2.png |

Also in docs/screenshots/ui/ (from the Playwright tests): rehearse.png (the box run of sample A),
check.png, verify.png, recover.png, scan-light.png and scan-dark.png.

## Scanner versions used

| backend | version found | adapter tested against | maintainer |
|---|---|---|---|
| cisco-mcp-scanner | mcp-scanner 4.8.6 | 4.8.6 | Cisco AI Defense |
| cisco-skill-scanner | skill-scanner 2.3.0 | 2.3.0 | Cisco AI Defense |
| yara-x | yara-x-cli 1.21.0 | 1.21.0 | VirusTotal |
