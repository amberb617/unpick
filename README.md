# unpick

*Gird your loins. Then read the Markdown raw.*

unpick vets AI components on your own laptop before you trust them: agent skills
(SKILL.md folders), IDE rules files, MCP servers and their tool descriptions, and Claude Code plugins
and hooks. It is for people with no security team, no budget and no vendor accounts. It runs offline by
default, and it is fully useful with nothing else installed.

To unpick a seam is to take it apart stitch by stitch and see what was sewn in. unpick does that to a
Markdown file. It backs the BSides Cambridge talk "The Devil Wears Markdown".

## Install

```
pipx install .
```

Python 3.11 or later, on macOS, Linux or Windows 11 (PowerShell 7 or Windows PowerShell 5.1). Optional
extras: `pipx install '.[yara]'` for YARA-X, `'.[ui]'` for the local web UI (phase 2), `'.[watch]'` for
the watcher (phase 3), `'.[fallback]'` for the fallback judge runtime (see below).

## The five-minute triage, mapped to commands

| step | what you do | command |
|---|---|---|
| 1. Who made it? | provenance: author, age, publisher matches the name | `unpick check <url>` (phase 3) |
| 2. Read the raw bytes | see what the model reads, not what the renderer shows | `unpick raw SKILL.md` |
| 3. Scan offline | built-in checks, plus any scanners and judge you have | `unpick scan <path>` |
| 4. First run in a box | no network, no real credentials | `unpick rehearse <path>` (phase 3) |
| 5. Pin and re-check | lockfile, diff on update | `unpick lock` / `verify` (phase 3) |

Also: `unpick inventory` lists every AI component already on this machine and in this project,
`unpick decide <id> accept|reject|ask-author` records what you concluded about a finding, and
`unpick demo` writes the talk's demo kit. Every command takes `--json` and `--no-color`.

`unpick ui` opens a local web app on 127.0.0.1 (random port, localhost-only, per-launch token,
strict CSP, no external assets, works with Wi-Fi off). It calls the same functions as the CLI; every
screen exports the same JSON as `--json` and the same HTML as `--html FILE`. Screenshots at 1920x1080 are
in docs/screenshots/ui/.

Exit codes for `scan`: 0 clean, 1 unaccepted findings, 2 error (including "nothing was scanned"),
3 a requested backend or judge was unavailable.

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

## Licence

Apache-2.0. The demo kit and adversarial corpus are CC0. Vendored test corpora keep their own licences
(tests/fixtures/*/NOTICE.md and SOURCES.md).
