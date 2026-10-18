# runthrough demo kit (CC0-1.0)

Everything here is safe to open, scan and project. Nothing in it runs anything.

- `sample-a/SKILL.md`: a defanged look-alike of a ClawHavoc skill. Three planted problems:
  a fake Prerequisites step, a base64-to-shell line (decodes to `echo "hello from the runthrough demo"`),
  and a line with hidden Unicode tag characters.
- `sample-b/SKILL.md`: a benign skill that gets flagged because it warns against committing a dotenv file.
- `tools.json`: one MCP tool whose description is poisoned in the style of Invariant Labs' proof of concept.
- `run.sh` / `run.ps1`: reproduce slides 18, 19 and B2 with no network.
- `accepted.decisions.json`: accepts every planted finding, so `runthrough scan . --decisions accepted.decisions.json`
  exits 0. Edit any planted line and its finding fires again.

Sources: ClawHavoc (Koi Security via eSecurityPlanet; Unit 42), Invariant Labs mcp-injection-experiments.
