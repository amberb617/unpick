# Decisions

Each entry: the question, what runthrough does now (the recommendation it is running on), and what would
change it. Open ones are marked **OPEN**. Answer by editing this file or telling the maintainer.

## Phase 1

1. **Name.** `runthrough` is free on PyPI and npm. On GitHub the `runthrough` organisation exists
   (created 2024, no public repos), so `github.com/runthrough` is unavailable; the repository name is
   free under `amberb617` and `Jiffy-Labs-AI`. `thatsall` and `priestly` are taken as GitHub user
   accounts too, so falling back gains nothing. Running on: `runthrough`. **OPEN:** host the repository
   under `amberb617/runthrough` (personal, vendor-neutral) or `Jiffy-Labs-AI/runthrough`? Recommendation:
   `amberb617`, because the talk is vendor-neutral and the org name would read as a product.

2. **Where the code lives locally.** `~/Desktop/bsides-cambridge/runthrough`, next to the talk material,
   not under `~/jiffy/` (that folder is auto-synced from the Jiffy-Labs-AI org).

3. **What `scan .` skips in this repo.** `.runthroughignore` skips `tests/`, `data/`, `demo/` and
   `runthrough/demo_kit/`, each with a reason. The remaining findings in source and docs (the tool's own
   descriptions of attacks) are accepted in `.runthrough/decisions.json` with notes. The demo kit passes
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
   agents' MCP servers and allow rules). Both are listed by `runthrough judges` with the reason.
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
    by default, which fights JSON-only output. It is not yet recorded on the adversarial corpus: the
    download is 2.1 GB and was left for you to approve. **OPEN:** download it now and record it?

12. **Apple Intelligence judge is unreliable.** It missed a planted base64-to-shell line when a hidden
    note told it the line was safe. It stays the default on-device judge on Macs (it is the only one
    many Macs have), shown with the "unreliable" result in docs/BENCHMARK.md. Recommendation: keep, since
    a judge is never the verdict.

13. **Hosted judges were not benchmarked.** Recording one sends the adversarial corpus (synthetic, CC0) to
    the provider. Left for you: `python tests/adversarial/eval.py claude-code:default`.

14. **The `api` judge tier is UNVERIFIED.** Provider endpoints and request shapes are written but not yet
    checked against each provider's current API reference; the tier warns when used and is never automatic.

15. **SkillSpector only runs with `--online` or `--boxed`.** It calls OSV.dev even with `--no-llm` and has
    no flag to stop it. Installed from GitHub at the pinned commit; it is not on PyPI.

16. **Code style.** The Jiffy pre-PR gate, translated to Python: ruff for unused imports, cognitive
    complexity of 15 or less and no empty `except`; an AST test for nested conditional expressions.
    pnpm, not npm, wherever a Node tool is installed.

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
