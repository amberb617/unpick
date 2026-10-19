# unpick

*Gird your loins. Then read the Markdown raw.*

unpick vets AI components on your own laptop before you trust them: agent skills
(SKILL.md folders), IDE rules files, MCP servers and their tool descriptions, and Claude Code plugins
and hooks. It is for people with no security team, no budget and no vendor accounts. It runs offline by
default, and it is fully useful with nothing else installed.

To unpick a seam is to take it apart stitch by stitch and see what was sewn in. unpick does that to a
Markdown file. It backs the BSides Cambridge talk "The Devil Wears Markdown".

## Threat model

**Who this protects:** one person or a small team with no security staff, installing AI components that
strangers wrote: skills, rules files, MCP servers, plugins and hooks.

**What it assumes about the component:** it may be hostile, and it may be written to look harmless to a
human and to a scanner: hidden Unicode, setup steps that ask you to paste a command, tool descriptions that
instruct the model, settings that switch off approvals or reroute your API traffic, and clean versions
that turn malicious on a later update.

**What it assumes about the tools:** every scanner misses things and flags honest files, and any model can
be talked out of a finding. So no single source decides, the judge is one witness, and every finding says
when it is a false positive.

**What it does not protect against:** a compromised machine, a malicious agent runtime itself, attacks
that only trigger outside a rehearsal, or anything already exfiltrated. It does not replace a sandbox or a
runtime guard (see "What unpick does not do").

## Install

```
pipx install .
```

Python 3.11 or later, on macOS, Linux or Windows 11 (PowerShell 7 or Windows PowerShell 5.1). Optional
extras: `pipx install '.[yara]'` for YARA-X, `'.[ui]'` for the local web UI (phase 2), `'.[watch]'` for
the watcher (phase 3), `'.[fallback]'` for the fallback judge runtime (see below).

## The five-minute triage, mapped to commands

| step | what you do | command | UI screen |
|---|---|---|---|
| 1. Who made it? | provenance: author, age, publisher matches the name | `unpick check <url or npm:pkg or pypi:pkg>` | Check |
| 2. Read the raw bytes | see what the model reads, not what the renderer shows | `unpick raw SKILL.md` | Scan (split view) |
| 3. Scan offline | built-in checks, plus any scanners and judge you have | `unpick scan <path>` | Scan |
| 4. First run in a box | no network, no real credentials | `unpick rehearse <path or check id>` | Rehearse |
| 5. Pin and re-check | lockfile, diff on update | `unpick lock`, `unpick verify`, `unpick outdated --online` | Verify |
| When it got through | contain, rotate, find out what happened | `unpick recover <component>` | Recover |

`unpick report <path> --html out.html` puts the scan, judge opinions, a saved rehearsal, your decisions
and (with `--inventory`) the inventory in one self-contained file that prints in black and white.

**Before install.** `unpick check` fetches into `~/.unpick/quarantine/` with nothing executed (git hooks,
fsmonitor and submodules off; archives checked for path traversal, links and zip bombs; npm and PyPI
downloads checked against the registry's digest), shows who made it, scans it, and `--approve <id>`
prints the install command (never runs it) and adds it to `unpick.lock.json`.

**The hook is the control, the watcher is the backstop.** `unpick hook install claude-code` (or `codex`,
`cursor`; `--dry-run` shows the settings change first, `uninstall` removes it) runs `check` before an agent
installs a skill, plugin or MCP server, or edits an MCP config, and blocks on unaccepted findings at or
above `--min-severity` (default high). It fails closed on installs it cannot check
(`UNPICK_HOOK_FAIL_OPEN=1` to allow them). A plugin install you type yourself is not a tool call, so no hook
sees it. `unpick watch` scans what lands in the agents' folders and notifies you; `--print-service
launchd|systemd|windows` prints a run-at-login recipe.

**First run in a box.** `unpick rehearse` copies the component into a throwaway home holding only fake
secrets, starts a disposable agent driven by the local Granite model inside Docker (no network, read-only
root, all capabilities dropped, no new privileges, process limit), gives it a harmless task (`--task`), and
records every file it opens, program it starts and connection it tries (strace inside the box, on every
host OS). It needs Docker, `unpick judges install fallback --online` and `unpick rehearse --build --online`
once. It is evidence, not proof: a component can behave differently outside the box, later, or only when a
task triggers it. In testing, demo sample A did nothing when asked to summarise a README, and piped base64
into bash when asked to use the skill.

Also: `unpick inventory` lists every AI component already on this machine and in this project,
`unpick decide <id> accept|reject|ask-author` records what you concluded about a finding, and
`unpick demo` writes the talk's demo kit. Every command takes `--json` and `--no-color`.

`unpick ui` opens a local web app on 127.0.0.1 (random port, localhost-only, per-launch token,
strict CSP, no external assets, works with Wi-Fi off). It calls the same functions as the CLI; every
screen exports the same JSON as `--json` and the same HTML as `--html FILE`. Screenshots at 1920x1080 are
in docs/screenshots/ui/.

Exit codes for `scan`: 0 clean, 1 unaccepted findings, 2 error (including "nothing was scanned"),
3 a requested backend or judge was unavailable.

## When it got through

`unpick recover <component>` (or `--all` when there is no single suspect; `--since 2026-10-17` sets the
window) runs the incident runbook in order:

1. **Contain.** Move the component into `~/.unpick/quarantine/incident-<time>/`, remove its entries from
   agent configs (each edited file is backed up first), and list running processes started from it.
   Without `--yes` this only prints exactly what it would do.
2. **Rotate.** Credentials and private files reachable from the agent's environment, as a checklist grouped
   by provider with the official rotation page for each. Names and locations only, never values.
3. **What the agents did.** The flight recorder plus Claude Code, Codex and Gemini CLI session logs for the
   window: commands that touched secrets, decoded or downloaded code, contacted hosts, or mentioned the
   component. Cursor keeps no tool-call log on disk; add the flight recorder as a hook (`unpick record`) so
   there is one.
4. **What changed on disk,** against the last lockfile and by modification time.
5. **Watch outbound connections from now on:** LuLu (macOS), OpenSnitch (Linux), Windows Firewall logging.
6. **Report** the component to the registry it came from.

It writes `incident-<time>.md`, a plain-language summary you can hand to someone more technical.

**If a credential stealer ran, rotation is not optional.** unpick cannot undo exfiltration. Recovery means
containment, rotation, and knowing what happened.

## A flag is a question, not a verdict

Every finding carries its rule id, its source (`builtin`, `backend:<name>`, `judge:<model>` or
`rehearse`), a severity, the matched line with three lines of context, one sentence on why it fires and
one on when it is a false positive. When several sources run, each finding says how many agreed. You
record a decision; accepted findings stay quiet until the matched line changes.

## When data leaves your machine

Nothing leaves the machine unless you pass the flag in this table or say yes to a consent prompt. There
is no telemetry, no auto-update and no version check.

| what you run | where it goes | what is sent |
|---|---|---|
| `unpick backends install <name> --online` | PyPI (and GitHub for SkillSpector) | a normal package download request |
| `unpick backends install <name> --docker --online` | Docker Hub and PyPI | image and package download requests |
| `unpick judges install fallback --online` | PyPI and GitHub (runtime), huggingface.co (model) | download requests for llama-cpp-python and one pinned model file (2.1 GB) |
| `scan --backends skillspector --online` | api.osv.dev (Google's OSV) | names and versions of the skill's dependencies, when it has a manifest. Without `--online` SkillSpector does not run; with `--boxed` the box blocks the call |
| `scan --backends jiffy --online` | Jiffy Labs API (commercial; the author's company) | file hashes, then the component's files if Jiffy has not seen those bytes. Needs a Jiffy account |
| `unpick check <url or registry ref>` (network on by default for this command; `--offline` skips provenance) | the git host, registry.npmjs.org, pypi.org / files.pythonhosted.org, api.github.com | the repository or package name; downloads it into quarantine |
| `unpick outdated --online` | registry.npmjs.org, pypi.org, api.github.com, the git host | the names of locked components; fetches new git versions into quarantine |
| `unpick rehearse --build --online` | Docker Hub, Debian mirrors, PyPI and GitHub | image and package downloads, once |
| `unpick rehearse --canary-dns <email or webhook>` | canarytokens.org (Thinkst) | a memo and the email address or webhook URL you give |
| the installed hook (`unpick hook install ...`) | whatever `check` contacts | runs `check` on what an agent is about to install |
| `scan --judge claude-code:<model>` | Anthropic, via the Claude Code CLI | the full content of every scanned file. Asks first, every session |
| `scan --judge gemini:<model>` | Google, via the Gemini CLI | the full content of every scanned file. Asks first, every session |
| `scan --judge api:<provider>` | the provider's API (Anthropic, OpenAI or xAI) | the full content of every scanned file. Asks first, every session. UNVERIFIED endpoints, see below |

Every other backend and judge runs locally: built-in checks, Cisco skill-scanner (static mode),
Cisco mcp-scanner (YARA on a saved tools file, with `LITELLM_LOCAL_MODEL_COST_MAP=True` so litellm does
not fetch its cost map), YARA-X, Apple Intelligence, Ollama, llama.cpp, LM Studio, MLX, Foundry Local and
the fallback judge. Local judges only ever talk to loopback addresses; a non-loopback URL is refused.

## Scanner backends (all optional)

| backend | maintainer | licence | network as invoked |
|---|---|---|---|
| cisco-skill-scanner | Cisco AI Defense | Apache-2.0 | none (no `--use-*` flags) |
| cisco-mcp-scanner | Cisco AI Defense | Apache-2.0 | none (`--analyzers yara`, static, saved tools file) |
| skillspector | NVIDIA | Apache-2.0 | OSV.dev, even with `--no-llm`; needs `--online` or `--boxed` |
| yara-x | VirusTotal | BSD-3-Clause | none; runs unpick's bundled rules |
| jiffy | Jiffy Labs (commercial) | MIT CLI, commercial service | Jiffy API; opt-in only, never a default |

`unpick backends` shows what is installed and the version each adapter was tested against.
`--boxed` runs scanners in a no-network box: Anthropic sandbox-runtime if installed (`pnpm add -g
@anthropic-ai/sandbox-runtime`, macOS and Linux), otherwise Docker with `--network none` and the target
mounted read-only, otherwise it refuses.

## Judges: the AI already on your machine

A judge is one witness, never the jury (docs/JUDGES.md). `unpick judges` lists what was found.
`--judge auto` picks the first on-device one, in this order: Apple Intelligence (macOS 26+, Apple
silicon), Ollama, llama.cpp, LM Studio, MLX, any loopback OpenAI-compatible server, Foundry Local, then
the fallback judge.

**Fallback judge for Windows and Linux.** When no other local model exists, unpick can use IBM
Granite 4.1 3B (Apache-2.0), run in-process on CPU by llama-cpp-python. No weights ship with unpick.
One opt-in command sets it up: `unpick judges install fallback --online` installs the llama-cpp-python
runtime into unpick's own environment (a prebuilt CPU wheel on Windows x64 and Linux, no compiler
needed; a source build on macOS, which needs the Xcode command line tools, because the published macOS
wheels are corrupt), then downloads one pinned 2.1 GB GGUF file from IBM's Hugging Face repository and
checks its SHA-256. A file that does not match is never loaded. Version 0.3.17 or later is required
(CVE-2026-27940).

Be clear about what it is: on the adversarial corpus Granite was fooled on three of four files, once by
obeying a planted "return an empty list" instruction. It is a witness of last resort, not a safety net.

Hosted judges (Claude Code CLI, Gemini CLI, an API key in your environment) are never used
automatically. Codex CLI and Grok CLI are detected but never used as judges, because neither can be
confirmed to run with zero tools.

## What unpick does not do

- It is not a runtime guard. To block risky tool calls while an agent runs, use agentjail
  (https://github.com/LuD1161/agentjail; turn off its telemetry and auto-update, see docs/DEFAULTS.md).
- It is not a sandbox. For the first run of anything, use Docker with `--network none` or Anthropic
  sandbox-runtime. unpick's `rehearse` (phase 3) uses those.
- It cannot prove something is safe. A clean scan means none of these checks fired.

## Limitations

- The built-in checks read prose and configuration well and code poorly. On Cisco's labelled eval set,
  which is mostly Python, they catch a minority of malicious cases; see docs/BENCHMARK.md.
- They flag a share of honest files too. That is why every finding explains when it is a false positive.
- On the adversarial corpus, Claude Code (hosted) caught every planted line; Apple Intelligence missed one
  file and Granite 4.1 3B missed three. `unpick judges` shows each judge's result next to it.
- A component can behave differently later (sleeper and rug-pull patterns). Re-check on every update.

UNVERIFIED items are listed in docs/VERIFIED.md and warned about at run time: the `api` judge tier's
provider endpoints, LM Studio's default port, Foundry Local's structured output, and nine inventory
locations.

## For the talk

- docs/HANDOUT-COMMANDS.md: the six no-install commands (macOS/Linux and PowerShell), tested on every OS.
- docs/SLIDES.md: what each slide shows, the command to reproduce it, the pinned commit and scanner versions.
- docs/BENCHMARK.md: false-positive and detection rates, and which judges the adversarial corpus fooled.
- `unpick demo`: the defanged demo kit, CC0.

## Licence

Apache-2.0. The demo kit and adversarial corpus are CC0. Vendored test corpora keep their own licences
(tests/fixtures/*/NOTICE.md and SOURCES.md).
