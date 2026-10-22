# Decisions

Each entry: the question, what unpick does now (the recommendation it is running on), and what would
change it. Open ones are marked **OPEN**. Answer by editing this file or telling the maintainer.

## Phase 1

1. **Name: `unpick`** (decided 2026-10-18; replaces `runthrough`, which reads like "ran through").
   To unpick a seam is to take it apart stitch by stitch and see what was sewn in, and "unpick" also
   means to examine something carefully. Free on PyPI and npm, and as `amberb617/unpick` on GitHub
   (a GitHub user named `unpick` exists, so `github.com/unpick` is not ours). Alternates that were also
   free everywhere: `seamrip`, `tailorcheck`. Repository: `amberb617/unpick`, private until you publish it.

2. **Where the code lives locally.** `~/Desktop/bsides-cambridge/unpick`, next to the talk material,
   not under `~/jiffy/` (that folder is auto-synced from the Jiffy-Labs-AI org).

3. **What `scan .` skips in this repo.** `.unpickignore` skips `tests/`, `data/`, `demo/` and
   `unpick/demo_kit/`, each with a reason. The remaining findings in source and docs (the tool's own
   descriptions of attacks) are accepted in `.unpick/decisions.json` with notes. The demo kit passes
   on its own with `demo/accepted.decisions.json`, which is a separate test.

4. **Decision key.** Accepted findings are suppressed by rule id plus the content hash of the matched
   line, as specified. That means accepting a line also accepts the identical line in another file.
   Recommendation: keep it (it is what makes a project-wide "this sentence is fine" decision possible).

5. **An empty scan is an error.** Scanning a folder with no readable text files exits 2 with
   "nothing was scanned", not 0. A clean exit would be absence posing as health.

6. **Severity floor for the benchmark.** A file counts as flagged by a source when it has a medium or
   high finding. Low findings (an env var named in docs, a plain HTML comment) are questions, not alarms.

7. **Agents added beyond the list.** Inventory also covers Amazon Q Developer, Kiro, Roo Code, OpenCode,
   Goose, Aider, xAI Grok Build (`~/.grok`), Augment (Auggie) and Amp. Windsurf is now Devin Desktop and
   its MCP config moved to `~/.config/devin/mcp_config.json`; the old path is kept, marked unverified.
   Codex still scans `~/.codex/skills`; its docs now list `~/.agents/skills`, and both are covered.

8. **Codex CLI and Grok CLI are not judges.** Neither can be confirmed to run with zero tools (Codex has
   no all-tools switch and cannot print its tool list; Grok keeps MCP tools available and loads other
   agents' MCP servers and allow rules). Both are listed by `unpick judges` with the reason.
   Revisit when either ships a verifiable no-tools mode.

9. **Gemini CLI as a judge** has no schema flag. The schema goes in the prompt and the answer is
   validated afterwards. Built-in tools are off through a system settings file (`tools.core: []`).

10. **Phi Silica is not offered.** Windows AI APIs need an app with package identity and the
    `systemAIModels` capability; a command-line Python process has neither. Foundry Local is offered
    instead (its structured output is UNVERIFIED, so answers are validated after the fact).

11. **Fallback judge for Windows and Linux: IBM Granite 4.1 3B, Q4_K_M GGUF, via llama-cpp-python.**
    Apache-2.0, 3.4B parameters, published as GGUF by IBM itself, pinned by commit and SHA-256, downloaded
    only with `--online`. Chosen over Qwen3-4B-Instruct-2507 (just over 4B, no first-party GGUF) and
    Ministral 3 3B (no published instruction-following score). Granite 4.2 was skipped because it reasons
    by default, which fights JSON-only output. Approved and recorded 2026-10-18: **unreliable**, fooled on
    3 of 4 adversarial files (once by obeying the planted instruction). Weights are never bundled (2.1 GB,
    over PyPI's file limit) and llama-cpp-python stays an optional extra (PyPI ships only source, which
    would force a compiler on every Windows install); `unpick judges install fallback --online` installs
    both. The macOS arm64 wheels for 0.3.34-0.3.36 are corrupt upstream, so macOS builds from source.

12. **Apple Intelligence judge is unreliable.** It missed a planted base64-to-shell line when a hidden
    note told it the line was safe. It stays the default on-device judge on Macs (it is the only one
    many Macs have), shown with the "unreliable" result in docs/BENCHMARK.md. Recommendation: keep, since
    a judge is never the verdict.

13. **Hosted judges benchmarked with consent (2026-10-18).** Claude Code: reliable on all four files.
    Gemini CLI could not run (the AI Studio project is out of prepaid credit); no recording kept.

14. **The `api` judge tier is UNVERIFIED.** Provider endpoints and request shapes are written but not yet
    checked against each provider's current API reference; the tier warns when used and is never automatic.

15. **SkillSpector only runs with `--online` or `--boxed`.** It calls OSV.dev even with `--no-llm` and has
    no flag to stop it. Installed from GitHub at the pinned commit; it is not on PyPI.

16. **Code style.** The Jiffy pre-PR gate, translated to Python: ruff for unused imports, cognitive
    complexity of 15 or less and no empty `except`; an AST test for nested conditional expressions.
    pnpm, not npm, wherever a Node tool is installed.

## After the October 2026 landscape review

21. **Built from docs/research/2026-10-landscape.md** (its top items, all offline): `RT-AUTORUN` (project hooks
    and folder-open tasks, the CHAINDROP pair), `RT-AGENT-SETTINGS` (approval flips and base-URL reroutes
    for Claude Code, VS Code, OpenCode, Codex, Gemini CLI, plus "export ANTHROPIC_BASE_URL=" in prose),
    `RT-MCP-LAUNCH` (unpinned `npx -y`/`uvx`, mcp-remote < 0.1.16, plain-http remotes, hidden binaries),
    `RT-GIT-AUTORUN` (.git/config and .gitattributes that run programs), download-to-file-then-run in
    `RT-ENCODED-EXEC` (the Zenity payload), `RT-UNREAD` (bundles, WebAssembly and binaries that cannot be
    read are findings, and every skipped file is listed), and the OpenCode inventory surface.
    Before: a CHAINDROP reproduction and the Zenity payload scored 0 findings. After: both are caught.

22. **Built 2026-10-18:** `RT-CI-AGENT` and `RT-INSTALL-REDIRECT` (below were queued). Look-alike GitHub
    org slugs (getpaperclipai vs paperclipai) are still not detected: without a list of the real orgs the
    comparison has nothing to compare against. Previously queued: a CI-workflow check for agent actions on `issues` / `pull_request_target`
    with unrestricted tools (Clinejection, "Comment and Control"); an install-redirect check for prose
    that steers the agent away from the registry to a look-alike source; and in phase 3, `lock`/`verify`
    that checks HEAD against the pinned SHA, refuses branch names shaped like a SHA (Claude Code
    CVE-2026-86063) and verifies NVIDIA `skill.oms.sig` signatures offline.

23. **No CHAINDROP file hashes shipped.** The report suggests matching published `setup.mjs` hashes; none
    were found in a primary source, and inventing them is worse than not having them.

## Phase 3

24. **rehearse needs Docker.** sandbox-runtime boxes a host command, but rehearse needs its own filesystem,
    a model runtime and tracing, so it uses a Linux container on every host OS. Tracing is strace inside the
    box. Host tracers (fs_usage, dtrace, ETW, Sysmon) need root or admin and SIP blocks dtrace, so they are
    not used.

25. **rehearse is offline only for now.** The spec allows a hosted model with exactly one allowed API host.
    Not built: a no-network box plus a local model already works, and a per-host egress allowance needs a
    proxy inside the box. Decided 2026-10-18: not building it.

26. **The hook fails closed.** An install the hook cannot resolve (an MCP add whose server is a local
    binary, say) is denied with the reason and the override, `UNPICK_HOOK_FAIL_OPEN=1`.

27. **`check` is network-on by default**, as the spec asks; `--offline` skips provenance. `outdated` needs
    `--online`. The hook inherits check's network behaviour, and the README table says so.

28. **CHAINDROP file hashes and GitHub look-alike orgs** are still not shipped (no primary-source IOC list).

29. **A hook must read the command, not the text around it.** On 2026-10-18 the Jiffy CLI hook on this
    machine blocked a shell script because a heredoc of documentation contained an MCP-add example.
    unpick's hook had the same weakness. Fixed 2026-10-18: `targets()` now splits the script into real shell
    commands first (quoted text stays one word, heredoc bodies are skipped, `sh -c` and `eval` are opened
    up) and matches installs only where a command starts. An unparseable script still gets the old
    whole-text match, which errs toward blocking.

## Phase 4

30. **recover changes nothing without `--yes`** (the UI asks in a dialog that lists every action). Moving a
    component and editing configs are hard to undo in the middle of an incident; a dry run first is cheap.

31. **TOML configs are not rewritten.** Python's standard library reads TOML but does not write it, so for
    a Codex `[mcp_servers.x]` table recover prints the exact edit to make by hand. JSONC configs are
    rewritten without their comments; the backup keeps the original.

32. **Session logs are parsed for Claude Code, Codex and Gemini CLI only.** None of these formats is
    documented by its vendor; they were read from local files (keys only) on 2026-10-18 and a parser that
    finds nothing says so. Cursor writes no tool-call log; OpenCode's storage is UNVERIFIED and skipped.

33. **Rotation and abuse-report data** (data/rotation.json, data/abuse_channels.json) carry a source URL per
    entry. UNVERIFIED items: OpenAI dashboard deletion steps (help pages returned 403), Firefox password
    steps and Ledger's recovery guidance (pages could not be read), npm `token revoke` vs `token delete`
    (the two npm doc pages disagree), and Smithery (no abuse channel published).

## Phase 5

34. **Handout commands wrap onto continuation lines** to stay within 60 characters: two of them (the
    invisible-Unicode grep and the red-flag grep) cannot fit on one line with a real file name. Every
    line, including continuations, is 60 or narrower.

35. **Windows PowerShell 5.1 was tested on GitHub's windows-latest runner**, the only Windows machine
    available. Its recorded output is in docs/HANDOUT-COMMANDS.md, and the job runs on every push.

36. **Windows CI found five real bugs** (hook marker on unpick.exe, POSIX quoting, backslash paths in the
    rotation matcher, cp1252 default reads, literal invisible characters in the PowerShell script). All
    fixed; a test now fails on any literal invisible character in the repo's own sources.

37. **Slide screenshots are generated, not hand-made:** `python tests/slides.py` drives the real UI at 2x
    with the installed scanners and records the commit and every scanner version in docs/SLIDES.md.

## After the UX review

38. **Quarantine is one engine.** `unpick quarantine`, `watch --quarantine`, the UI's "Stop the AI from loading this"
    and `recover`'s containment step all call unpick/isolate.py, so they cannot drift apart. Nothing is
    deleted; `restore` refuses to overwrite something that has come back in the meantime.

39. **`clean` only removes what is never legitimate.** Invisible characters, hidden HTML comments outside
    code blocks, and one-step decode-or-download-and-run lines. It does not rewrite instructions or tool
    descriptions, because a rewrite that looks right is worse than an honest flag.

40. **The tagline stays** at the top of the UI (the spec asked for it); the start screen carries a
    plain-language line for newcomers. The third review (Grok) asked again to replace it; it still stays.

## After the third review (Grok)

41. **Quarantine never follows a link or rewrites text it cannot keep.** A symlinked skill is moved as a
    link, so its target is untouched. A config is rewritten only when it is plain JSON in valid UTF-8 with
    no comments; otherwise unpick prints the manual edit. Every rewrite is backed up and swapped in
    atomically. Hooks are matched by content, and an MCP server is removed from every block that lists it,
    including Claude Code's per-project blocks and OpenCode's `plugin` array.

42. **The watcher quarantines the add-on, not the folder it lives in.** It moves the deepest inventoried
    skill, plugin or extension folder that owns the changed file. A shared config or cache is never moved
    whole; the event records `quarantine_skipped` instead.

43. **Review copies live outside every agent folder**, in ~/.unpick/cleaned/, with symlinks dropped, so an
    agent cannot load a half-cleaned add-on by accident.

44. **No folder picker in the UI.** A browser page cannot read a local folder's full path, which every
    command needs, so the path box stays. The next steps (test run, recovery) now always follow the
    latest scan instead.

## Redesign after the UX cycles (2026-10-19)

45. **The UI follows the Jiffy quickstart, not the signed-in admin app.** unpick is a free offline scanner,
    which is what the quickstart is. Start is one input card; a scan is a result page with a verdict block,
    one warning list and an aside. The talk's five steps stay in the README and the talk, not in the
    navigation. Sources and what was left out: docs/UI-NOTES.md.

46. **No result is ever called "clear".** The neutral verdict reads "NO WARNINGS / This does not prove it
    is safe", on a grey block rather than green (Codex review, and the Jiffy rule that absence must not
    render as health).

47. **The decision comes after the explanation,** with "Not sure: ask the author" and a line saying that
    leaving it open is a valid answer. A newcomer should not be asked to judge before reading why.

48. **Warnings are ordered for a newcomer:** undecided, then severity, then how many checkers agree, then
    unpick's own plain-language checks before another scanner's terse rule names.

49. **Quarantine from the UI acts on one add-on, decided by the server.** An entry in a shared settings file
    is removed alone; a file holding other add-ons' entries, or a folder holding several add-ons, is never
    moved whole, whatever the page sends; links are moved, never followed.

50. **Nothing the UI saves is called an approval.** A web check saves "a record of this download"; Changes
    saves "a copy to compare later". Both say they are not a safety verdict. Re-locking keeps the download
    records, and a lockfile holding only those counts as a first run.

## Plain-language UI (2026-10-21)

51. **The UI has no tagline and no presenter mode.** The header shows only the name, version, navigation,
    theme and "Something got in?". The tagline read as noise to a first-time user, and presenter mode was a
    talk aid that put an unexplained button in everyone's header. Supersedes 40.

52. **Results lead with a verdict and its reason in plain words.** Three verdicts (STOP, CHECK FIRST,
    NOTHING FOUND); the reason is the top open warning's plain sentence from `unpick/ui/plain.py`. Severity,
    rule id and the checker's own wording sit in each card's technical details. A path with no readable
    files shows NOT CHECKED, never NOTHING FOUND.

## Phase 2 (looking ahead)

17. **UI fonts.** Resolved: system sans and a Courier New mono stack, as specified. The Jiffy platform's
    own tokens (jiffy-base.css) fall back to the same system stack, and no font files are loaded.

18. **UI scope in phase 2.** Inventory, Scan, and Backends and judges are built now. Check, Rehearse,
    Verify and Recover screens are added in phases 3 and 4 with the engines they drive, because nothing
    may exist in the UI that the CLI cannot do. "Lock these" on the inventory screen arrives with `lock`.

19. **Localhost hardening.** Besides the Host-header check and strict CSP, every API call needs a random
    per-launch token in a custom header. A web page on another origin cannot send that header without a
    CORS preflight, which the server never answers, so it cannot drive the local API (CSRF).

20. **Visual tokens** come from Jiffy-Labs-AI/platform `src/app/styles/jiffy-base.css` @4eb0f40: navy
    #040E27, pale blue #E7EEFA, pink #FF97BF, red #FF4E4E, lavender, the pill palette, and the `.j-offset`
    offset shadow (pink on dark, #FFC5C5 on light).
