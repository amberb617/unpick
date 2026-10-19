# Verified phase 3 facts

One claim per line. "Live" means a request made on 2026-10-18 from this machine with no credentials. "Box test" means a run on Docker 27.4.0 (Colima, linux/aarch64, kernel 6.8.0-50) on 2026-10-18, using a throwaway image built from `python:3.12-slim` plus apt `strace inotify-tools`. That image was deleted after the run.

Commits and versions read:
- npm/registry@ae49abf1bac0ec1a3f3f1fceea1cca6fe2dc00e1 (docs/REGISTRY-API.md, docs/responses/package-metadata.md)
- gorakhargosh/watchdog@a98cad12b0ddcdd1fc2b35c6e5defc3a7be35226 (PyPI latest 6.0.0)
- abetlen/llama-cpp-python@1652066e0af45f2313b339670ef9555e8a54e545 (tag v0.3.36)
- huggingface.co ibm-granite/granite-4.1-3b-GGUF@ab4701481089b58a082ef63cc1cee738887293ff
- thinkst/canarytokens@8684b6db5f965a557c154fac5f29dfa252be5773
- Claude Code 2.1.303 (`claude --version`)

## 1. Provenance APIs (unauthenticated)

### GitHub REST

- `GET https://api.github.com/repos/cli/cli` returns 200 with `full_name`, `created_at` (`2019-10-03T15:24:53Z`), `stargazers_count`, `forks_count`, `pushed_at`, `default_branch` (`trunk`) and `owner.login`/`owner.type` (`Organization`) — verified 2026-10-18 against live api.github.com/repos/cli/cli
- A transferred or renamed repo returns `301` with `Location: https://api.github.com/repositories/<id>` and body `{"message":"Moved Permanently","url":...}`. Following the redirect gives the new `full_name`. For example `zeit/next.js` resolves to `vercel/next.js`, and `jakubroztocil/httpie` returns 301 — verified 2026-10-18 against live api.github.com/repos/zeit/next.js and https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api#follow-redirects
- The redirect is to `/repositories/<numeric id>`, not to `/repos/<new owner>/<new name>`, so the code must follow it (`curl -L`, `urllib` follows by default) and read `full_name` from the final body — verified 2026-10-18 against live api.github.com
- A missing repo returns `404` with no redirect — verified 2026-10-18 against live api.github.com/repos/github/hub-test-nonexist
- `/repos/{o}/{r}/contributors` items carry `login`, `id`, `type`, `contributions` — verified 2026-10-18 against live api.github.com/repos/cli/cli/contributors
- `/repos/{o}/{r}/releases` items carry `tag_name`, `author`, `created_at`, `published_at`, `draft`, `prerelease`, `immutable`, `assets`, `tarball_url` — verified 2026-10-18 against live api.github.com/repos/cli/cli/releases
- `/repos/{o}/{r}/tags` items carry `name`, `commit` (`sha`, `url`), `tarball_url`, `zipball_url` — verified 2026-10-18 against live api.github.com/repos/cli/cli/tags
- `/repos/{o}/{r}/commits?per_page=1` items carry `sha`, `commit` (author/committer/message), `author`, `committer`, `parents` — verified 2026-10-18 against live api.github.com/repos/cli/cli/commits
- With `per_page=1`, the `Link` header's `rel="last"` page number equals the total count (cli/cli: 12363 commits, 205 releases, 205 tags, 190 contributor pages at per_page=2). This is the cheap way to count without paging — verified 2026-10-18 against live api.github.com/repos/cli/cli/commits?per_page=1
- The unauthenticated primary rate limit is 60 requests per hour per originating IP. Headers are `x-ratelimit-limit`, `x-ratelimit-remaining`, `x-ratelimit-used`, `x-ratelimit-reset` and `x-ratelimit-resource` — verified 2026-10-18 against https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api and live headers (`x-ratelimit-limit: 60`)
- `GET /rate_limit` reports `resources.core` and does not count against the limit — UNVERIFIED (called once; did not measure whether it decremented)

### npm registry

- `https://registry.npmjs.org/<pkg>` top-level keys include `name`, `time`, `maintainers`, `dist-tags`, `versions`, `repository`, `author` — verified 2026-10-18 against live registry.npmjs.org/left-pad
- `time` maps `created`, `modified` and each version to an ISO timestamp — verified 2026-10-18 against live registry.npmjs.org/left-pad and npm/registry@ae49abf docs/responses/package-metadata.md:238
- `versions[v].dist` has `tarball`, `integrity` (`sha512-<base64>`), `shasum` (sha1 hex), `fileCount`, `unpackedSize`, `signatures` — verified 2026-10-18 against live registry.npmjs.org/left-pad (1.3.0)
- `dist.integrity` is SRI form `<alg>-<base64>`, present since April 2017 — verified 2026-10-18 against npm/registry@ae49abf docs/responses/package-metadata.md:152
- `sha512-` + base64(sha512(tarball bytes)) equals `dist.integrity` for left-pad 1.3.0 — verified 2026-10-18 by live download and `openssl dgst -sha512 -binary | base64`
- `versions[v]._npmUser` is `{name, email}` of the account that published that version — verified 2026-10-18 against npm/registry@ae49abf docs/REGISTRY-API.md:68 and live left-pad
- Trusted-publishing versions have `_npmUser.trustedPublisher` (`{id: "github", oidcConfigId}`) and `dist.attestations` (`{url, provenance: {predicateType: "https://slsa.dev/provenance/v1"}}`) — verified 2026-10-18 against live registry.npmjs.org/esbuild (0.28.2)
- `repository` is `{type, url}` copied from package.json and is not validated by the registry — verified 2026-10-18 against npm/registry@ae49abf docs/REGISTRY-API.md:47 and docs/responses/package-metadata.md:135
- There is no field that records a maintainer change. It has to be derived by diffing `versions[v]._npmUser.name` and `versions[v].maintainers[].name` across versions in `time` order. left-pad shows publisher `westlac` up to 1.0.2, then `stevemao` from 1.1.0, and `npm` for the 2016 republished 0.0.x — verified 2026-10-18 against live registry.npmjs.org/left-pad
- The abbreviated document (`Accept: application/vnd.npm.install-v1+json`) adds `hasInstallScript` per version, which the full document lacks. esbuild 0.28.2 shows `true` (`scripts.postinstall: "node install.js"`) — verified 2026-10-18 against npm/registry@ae49abf docs/responses/package-metadata.md:11,256 and live registry.npmjs.org/esbuild
- Downloading a tarball with no install scripts run: a plain HTTP GET of `dist.tarball`, then checking `dist.integrity`. No npm client is involved — verified 2026-10-18 by live download of https://registry.npmjs.org/left-pad/-/left-pad-1.3.0.tgz
- `npm pack <name>@<version> --ignore-scripts` as an alternative — UNVERIFIED (not run; plain GET is sufficient)

### PyPI JSON API

- `https://pypi.org/pypi/<p>/json` top-level keys: `info`, `last_serial`, `ownership`, `releases`, `urls`, `vulnerabilities` — verified 2026-10-18 against live pypi.org/pypi/requests/json
- `/pypi/<p>/<v>/json` returns the same keys minus `releases` — verified 2026-10-18 against live pypi.org/pypi/requests/2.32.3/json
- `info` holds `author`, `author_email`, `maintainer`, `maintainer_email`, `project_urls`, `home_page`, `version`, `yanked`, `yanked_reason` (requests: `author` null, `author_email` "Kenneth Reitz <...>", `project_urls.Source` https://github.com/psf/requests) — verified 2026-10-18 against live pypi.org/pypi/requests/json
- `ownership` is `{organization, roles: [{role: "Owner"|"Maintainer", user}]}`, giving the PyPI account names (requests: Lukasa, graffatcolmingov, nateprewitt) — verified 2026-10-18 against live pypi.org/pypi/requests/json and https://docs.pypi.org/api/json/
- Each `urls[]` file has `filename`, `url` (files.pythonhosted.org), `digests` (`sha256`, `md5`, `blake2b_256`), `upload_time`, `upload_time_iso_8601`, `packagetype`, `size`, `yanked` — verified 2026-10-18 against live pypi.org/pypi/requests/json
- `releases` is deprecated in favour of the Index API, `downloads` is always -1 and `has_sig` is always false — verified 2026-10-18 against https://docs.pypi.org/api/json/
- The JSON Simple API (`Accept: application/vnd.pypi.simple.v1+json` on `/simple/<p>/`) returns 200 — verified 2026-10-18 against live pypi.org/simple/requests/

## 2. Claude Code hooks

- Hooks live under `"hooks"` in `~/.claude/settings.json` (user), `.claude/settings.json` (project), `.claude/settings.local.json`, managed policy, plugin `hooks/hooks.json`, and skill/subagent frontmatter. All levels merge — verified 2026-10-18 against https://code.claude.com/docs/en/hooks
- Config shape: `{"hooks":{"PreToolUse":[{"matcher":"Bash","hooks":[{"type":"command","command":"...","timeout":30}]}]}}`. `timeout` is in seconds, default 600 for `command` — verified 2026-10-18 against https://code.claude.com/docs/en/hooks
- PreToolUse stdin JSON: `session_id`, `transcript_path`, `cwd`, `permission_mode`, `hook_event_name: "PreToolUse"`, `tool_name`, `tool_input`, `tool_use_id`, plus `prompt_id` and `scratchpad_dir`. Inside a subagent it also has `agent_id` and `agent_type` — verified 2026-10-18 against https://code.claude.com/docs/en/hooks
- `tool_input` for Bash is `{command, description, timeout, run_in_background}`. PowerShell has the same shape. Write is `{file_path, content}`. Edit is `{file_path, old_string, new_string, replace_all}` — verified 2026-10-18 against https://code.claude.com/docs/en/hooks
- On Windows the Bash tool may not be registered (no Git Bash), so shell matchers should be `Bash|PowerShell`. File paths arrive with backslashes — verified 2026-10-18 against https://code.claude.com/docs/en/hooks
- Exit 2 blocks the call and stderr becomes the reason shown to Claude. Any other non-zero exit is a non-blocking error and the call proceeds. A timeout does not block. Exit 0 with no output is "no decision", not approval — verified 2026-10-18 against https://code.claude.com/docs/en/hooks
- JSON deny on exit 0: `{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"..."}}`. Values are `allow|deny|ask|defer`. stdout must contain only the JSON — verified 2026-10-18 against https://code.claude.com/docs/en/hooks
- Matcher: `"*"`, `""` or omitted matches all. A string of only `[A-Za-z0-9_\- ,|]` is an exact name or a `|`/`,` list. Anything else is an unanchored JS regex. MCP tools are `mcp__<server>__<tool>` and need `.*` (e.g. `mcp__.*`) — verified 2026-10-18 against https://code.claude.com/docs/en/hooks
- Optional `"if": "Bash(claude mcp *)"` field uses permission-rule syntax, one rule per entry — verified 2026-10-18 against https://code.claude.com/docs/en/hooks
- A shell-run `claude mcp add ...` reaches PreToolUse as `tool_name: "Bash"` with the full string in `tool_input.command`. This is observed: an existing user PreToolUse Bash hook on this machine blocked this research session's own `claude mcp add --help` call by matching the command text — verified 2026-10-18 by observation in this session
- The MCP add command writes to `~/.claude.json` (`--scope local|user`) or `.mcp.json` (`--scope project`) — verified 2026-10-18 against local `claude mcp add --help` (Claude Code 2.1.303) and https://code.claude.com/docs/en/mcp
- `npx skills add ...` is a Bash tool call (`tool_input.command`). The npm package `skills` (vercel-labs/skills, latest 1.7.2) exposes bins `skills` and `add-skill` — verified 2026-10-18 against live registry.npmjs.org/skills
- Edits to `.mcp.json` or `~/.claude.json` through Edit/Write arrive as `tool_name: "Edit"|"Write"` with `tool_input.file_path` — verified 2026-10-18 against https://code.claude.com/docs/en/hooks (Write/Edit input tables)
- `/plugin install` typed by the user is not a tool call. In a session it opens the `/plugin` panel rather than installing — verified 2026-10-18 against https://code.claude.com/docs/en/discover-plugins
- `UserPromptExpansion` fires for prompt-type commands (skills, custom commands, MCP prompts) and is how to catch a typed `/skillname`, which bypasses PreToolUse — verified 2026-10-18 against https://code.claude.com/docs/en/hooks
- `UserPromptExpansion` also fires for the built-in `/plugin` command — UNVERIFIED (the docs scope it to prompt-type commands; `/plugin` is built-in, so probably not)
- `claude plugin install <name>@<marketplace>` exists as a shell command. When Claude runs it, it is a Bash tool call — verified 2026-10-18 against local `claude plugin install --help`
- `ConfigChange` sources are `user_settings`, `project_settings`, `local_settings`, `policy_settings`, `skills`. `.mcp.json` and `~/.claude.json` are not listed — verified 2026-10-18 against https://code.claude.com/docs/en/hooks
- `ConfigChange` fires when the `/plugin` panel writes `enabledPlugins` — UNVERIFIED
- `--bare` skips all settings and plugin hooks, so a hook is not a hard boundary — verified 2026-10-18 against local `claude --help` (2.1.303)

### Other agents

- OpenAI Codex CLI has PreToolUse hooks in `~/.codex/hooks.json`, `~/.codex/config.toml` `[hooks]`, `<repo>/.codex/hooks.json`, `<repo>/.codex/config.toml`. They are on by default (`[features] hooks = false` turns them off). Non-managed hooks must be trusted via `/hooks`, and trust is hash-bound — verified 2026-10-18 against https://learn.chatgpt.com/docs/hooks (redirect target of developers.openai.com/codex/hooks)
- The Codex schema matches Claude Code: `{"hooks":{"PreToolUse":[{"matcher":"Bash","hooks":[{"type":"command","command":"...","timeout":30}]}]}}`. stdin has `session_id`, `transcript_path`, `cwd`, `hook_event_name`, `model`, `permission_mode`, `turn_id`, `tool_name`, `tool_use_id`, `tool_input`. Shell and `apply_patch` arrive in `tool_input.command` — verified 2026-10-18 against https://learn.chatgpt.com/docs/hooks
- Codex blocks with exit 2 plus stderr, with `hookSpecificOutput.permissionDecision: "deny"` plus `permissionDecisionReason`, or with legacy `{"decision":"block","reason":...}`. `"ask"` is unsupported, so the hook is marked failed and the call proceeds. The matcher is a regex on the tool name. Hosted tools such as WebSearch are not covered — verified 2026-10-18 against https://learn.chatgpt.com/docs/hooks
- Cursor has hooks in `~/.cursor/hooks.json`, `<project>/.cursor/hooks.json` and enterprise paths. The shape is `{"version":1,"hooks":{"<event>":[{"command":"...","matcher":"...","timeout":N,"failClosed":false}]}}`. Events include `preToolUse`, `beforeShellExecution`, `beforeMCPExecution` and `beforeReadFile` — verified 2026-10-18 against https://cursor.com/docs/hooks
- Cursor `beforeShellExecution` stdin is `{command, cwd, sandbox}` plus base fields. `beforeMCPExecution` has `tool_name`, `tool_input` (a JSON string), `mcp_server_name`, and `url` or `command`. Output is `{"permission":"allow"|"deny"|"ask","user_message","agent_message"}`. Exit 2 is deny. Other non-zero exits fail open unless `failClosed: true` — verified 2026-10-18 against https://cursor.com/docs/hooks

## 3. Watcher and service recipes

- watchdog latest is 6.0.0 (requires Python >=3.9) — verified 2026-10-18 against live pypi.org/pypi/watchdog/json
- API: `from watchdog.observers import Observer`, `from watchdog.events import FileSystemEventHandler`. Override `on_any_event`, `on_created`, `on_modified`, `on_deleted`, `on_moved`, `on_closed` (also `on_attrib`, `on_opened`, `on_closed_no_write`). Call `obs.schedule(handler, path, recursive=False, event_filter=None)`, then `obs.start()`, `obs.stop()`, `obs.join()`. Events carry `src_path`, `dest_path`, `event_type`, `is_directory`, `is_synthetic` — verified 2026-10-18 against gorakhargosh/watchdog@a98cad1 src/watchdog/events.py:249-339, observers/api.py:324-330
- `Observer` picks inotify (Linux), FSEvents then kqueue (macOS), ReadDirectoryChangesW (Windows), with polling as the fallback — verified 2026-10-18 against gorakhargosh/watchdog@a98cad1 src/watchdog/observers/__init__.py:53-78
- launchd user agent: plist in `~/Library/LaunchAgents/<Label>.plist` with keys `Label`, `ProgramArguments` (array), `RunAtLoad` (bool), `KeepAlive` (bool or dict), `StandardOutPath`, `StandardErrorPath`, `ThrottleInterval`, `ProcessType` — verified 2026-10-18 against local `man launchd.plist` (macOS 26.6.2)
- Load with `launchctl bootstrap gui/$(id -u) <plist>`, unload with `launchctl bootout gui/$(id -u)/<Label>`. The legacy `load|unload` still exist — verified 2026-10-18 against local `man launchctl` (subcommands bootstrap, bootout, enable, kickstart, load listed)
- systemd user unit: `~/.config/systemd/user/<name>.service` (or `$XDG_CONFIG_HOME/systemd/user`) — verified 2026-10-18 against https://www.freedesktop.org/software/systemd/man/latest/systemd.unit.html
- `default.target` is the main target of the user manager, so user services use `[Install] WantedBy=default.target` — verified 2026-10-18 against https://www.freedesktop.org/software/systemd/man/latest/systemd.special.html
- `systemctl --user enable --now <unit>` talks to the calling user's manager, creates the symlinks and starts the unit — verified 2026-10-18 against https://www.freedesktop.org/software/systemd/man/latest/systemctl.html
- `loginctl enable-linger` is needed only to keep user units running without a login session — verified 2026-10-18 against https://www.freedesktop.org/software/systemd/man/latest/loginctl.html
- `schtasks /Create /SC ONLOGON /TN "<name>" /TR "<cmd>" [/RL LIMITED] [/F]`. `/TR` is limited to 262 characters. ONLOGON runs when any user logs on, or the `/RU` user. `/RL` defaults to LIMITED. `/F` overwrites — verified 2026-10-18 against https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/schtasks-create (git 4282dd4)
- `schtasks /SC ONLOGON` succeeds as a standard (non-admin) user — UNVERIFIED (no Windows host; the doc says "Only Administrators can schedule tasks" in its System-account section; an HKCU `...\CurrentVersion\Run` value or a Startup-folder shortcut is the non-admin fallback)
- PowerShell equivalent: `$a = New-ScheduledTaskAction -Execute "<exe>" -Argument "<args>"; $t = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME; Register-ScheduledTask -TaskName "<name>" -Action $a -Trigger $t` — verified 2026-10-18 against https://learn.microsoft.com/en-us/powershell/module/scheduledtasks/new-scheduledtasktrigger (Example 5, `-AtLogOn`, `-User`)
- `Register-ScheduledTask` with `-AtLogOn -User <self>` works without elevation — UNVERIFIED (no Windows host)
- macOS: `osascript -e 'display notification "<body>" with title "<title>" [subtitle "<s>"] [sound name "<n>"]'` exits 0. The notification is attributed to the calling script or host app — verified 2026-10-18 by local run (exit 0) and https://developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide/DisplayNotifications.html
- Linux: `notify-send [-u low|normal|critical] [-t ms] [-a app] [-i icon] <summary> [body]` (libnotify-bin). It needs a running notification daemon. GNOME ignores `-t` — verified 2026-10-18 against https://manpages.debian.org/trixie/libnotify-bin/notify-send.1.en.html
- Windows: `System.Windows.Forms.NotifyIcon.ShowBalloonTip(timeout, title, text, ToolTipIcon)` exists in .NET Framework 2.0 to 4.8.1 (PowerShell 5.1) and windowsdesktop 3.0 and later (PowerShell 7 on Windows). It needs `Icon` set and `Visible = $true`, and `timeout` is ignored by the OS — verified 2026-10-18 against https://learn.microsoft.com/en-us/dotnet/api/system.windows.forms.notifyicon.showballoontip
- The NotifyIcon recipe (`Add-Type -AssemblyName System.Windows.Forms`; set `.Icon = [System.Drawing.SystemIcons]::Information`; `.Visible = $true`; `ShowBalloonTip`; `Start-Sleep`; `Dispose()`) shows a notification from a plain script on Windows 11 — UNVERIFIED (no Windows host)
- The WinRT toast (`[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType=WindowsRuntime]`) works from a plain 5.1 script without a registered AppUserModelID — UNVERIFIED (no Windows host; that type syntax does not load on PowerShell 7, so NotifyIcon is the one choice that covers both)

## 4. Rehearse box and tracing

- The flags `--network none --read-only --cap-drop ALL --security-opt no-new-privileges --pids-limit 128 --tmpfs /tmp:rw,nosuid,size=64m --tmpfs /home/box:rw,nosuid,size=64m,uid=10001,gid=10001 --user 10001:10001 -e HOME=/home/box` run together. Inside: `CapEff: 0000000000000000`, `NoNewPrivs: 1`, `Seccomp: 2`. A write to `/etc` fails with "Read-only file system". `connect()` to 1.1.1.1:53 fails with `ENETUNREACH`. Forking past the pids limit fails with "Cannot fork" — verified 2026-10-18 by box test
- `--tmpfs` options use `mount -t tmpfs -o` syntax. `--read-only`, `--cap-drop`, `--pids-limit`, `--security-opt no-new-privileges`, `--memory` and `--user` are documented flags — verified 2026-10-18 against https://docs.docker.com/reference/cli/docker/container/run/
- `strace -f -o <file> <cmd>`, tracing its own child, works inside that box with zero capabilities under the default seccomp profile. `--cap-add SYS_PTRACE` is not needed for it. The log captured `connect(... 1.1.1.1 ...) = -1 ENETUNREACH` and `openat(... "/home/box/x", O_WRONLY|O_CREAT ...)` — verified 2026-10-18 by box test
- Attaching to a non-child (`strace -p <pid>`) fails with `ptrace(PTRACE_SEIZE): Operation not permitted`, and still fails with `--cap-add SYS_PTRACE` when running as non-root `--user` — verified 2026-10-18 by box test
- Default seccomp allows `ptrace` on kernel 4.8 and later. Tracing arbitrary processes is blocked by dropping `CAP_SYS_PTRACE`, not by seccomp — verified 2026-10-18 against https://docs.docker.com/engine/security/seccomp/
- `inotifywait -m -r -e create,modify,delete,moved_to --format "%w%f %e" <dir>` (Debian `inotify-tools`) runs unprivileged in the box and printed `/home/box/f CREATE` and `/home/box/f MODIFY` — verified 2026-10-18 by box test
- macOS `fs_usage` requires root ("'fs_usage' must be run as root...") — verified 2026-10-18 against local `man fs_usage` and a local run
- macOS `dtrace` without root fails ("DTrace requires additional privileges"). With SIP enabled, destructive actions and kernel memory access are refused even as root — verified 2026-10-18 by local run (SIP enabled) and local `man dtrace`
- Sysmon install (`sysmon64 -accepteula -i [config]`) installs a service and a boot-start driver. Events go to `Applications and Services Logs/Microsoft/Windows/Sysmon/Operational`. Supported on Windows 11+ and Server 2019+ — verified 2026-10-18 against https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon (git 2fd3249)
- Installing Sysmon and starting ETW kernel sessions (NT Kernel Logger) require Administrator or membership of Performance Log Users — UNVERIFIED (the fetched pages do not state the privilege rule; follow-up source is https://learn.microsoft.com/en-us/windows/win32/etw/configuring-and-starting-the-nt-kernel-logger-session)
- `python:3.12-slim` is a multi-arch index with `linux/amd64` and `linux/arm64/v8` (also arm/v5, arm/v7, 386). It is currently Debian 13 trixie with Python 3.12.15 — verified 2026-10-18 against `docker buildx imagetools inspect python:3.12-slim` and box test

## 5. Offline agent loop

- llama-cpp-python 0.3.36 exists on PyPI. Tag v0.3.36 is commit 1652066 — verified 2026-10-18 against live pypi.org/pypi/llama-cpp-python/json and abetlen/llama-cpp-python tags
- `Llama.create_chat_completion(messages, ..., tools=None, tool_choice=None, ...)` accepts OpenAI-style `tools` and `tool_choice` — verified 2026-10-18 against abetlen/llama-cpp-python@1652066 llama_cpp/llama.py:2004-2081
- With `chat_format=None`, the handler is the GGUF's `tokenizer.chat_template`, rendered by `Jinja2ChatFormatter` (registered as `chat_template.default`). Known templates map to a named format. The fallback is `llama-2` — verified 2026-10-18 against abetlen/llama-cpp-python@1652066 llama_cpp/llama.py:512-566
- `Jinja2ChatFormatter` passes `tools` (and `functions`) into the template render, so a model's own tool prompt is used — verified 2026-10-18 against abetlen/llama-cpp-python@1652066 llama_cpp/llama_chat_format.py:262-280
- In the generic or Jinja handler, `tool_calls` are returned only when `tool_choice` is a dict `{"type":"function","function":{"name":X}}`. That builds a JSON-schema grammar from that tool's `parameters` and wraps the raw completion text as `tool_calls[0].function.arguments` with `finish_reason: "tool_calls"`. With `tool_choice="auto"` or None, output is plain `message.content` and is not parsed for tool calls — verified 2026-10-18 against abetlen/llama-cpp-python@1652066 llama_cpp/llama_chat_format.py:700-755, 423-470
- `chat_format="chatml-function-calling"` handles `tool_choice="auto"` itself. It uses its own ChatML prompt and a grammar `root ::= functions | "message:"`, where the model emits `functions.<name>:` then JSON, or `message:` then text — verified 2026-10-18 against abetlen/llama-cpp-python@1652066 llama_cpp/llama_chat_format.py:4131-4420
- `chat_format="functionary"`, `"functionary-v1"` and `"functionary-v2"` are registered handlers for Functionary models only — verified 2026-10-18 against abetlen/llama-cpp-python@1652066 llama_cpp/llama_chat_format.py:1459, 1821-1822
- `ibm-granite/granite-4.1-3b-GGUF` ships Q2_K to Q8_0 and bf16 GGUFs. Its embedded `chat_template` (6099 chars) has a tools section, asks for `<tool_call>{"name": ..., "arguments": {...}}</tool_call>`, and has a `tool_response` role. It uses `<|start_of_role|>`/`<|end_of_role|>`/`<|end_of_text|>` (not ChatML). Context length is 131072 — verified 2026-10-18 against https://huggingface.co/api/models/ibm-granite/granite-4.1-3b-GGUF (sha ab47014)
- So with Granite 4.1 and the default GGUF template plus `tool_choice="auto"`, the code must parse `<tool_call>...</tool_call>` JSON out of `message.content` itself. Forcing one named tool via a dict `tool_choice` gives grammar-valid JSON args. `chatml-function-calling` would apply a ChatML prompt that mismatches Granite's role tokens — verified 2026-10-18 by combining the two lines above (inference from source, not a model run)
- Granite 4.1 3B reliably emits well-formed `<tool_call>` blocks under llama-cpp-python 0.3.36 — UNVERIFIED (no model run)

## 6. DNS canary

- canarytokens.org has an HTTP API at `POST https://canarytokens.org/d3aece8093b71007b5ccfedad91ebb11/generate`, which is the same endpoint the web UI uses. Its OpenAPI is at `/d3aece8093b71007b5ccfedad91ebb11/openapi.json` — verified 2026-10-18 against thinkst/canarytokens@8684b6d frontend/app.py:339-350, 566-572 and frontend_vue/src/api/main.ts:42, and live (openapi.json 200, paths include `/generate`, `/history`, `/manage`)
- Request: JSON `{"token_type":"dns","memo":"<text>","email":"<addr>"}` or with `"webhook_url":"<url>"`. Form encoding uses `type` instead of `token_type`. `memo` is required, and either `email` or `webhook_url` is required — verified 2026-10-18 against thinkst/canarytokens@8684b6d canarytokens/models/common.py:179-197, models/dns.py, frontend/app.py:579-592
- Response fields: `token`, `hostname` (the name to resolve), `token_url`, `auth_token`, `email`, `webhook_url`, `error`, `error_message`. Errors return `{"error":"1","error_message":"Malformed request, invalid data supplied."}` with HTTP 400 — verified 2026-10-18 against thinkst/canarytokens@8684b6d canarytokens/models/common.py (TokenResponse) and a live POST of `{}` (400, error 1)
- Hit history: `GET .../history?token=<token>&auth=<auth_token>` — verified 2026-10-18 against thinkst/canarytokens@8684b6d frontend/app.py:782-786
- No account and no CAPTCHA for DNS tokens. Turnstile is checked only for `credit_card_v2` and `/fetchlinks` — verified 2026-10-18 against thinkst/canarytokens@8684b6d frontend/app.py:628-640, 860-870
- Network behaviour: any attempt to resolve the token hostname triggers an alert. Up to about 125 bytes of Base32 data can be prefixed with a `.G<nn>.` marker — verified 2026-10-18 against https://docs.canarytokens.org/guide/dns-token.html
- An alert fires through a recursive resolver even when the resolving host has no direct route out — UNVERIFIED (docs do not mention resolvers; not tested; in a `--network none` box nothing resolves, so nothing fires)
- Free: the guide says tokens are "completely free" — verified 2026-10-18 against https://docs.canarytokens.org/guide/
- Creating a live token sends the memo and the email/webhook to Thinkst. No token was created during this research — verified 2026-10-18 against thinkst/canarytokens@8684b6d frontend/app.py:585 (logs the full request)
