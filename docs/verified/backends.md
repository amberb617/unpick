# Verified backend facts

One claim per line. "Fixture" means a run recorded under `tests/fixtures/backends/<backend>/` on 2026-10-18, under macOS `sandbox-exec` with `(deny network*)`, `env -i` (no API keys), and a Python audit hook logging `socket.getaddrinfo`/`socket.connect`.

Commits read:
- cisco-ai-defense/skill-scanner@8554b119bd118583f1a235e4e7aad8f2005ef904
- cisco-ai-defense/mcp-scanner@07cb5b085597d46c1e5fb829991d3c9d44787497
- NVIDIA/skillspector@cf5cac7ba5c756a6e0ebf52dc9763f49422f889f
- VirusTotal/yara-x@649cd3bb08e1c4ecc1524cc016c7aa27a75d2193
- anthropics/sandbox-runtime@626a59671ee2be556d70a290a8036224be996193
- LuD1161/agentjail@944df1c747f467c7f78dcd57547bbddc86c72b26

## 1. Cisco skill-scanner

- PyPI package is `cisco-ai-skill-scanner`; CLI entry point is `skill-scanner` — verified 2026-10-18 against cisco-ai-defense/skill-scanner@8554b11 (pyproject.toml:6, :166-167)
- Latest version is 2.3.0 (PyPI, and GitHub release 2.3.0 published 2026-10-15); `skill-scanner --version` prints `skill-scanner 2.3.0` — verified 2026-10-18 against https://pypi.org/pypi/cisco-ai-skill-scanner/json and the installed package
- Main is ahead of the 2.3.0 tag (tag commit e4e334f); flags below were also confirmed in the installed 2.3.0 `scan --help` — verified 2026-10-18 against cisco-ai-defense/skill-scanner@8554b11
- Maintainer is Cisco (pyproject `authors`); CODEOWNERS is `@cisco-ai-defense/skill-scanner-reviewers` — verified 2026-10-18 against cisco-ai-defense/skill-scanner@8554b11 (pyproject.toml:9-11, CODEOWNERS)
- License is Apache-2.0, "Copyright 2026 Cisco Systems, Inc. and its affiliates" — verified 2026-10-18 against cisco-ai-defense/skill-scanner@8554b11 (LICENSE, pyproject.toml:14)
- Offline static invocation: `skill-scanner scan <skill_dir> --format json` — verified 2026-10-18 against fixture skill-scanner/meta.json
- Every network analyzer is opt-in, so leaving these flags off disables them: `--use-llm`, `--use-virustotal` (and `--vt-upload-files`), `--use-aidefense`, `--use-osv`, `--enable-meta`, `--adjudicate`, `--system-one-endpoint` — verified 2026-10-18 against cisco-ai-defense/skill-scanner@8554b11 (README.md:324-348, skill_scanner/cli/cli.py:1249-1256)
- No `--no-llm`/`--offline` flag exists; offline means omitting the `--use-*` flags — verified 2026-10-18 against cisco-ai-defense/skill-scanner@8554b11 (skill_scanner/cli/cli.py add_argument list)
- Default analyzers that ran: `static_analyzer`, `bytecode`, `pipeline`, `correlation` — verified 2026-10-18 against fixture skill-scanner/output.json `analyzers_used`
- OSV analyzer is "Opt-in ... requires no API key" and posts to `https://api.osv.dev/v1/querybatch` — verified 2026-10-18 against cisco-ai-defense/skill-scanner@8554b11 (skill_scanner/core/analyzers/osv_analyzer.py:20, :218)
- The default static scan made zero DNS lookups or socket connects — verified 2026-10-18 against fixture skill-scanner/meta.json `observed_network_attempts: []`
- JSON top level: `skill_name`, `skill_path` (absolute), `is_safe`, `max_severity`, `findings_count`, `findings[]`, `scan_duration_seconds`, `duration_ms`, `analyzers_used`, `timestamp`, `scan_metadata` — verified 2026-10-18 against fixture skill-scanner/output.json
- Finding fields: `id`, `rule_id`, `category`, `severity`, `title`, `description` (message), `file_path`, `line_number`, `snippet`, `remediation`, `analyzer`, `metadata` — verified 2026-10-18 against fixture skill-scanner/output.json
- Exit 0 when findings exist but no `--fail-on-severity` is set (fixture had 3 HIGH findings, exit 0) — verified 2026-10-18 against fixture skill-scanner/meta.json
- Exit 1 = findings at or above `--fail-on-severity` (or a scan error); exit 2 = configuration error, such as a requested analyzer that could not be built — verified 2026-10-18 against cisco-ai-defense/skill-scanner@8554b11 (skill_scanner/cli/cli.py:79-83)
- On the defanged test skill it flagged the `base64 -d | bash` line three times (PIPELINE_TAINT_FLOW, YARA_SUSP_Lnx_EncodedShell_DecodeExec_Sep26, CORRELATED_OBFUSCATION_EXECUTION_FLOW, all HIGH). It did not flag the zero-width space or `example.invalid` — verified 2026-10-18 against fixture skill-scanner/output.json
- Labelled eval fixtures: 29 under `evals/skills/<category>/<case>/` and 3 under `evals/test_skills/{malicious,safe}/<case>/`, each with an `_expected.json` — verified 2026-10-18 against cisco-ai-defense/skill-scanner@8554b11 (evals/README.md)
- All 29 `evals/skills` cases carry `provenance.source: "first-party human-reviewed inert fixture"` and `provenance.license: "Apache-2.0"` — verified 2026-10-18 against cisco-ai-defense/skill-scanner@8554b11 (evals/skills/*/*/_expected.json)
- The 3 `evals/test_skills` cases with `_expected.json` (malicious/eicar-test, malicious/exfiltrator, safe/simple-formatter) have no provenance or license field and fall under the repo Apache-2.0 LICENSE. Six more `evals/test_skills` dirs have no `_expected.json` — verified 2026-10-18 against cisco-ai-defense/skill-scanner@8554b11
- The repo does not use the word "defanged"; it uses "inert". Whether every fixture is inert was not independently audited — UNVERIFIED

## 2. Cisco mcp-scanner

- PyPI package is `cisco-ai-mcp-scanner`; CLI is `mcp-scanner` — verified 2026-10-18 against cisco-ai-defense/mcp-scanner@07cb5b0 (pyproject.toml:9, :119-120)
- Latest version is 4.8.6 (pyproject, PyPI, and GitHub release v4.8.6 of 2026-10-07) — verified 2026-10-18 against cisco-ai-defense/mcp-scanner@07cb5b0 (pyproject.toml:10) and https://pypi.org/pypi/cisco-ai-mcp-scanner/json
- `mcp-scanner --version` is not a valid flag (argparse error) — verified 2026-10-18 against the installed package
- Maintainer is Cisco; CODEOWNERS is `@cisco-ai-defense/mcp-scanner-reviewers` — verified 2026-10-18 against cisco-ai-defense/mcp-scanner@07cb5b0 (pyproject.toml:12-13, CODEOWNERS)
- License is Apache-2.0 (LICENSE file; PyPI metadata `license` is empty) — verified 2026-10-18 against cisco-ai-defense/mcp-scanner@07cb5b0 (LICENSE)
- Offline invocation without starting a server: `mcp-scanner --analyzers yara --format raw static --tools <tools.json>`. Global flags must come before the subcommand — verified 2026-10-18 against cisco-ai-defense/mcp-scanner@07cb5b0 (README.md:190, :545-573) and fixture mcp-scanner/meta.json
- `--analyzers` defaults to `api,yara,llm`, so `--analyzers yara` must be explicit. Without keys, `llm` and `api` print a warning and are skipped in `static` mode — verified 2026-10-18 against cisco-ai-defense/mcp-scanner@07cb5b0 (mcpscanner/cli.py:1533-1537, :1753-1770)
- Expected tools.json shape: `{"tools":[{"name":..., "description":..., "inputSchema":{"type":"object","properties":{...}}}]}` (MCP `tools/list` output) — verified 2026-10-18 against cisco-ai-defense/mcp-scanner@07cb5b0 (README.md:575-586)
- `--format` choices: raw, summary, detailed, by_tool, by_analyzer, by_severity, table. `--raw`/`-r` also prints raw JSON — verified 2026-10-18 against cisco-ai-defense/mcp-scanner@07cb5b0 (mcpscanner/cli.py:1564-1566, :1630-1643)
- Raw JSON top level: `server_url`, `scan_results[]`, `requested_analyzers`. In static mode `server_url` holds the `--server-url` default `https://mcp.deepwiki.com/mcp`, but no connection is made — verified 2026-10-18 against fixture mcp-scanner/output.json and mcpscanner/cli.py:1582
- Per-tool result fields: `status`, `is_safe`, `tool_name`, `tool_description`, `item_type`, and `findings.yara_analyzer.{severity, threat_names[], threat_summary, total_findings, mcp_taxonomies[]}`. There is no rule id, file, or line field; the location is the tool name — verified 2026-10-18 against fixture mcp-scanner/output.json
- Exit 0 on completion even when `is_safe` is false (no fail-on flag in `static`); exit 1 on errors such as no analyzers available, no input files, or an exception during the scan — verified 2026-10-18 against cisco-ai-defense/mcp-scanner@07cb5b0 (mcpscanner/cli.py:1771-1793, :2649-2651) and fixture exit 0
- Network: importing litellm (pinned `litellm==1.93.2`) calls `getaddrinfo('raw.githubusercontent.com', 443)` to fetch the model cost map, even with `--analyzers yara` — verified 2026-10-18 against an audit-hook run without the env var, and cisco-ai-defense/mcp-scanner@07cb5b0 (pyproject.toml:33)
- `LITELLM_LOCAL_MODEL_COST_MAP=True` stops that fetch; with it set, the static yara run made zero network attempts — verified 2026-10-18 against fixture mcp-scanner/meta.json
- On the test tools.json it flagged `add_note` HIGH with CREDENTIAL HARVESTING and PROMPT INJECTION — verified 2026-10-18 against fixture mcp-scanner/output.json

## 3. NVIDIA SkillSpector

- Not published on PyPI (`https://pypi.org/pypi/skillspector/json` returns 404); install is from GitHub: `uv tool install git+https://github.com/NVIDIA/skillspector.git`. CLI is `skillspector` — verified 2026-10-18 against NVIDIA/skillspector@cf5cac7 (README.md:45, pyproject.toml:75-76)
- Because the name is not on PyPI, `pip install skillspector` would resolve to whoever registers it — UNVERIFIED as a live risk (noted only)
- Latest GitHub release is v2.13.0 (tag 091a509, 2026-10-16), on a branch that diverged from main (67 ahead, 937 behind). Main@cf5cac7 pyproject says 2.12.0 — verified 2026-10-18 against `gh api repos/nvidia/skillspector/compare/main...v2.13.0` and pyproject.toml:7
- Installed and recorded version: main@cf5cac7, `skillspector --version` prints `SkillSpector v2.12.0` — verified 2026-10-18 against fixture skillspector/meta.json
- Maintainer is NVIDIA (repo org); pyproject has no authors field and there is no CODEOWNERS file — verified 2026-10-18 against NVIDIA/skillspector@cf5cac7
- License is Apache-2.0 — verified 2026-10-18 against NVIDIA/skillspector@cf5cac7 (LICENSE, pyproject.toml:10)
- LLM off is `--no-llm` ("Skip LLM analysis (static only)"); it maps to `use_llm = not no_llm` and skips provider initialization — verified 2026-10-18 against NVIDIA/skillspector@cf5cac7 (README.md:784, :746; src/skillspector/cli.py:323-335)
- `--no-llm` is still the flag in release v2.13.0 — verified 2026-10-18 against NVIDIA/skillspector@v2.13.0 README.md:669
- Offline invocation: `skillspector scan <skill_dir> --no-llm --format json` (JSON goes to stdout when `-o` is not given) — verified 2026-10-18 against NVIDIA/skillspector@cf5cac7 (README.md:813-816) and fixture skillspector/meta.json
- OSV is still called with `--no-llm`. The README says SC4 "runs even with `--no-llm`" — verified 2026-10-18 against NVIDIA/skillspector@cf5cac7 (README.md:975)
- OSV code path: `static_patterns_supply_chain.py:3023-3031` ("# SC4: Live OSV.dev lookup, then static fallback" → `_sc4_from_osv_detailed(...)`) → `:2732 query_batch(pkg_pairs, ecosystem, budget=budget)` → `osv_client.py:667 httpx.Client(...)` → `:684-689 _request_json_bounded(client, "POST", _OSV_BATCH_URL, ...)` with `_OSV_BATCH_URL = "https://api.osv.dev/v1/querybatch"` (:42). Advisory details come from `_OSV_VULN_URL` `https://api.osv.dev/v1/vulns` (:43, :524) — verified 2026-10-18 against NVIDIA/skillspector@cf5cac7
- `query_batch` returns early with no request when no packages are found (`if not packages: return QueryBatchResults([])`) — verified 2026-10-18 against NVIDIA/skillspector@cf5cac7 (osv_client.py:564-592)
- Run against the test skill plus a `requirements.txt` (`requests==2.19.0`) with `--no-llm`, it called `getaddrinfo('api.osv.dev', 443)`. With network denied it fell back to the bundled list and still emitted SC4 HIGH — verified 2026-10-18 against an audit-hook probe in the scratchpad
- Without a dependency manifest (the recorded fixture), it made zero network attempts — verified 2026-10-18 against fixture skillspector/meta.json
- No flag or env var disables OSV. CLI flags are only baseline, exclude, fail-on-findings, fail-on-incomplete, format, host, mcp-registry(-compare), min-coverage, no-llm, output, port, reason, recursive, show-suppressed, transitive*, transport, use-shipped-baseline, verbose, version, yara-rules-dir. The only OSV env var is `SKILLSPECTOR_OSV_TIMEOUT` (a timeout, not an off switch) — verified 2026-10-18 against NVIDIA/skillspector@cf5cac7 (src/skillspector/cli.py, osv_client.py:45-53)
- Workaround: block network at the OS layer. OSV failure is non-fatal and falls back to a built-in list — verified 2026-10-18 against NVIDIA/skillspector@cf5cac7 (README.md:964, :967) and the probe above
- `--transitive` (opt-in) follows external references and is another network path; it was not exercised — verified 2026-10-18 against NVIDIA/skillspector@cf5cac7 (src/skillspector/nodes/report.py:560-583, src/skillspector/cli.py)
- JSON top level: `skill`, `risk_assessment{score,severity,recommendation,max_issue_severity}`, `components`, `structured_summaries`, `issues[]`, `suppressed_count`, `suppressed`, `metadata{llm_requested,skillspector_version,...}`, `execution_successful`, `analysis_completeness` — verified 2026-10-18 against fixture skillspector/output.json
- Issue fields: `id` (rule id, e.g. YR4/SC3/TM2/P2), `finding_id`, `category`, `pattern` (message), `severity`, `confidence`, `location{file,start_line,end_line,start_column?,end_column?}`, `finding`, `explanation`, `remediation`, `code_snippet` — verified 2026-10-18 against fixture skillspector/output.json and README.md:876 (`Finding.to_dict()` is authoritative)
- Exit 0 = score ≤ 50 (SAFE/CAUTION); 1 = score > 50 or a strict gate fired; 2 = error — verified 2026-10-18 against NVIDIA/skillspector@cf5cac7 (README.md:797-809)
- The fixture scored 75 HIGH (DO_NOT_INSTALL) and exited 1 — verified 2026-10-18 against fixture skillspector/meta.json and output.json
- It flagged the zero-width space (YR4 at SKILL.md:3 and P2 at :21) and the `base64 -d | bash` line (SC3, TM2 at :16) — verified 2026-10-18 against fixture skillspector/output.json

## 4. YARA-X

- License is BSD-3-Clause; copyright "The YARA-X Authors"; maintainer is VirusTotal — verified 2026-10-18 against VirusTotal/yara-x@649cd3b (LICENSE, Cargo.toml:8, AUTHORS)
- Latest version is 1.21.0 (workspace Cargo.toml, PyPI `yara-x`, GitHub release v1.21.0) — verified 2026-10-18 against VirusTotal/yara-x@649cd3b (Cargo.toml:2) and https://pypi.org/pypi/yara-x/json
- Python package name is `yara-x` (`pip install yara-x`), imported as `yara_x` — verified 2026-10-18 against VirusTotal/yara-x@649cd3b (py/pyproject.toml:6, site/content/docs/api/python.md:32)
- The `yr` CLI is not on PyPI. It ships as GitHub release binaries, `brew install yara-x`, or `cargo install --path cli` — verified 2026-10-18 against VirusTotal/yara-x@649cd3b (site/content/docs/intro/installation.md:24-47)
- Recorded binary: `yara-x-v1.21.0-aarch64-apple-darwin.tar.gz`, sha256 03ba0bc33552b324e9efd77852875779cc63f6c18d6e7b53665cb91aad67451a, which matches the GitHub release asset digest. `yr --version` prints `yara-x-cli 1.21.0` — verified 2026-10-18 against `gh release view v1.21.0 -R VirusTotal/yara-x`
- Scan invocation: `yr scan [OPTIONS] <RULES_PATH>... <TARGET_PATH>`. Rules may be a file or a directory of `*.yar`/`*.yara` files; `-r/--recursive` recurses into the target directory — verified 2026-10-18 against VirusTotal/yara-x@649cd3b (cli/src/commands/scan.rs, `yr scan --help`)
- Output flag: `-o/--output-format` with values `text` (default), `ndjson` (one object per file), `json` (one object at the end) — verified 2026-10-18 against VirusTotal/yara-x@649cd3b (cli/src/commands/scan.rs:30-38, :87)
- `--output-format json` shape: `{"version", "matches":[{"rule","file","meta"?,"tags"?,"strings"?:[{"identifier","offset","match","xor_key"?,"plaintext"?}]}]}`. `meta` needs `-m/--print-meta`, `strings` needs `-s/--print-strings`, and `tags` needs `-g/--print-tags` — verified 2026-10-18 against VirusTotal/yara-x@649cd3b (cli/src/commands/scan.rs:970-1000) and fixture yara-x/output.json
- `--output-format ndjson` shape per line: `{"path", "rules":[{"identifier","namespace"?,"meta"?,"tags"?,"strings"?}]}` — verified 2026-10-18 against VirusTotal/yara-x@649cd3b (cli/src/commands/scan.rs:600-630)
- Locations are byte `offset`s, not line numbers; `file` is printed as an absolute path. Severity exists only if the rule author puts it in `meta` — verified 2026-10-18 against fixture yara-x/output.json
- Exit 0 on success whether or not rules matched; 1 (`EXIT_ERROR`) on error — verified 2026-10-18 against VirusTotal/yara-x@649cd3b (cli/src/main.rs:28) and fixture exit 0 with 4 matches
- Network: the `yr` CLI has no HTTP client dependency, and the fixture ran with network denied — verified 2026-10-18 against VirusTotal/yara-x@649cd3b (cli/Cargo.toml) and fixture yara-x/meta.json
- Python API: `yara_x.compile(src) -> Rules`; `yara_x.Compiler().add_source(src, origin=None)` then `.build() -> Rules`; `yara_x.Scanner(rules)` with `.scan(data: bytes)`, `.scan_file(path)`, `.scan_with_options(...)`; `Rules.scan(data)`; `ScanResults.matching_rules -> tuple[Rule]`; `Rule.identifier/.namespace/.tags/.metadata/.patterns`; `Pattern.identifier/.matches`; `Match.offset/.length` — verified 2026-10-18 against VirusTotal/yara-x@649cd3b (py/yara_x.pyi:22-155, :264-297, :443-593) and a local run in the venv

## 5. Anthropic sandbox-runtime (`srt`)

- npm package is `@anthropic-ai/sandbox-runtime`, version 0.0.80 (npm latest and GitHub release v0.0.80 of 2026-10-16); bin is `srt`; author is Anthropic PBC; license Apache-2.0 — verified 2026-10-18 against anthropics/sandbox-runtime@626a596 (package.json) and https://registry.npmjs.org/@anthropic-ai/sandbox-runtime/latest
- Install: `npm install -g @anthropic-ai/sandbox-runtime` (as documented; under this repo's conventions use `pnpm add -g`) — verified 2026-10-18 against anthropics/sandbox-runtime@626a596 (README.md:14)
- Run a command: `srt <command>`, e.g. `srt echo "hello world"`; `srt --settings /path/to/srt-settings.json <command>`; `--debug` for logs — verified 2026-10-18 against anthropics/sandbox-runtime@626a596 (README.md:168-174)
- Network is denied by default. An empty `network.allowedDomains` means no network access, and with no settings file the default is no network — verified 2026-10-18 against anthropics/sandbox-runtime@626a596 (README.md:122, :177-179)
- Network-denied run: `srt --settings ./srt-settings.json <cmd>` with `"network": {"allowedDomains": [], "deniedDomains": []}` — verified 2026-10-18 against anthropics/sandbox-runtime@626a596 (README.md:80-93)
- Settings file path is `~/.srt-settings.json` by default, or the file named with `--settings`. Format is JSON with required top-level `network` and `filesystem` objects. A file that exists but is invalid makes srt fail rather than fall back — verified 2026-10-18 against anthropics/sandbox-runtime@626a596 (README.md:80, :174-193)
- Filesystem keys: `filesystem.denyRead`, `filesystem.allowRead` (wins over denyRead), `filesystem.allowWrite` (an empty array means no writes), `filesystem.denyWrite` (wins over allowWrite) — verified 2026-10-18 against anthropics/sandbox-runtime@626a596 (README.md:117-120, :532-537)
- Read-only config: `{"filesystem":{"denyRead":["~/.ssh"],"allowWrite":[],"denyWrite":[]},"network":{"allowedDomains":[],"deniedDomains":[]}}`. Writes are denied by default except the child's stdio, `/tmp/claude`, `~/.npm/_logs`, and `~/.claude/debug` — verified 2026-10-18 against anthropics/sandbox-runtime@626a596 (README.md:120, :539)
- Mechanism: `sandbox-exec` (Seatbelt) on macOS, bubblewrap plus network-namespace removal on Linux, and a host proxy for allowed domains — verified 2026-10-18 against anthropics/sandbox-runtime@626a596 (README.md:5, :108, :122-128)
- srt was not installed or run (per scope) — verified 2026-10-18 (not applicable)

## 6. agentjail

- Repo `LuD1161/agentjail` (Go module `github.com/LuD1161/agentjail`), maintainer LuD1161, license Apache-2.0, latest release v1.8.2 (2026-09-08) — verified 2026-10-18 against LuD1161/agentjail@944df1c (go.mod:1, LICENSE) and `gh release view -R LuD1161/agentjail`
- Disable daemon auto-update: `export AGENTJAIL_AUTO_UPDATE=false` — verified 2026-10-18 against LuD1161/agentjail@944df1c (README.md:594-596; read in internal/daemonapp/main.go)
- Disable all update checks (notifications and auto-update): `export AGENTJAIL_NO_UPDATE_CHECK=1` — verified 2026-10-18 against LuD1161/agentjail@944df1c (README.md:598-600; read in cmd/agentjail/updatecheck.go and internal/daemonapp/main.go)
- The daemon checks for updates about every 6 hours — verified 2026-10-18 against LuD1161/agentjail@944df1c (README.md:589)
- For launchd daemons, set the env var in `~/Library/LaunchAgents/com.agentjail.daemon.plist` `EnvironmentVariables`. For systemd, use `systemctl --user edit agentjail-daemon.service` → `Environment=AGENTJAIL_AUTO_UPDATE=false` — verified 2026-10-18 against LuD1161/agentjail@944df1c (README.md:602-616)
- Disable telemetry: `agentjail telemetry disable`, or `export AGENTJAIL_SEND_ANONYMOUS_USAGE_STATS=false` (also accepts `0`/`no`). Check with `agentjail telemetry status` — verified 2026-10-18 against LuD1161/agentjail@944df1c (README.md:1074-1080, docs/TELEMETRY.md:18-50; read in internal/telemetry/consent.go)
- Telemetry resolution order is env var → CI auto-detect (`CI=true`) → `~/.agentjail/telemetry.json` → default ON — verified 2026-10-18 against LuD1161/agentjail@944df1c (docs/TELEMETRY.md:21, :48-50)
- agentjail was not installed or run (per scope) — verified 2026-10-18 (not applicable)
