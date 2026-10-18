# Judge backends: verified claims

One line per claim. UNVERIFIED means we could not confirm it, not that it is false.
Abbreviations: `FM.swiftinterface` = `MacOSX.sdk/System/Library/Frameworks/FoundationModels.framework/Versions/A/Modules/FoundationModels.swiftmodule/arm64e-apple-macos.swiftinterface` in Xcode SDK 27.0 (module 2.0.68.1.402).

## This machine

- macOS 26.6.2 (build 25G83), arm64 — verified 2026-10-18 against local `sw_vers` and `uname -m`
- Swift 6.4 (swiftlang-6.4.0.34.1), default target arm64-apple-macosx26.0, SDK 27.0 — verified 2026-10-18 against local `xcrun swiftc --version` and `xcrun --show-sdk-version`
- Installed: claude 2.1.302, codex-cli 0.159.3, gemini 0.59.0, grok 1.0.46 — verified 2026-10-18 against local `--version`
- Not installed: ollama, lms, foundry, mlx_lm.server, llama-server; nothing listening on :11434 or :1234 — verified 2026-10-18 against local `which` and `curl`

## Tier 1: Apple Foundation Models (on-device)

- Needs macOS 26.0 or later — verified 2026-10-18 against https://developer.apple.com/tutorials/data/documentation/foundationmodels/systemlanguagemodel/availability-swift.property.json (introducedAt macOS 26.0)
- Needs an Apple Intelligence Mac: M1 or later (plus MacBook Neo, A18 Pro); 8 GB of storage, or up to 14 GB on M3+ with 12 GB+ memory — verified 2026-10-18 against https://support.apple.com/en-us/121115
- Availability check is `SystemLanguageModel.default.availability`, which returns `.available` or `.unavailable(.deviceNotEligible | .appleIntelligenceNotEnabled | .modelNotReady)` — verified 2026-10-18 against FM.swiftinterface lines 345-368
- `LanguageModelSession(model: = .default, tools: = [], instructions: String?)` exists; passing `tools: []` gives the model nothing to call — verified 2026-10-18 against FM.swiftinterface line 38
- SDK 27 also ships `PrivateCloudComputeLanguageModel`, which is off-device; `SystemLanguageModel.default` is the one to use for on-device — verified 2026-10-18 against FM.swiftinterface lines 73-83 (type present). That it is off-device is inferred from its name, so UNVERIFIED
- A runtime schema is built with `DynamicGenerationSchema(name:description:properties:)` / `anyOf:` / `arrayOf:` / `referenceTo:` and then `GenerationSchema(root:dependencies:) throws` — verified 2026-10-18 against FM.swiftinterface lines 3151-3182 and 3370; https://developer.apple.com/tutorials/data/documentation/foundationmodels/dynamicgenerationschema.json
- `GenerationSchema` is `Codable`, so a JSON Schema document can be decoded straight into it with no DynamicGenerationSchema walker — verified 2026-10-18 against FM.swiftinterface line 3351 and a working local run
- The `GenerationSchema` decoder rejects plain JSON Schema unless every object has `title`, `x-order`, `additionalProperties` and `required` (errors: `keyNotFound` for each) — verified 2026-10-18 against local shim runs
- `respond(to: String, schema: GenerationSchema, options:)` returns `Response<GeneratedContent>`, and `GeneratedContent.jsonString` serializes the result — verified 2026-10-18 against FM.swiftinterface lines 2107, 1356
- Greedy sampling is `GenerationOptions(samplingMode: .greedy)`, back-deployed to macOS 26.0; `init(sampling:)` is deprecated; `temperature: Double?` is also available — verified 2026-10-18 against FM.swiftinterface lines 3200-3282, 3523; https://developer.apple.com/tutorials/data/documentation/foundationmodels/generationoptions/samplingmode-swift.struct/greedy.json
- It works from a plain CLI built with `swiftc`, with no app bundle, entitlement or signing: `xcrun swiftc -O -parse-as-library -target arm64-apple-macosx26.0 main.swift -o apple-fm`. `-parse-as-library` is needed for `@main` with async `main`, and `-target …26.0` is needed because the SDK defaults to 27 — verified 2026-10-18 against a local build and run
- The shim at `shims/apple-fm/main.swift` compiles cleanly and returned schema-valid JSON for a flat schema and for a nested object+array+enum schema on this Mac — verified 2026-10-18 against a local run
- Output quality is weak: the model invented line numbers and "malware signature" findings for a one-line input. It is schema-valid but not trustworthy as a sole verdict — verified 2026-10-18 against a local run

## Tier 2: local servers

- Ollama listens on 127.0.0.1:11434 by default (`OLLAMA_HOST`) — verified 2026-10-18 against ollama/ollama@36a6e994d2 envconfig/config.go
- Ollama `GET /api/tags` lists local models — verified 2026-10-18 against ollama/ollama@36a6e994d2 docs/api.md
- Ollama `POST /api/chat` takes `format` as `"json"` or a JSON schema object for structured outputs — verified 2026-10-18 against ollama/ollama@36a6e994d2 docs/api.md
- Ollama takes `options.temperature`, and the docs' structured-output example uses 0 — verified 2026-10-18 against ollama/ollama@36a6e994d2 docs/api.md
- llama.cpp `llama-server` defaults to 127.0.0.1:**9931**, not 8080 (`--port`, `LLAMA_ARG_PORT`) — verified 2026-10-18 against ggml-org/llama.cpp@ff5a233767 common/common.h:630 and tools/server/README.md
- llama.cpp `GET /v1/models` returns one element: the loaded model, with id = the `-m` path or `--alias` — verified 2026-10-18 against ggml-org/llama.cpp@ff5a233767 tools/server/README.md
- llama.cpp `/v1/chat/completions` takes `response_format` `{"type":"json_schema","schema":…}` or `{"type":"json_object","schema":…}`; `/completion` takes `json_schema` (grammar-constrained) — verified 2026-10-18 against ggml-org/llama.cpp@ff5a233767 tools/server/README.md
- LM Studio base URL in the docs is http://localhost:1234/v1. The docs say the examples "assume" port 1234 and do not call it the default, so UNVERIFIED as a default — https://lmstudio.ai/docs/developer/openai-compat
- LM Studio serves `GET /v1/models`, `POST /v1/chat/completions`, `/v1/responses`, `/v1/completions`, `/v1/embeddings` — verified 2026-10-18 against https://lmstudio.ai/docs/developer/openai-compat
- LM Studio structured output is `response_format: {"type":"json_schema","json_schema":{"name":…,"strict":…,"schema":…}}`, the result is a string in `choices[0].message.content`, and the docs warn models under 7B may not comply — verified 2026-10-18 against https://lmstudio.ai/docs/developer/openai-compat/structured-output
- `lms server start`, `lms ls [--json]`, `lms ps`, `lms load` — verified 2026-10-18 against lmstudio-ai/lms@43d4b2680e README.md and https://lmstudio.ai/docs/cli
- `mlx_lm.server` defaults to localhost:8080 and serves `/v1/chat/completions`, `/v1/completions`, `/v1/models` — verified 2026-10-18 against ml-explore/mlx-lm@93e6d4a644 mlx_lm/server.py:1244-1245, 1791, 1943
- `mlx_lm.server` has no `response_format` / JSON-schema support, so schema compliance must be validated after the response — verified 2026-10-18 against ml-explore/mlx-lm@93e6d4a644 (no match in server.py or SERVER.md)
- `mlx_lm.server` temperature defaults to 0.0 — verified 2026-10-18 against ml-explore/mlx-lm@93e6d4a644 mlx_lm/SERVER.md

## Tier 2b: Windows

- Foundry Local CLI is `foundry`, installed with `winget install Microsoft.FoundryLocal` (macOS: `brew install foundrylocal`); it is preview — verified 2026-10-18 against https://learn.microsoft.com/en-us/azure/ai-foundry/foundry-local/reference/reference-cli (git cb8e7145)
- `foundry model list [--cached|--loaded]` lists models — verified 2026-10-18 against the same page
- The Foundry Local port is dynamic ("assigns a dynamic port each time the server starts"). Discover it with `foundry server status`, which prints the local service URLs, or pin it with `foundry server start --port N`; the endpoint is OpenAI-compatible at `http://localhost:PORT/v1` — verified 2026-10-18 against the same page
- The older `foundry service status` name appears only in the 0.8.x upgrade note; the current command is `foundry server …` — verified 2026-10-18 against the same page
- Foundry Local structured-output / `response_format` support — UNVERIFIED (not on the CLI reference page)
- Phi Silica runs on Copilot+ PC NPUs, or on GPU (RTX 30+ / Radeon RX 9060+, 6 GB+ VRAM, Insider build 26300.8553+, Developer Mode, WinAppSDK 2.2.2-experimental9+) — verified 2026-10-18 against https://learn.microsoft.com/en-us/windows/ai/apis/phi-silica (git 8b58a0b3)
- Phi Silica is a Limited Access Feature that needs an unlock token on stable releases. Experimental releases do not need one, and Aion Instruct replaces Phi Silica on retail devices in January 2027 with no LAF token — verified 2026-10-18 against the phi-silica and troubleshooting pages
- Windows AI APIs (Phi Silica) need package identity at runtime plus the `systemAIModels` manifest capability; without them the call fails with `UnauthorizedAccessException`. A plain Python process or an unpackaged console exe cannot call them directly — verified 2026-10-18 against https://learn.microsoft.com/en-us/windows/ai/apis/troubleshooting (git 7f6ea0b9), "Other guidance"
- A packaged-with-external-location (sparse package) helper exe that a Python process shells out to might satisfy identity — UNVERIFIED (not stated on these pages)
- Phi Silica `LanguageModel.GenerateResponseAsync` has no JSON-schema / constrained-decoding parameter — UNVERIFIED (none shown on the phi-silica page; the full API reference was not checked)

## Tier 3: hosted agent CLIs

### Claude Code 2.1.302

- Headless is `claude -p "<prompt>"`; piped stdin is capped at 10 MB — verified 2026-10-18 against local `claude --help` and https://code.claude.com/docs/en/headless
- `--output-format json` returns `result`, plus `structured_output` when `--json-schema '<schema>'` is given — verified 2026-10-18 against local `--help`, the headless docs, and a local trivial run
- `--tools ""` disables all built-in tools — verified 2026-10-18 against local `--help` ("Use \"\" to disable all tools")
- `--strict-mcp-config` with no `--mcp-config` means no MCP servers — verified 2026-10-18 against local `--help`
- `--setting-sources ""` skips user/project/local settings, `--no-session-persistence` writes no transcript, and `--bare` also skips hooks, plugins, CLAUDE.md and memory but requires `ANTHROPIC_API_KEY` (no OAuth) — verified 2026-10-18 against local `--help` and the headless docs
- `--json-schema` is enforced through a synthetic output tool: the trivial run had `stop_reason: "tool_use"`, `num_turns: 3`, `permission_denials: []`, and the result was `structured_output: {"ok":true}` — verified 2026-10-18 against a local run (`claude -p … --tools "" --strict-mcp-config --setting-sources "" --no-session-persistence --output-format json --json-schema … --model haiku`)
- `--model <alias|full id>` — verified 2026-10-18 against local `--help`

### OpenAI Codex CLI 0.159.3

- Headless is `codex exec [PROMPT]` (stdin if `-`), with `--skip-git-repo-check`, `--ephemeral`, `--ignore-user-config`, `--ignore-rules` — verified 2026-10-18 against local `codex exec --help`
- `--json` streams events as JSONL; `-o FILE` writes the last message — verified 2026-10-18 against local `--help` and https://learn.chatgpt.com/docs/non-interactive-mode.md
- `--output-schema FILE` enforces the final response shape; the docs' example uses `required` + `additionalProperties:false`, but the docs state no requirements — verified 2026-10-18 against the same sources
- `codex exec` runs in a read-only sandbox by default (`-s read-only`) — verified 2026-10-18 against https://learn.chatgpt.com/docs/non-interactive-mode.md
- The shell tool can be turned off with `--disable shell_tool` (also `unified_exec`), web search with `-c web_search="disabled"`, and MCP per server with `mcp_servers.<n>.enabled=false` — verified 2026-10-18 against local `codex features list` and https://learn.chatgpt.com/docs/config-file/config-reference
- No single switch disables all tools: apps, plugins, browser_use, computer_use, view_image, image_generation, multi_agent and others are separate flags, and the model-visible tool list cannot be printed (`codex debug prompt-input` shows messages only). Zero tools CANNOT be confirmed — verified 2026-10-18 against local `codex features list` and `codex debug --help`. No trivial run was done.
- `-m, --model` — verified 2026-10-18 against local `--help`

### Gemini CLI 0.59.0

- Headless is `gemini -p "<prompt>"`, and untrusted folders need `--skip-trust` — verified 2026-10-18 against local `gemini --help` and a local run
- `-o json` returns `{response, stats, error?}` — verified 2026-10-18 against https://geminicli.com/docs/cli/headless
- There is no JSON-schema flag, so the schema must be validated after the response — verified 2026-10-18 against local `--help` and the headless docs
- `tools.core: []` registers zero built-in tools (an empty array is truthy and `.some()` is false) — verified 2026-10-18 against the local bundle @google/gemini-cli@0.59.0 `maybeRegister`
- MCP / extensions / skills can be cut with `mcp.allowed`, `admin.mcp.enabled:false`, `admin.extensions.enabled:false`, `admin.skills.enabled:false`, and `-e none`, through a system settings file at `GEMINI_CLI_SYSTEM_SETTINGS_PATH` (highest precedence) — verified 2026-10-18 against https://geminicli.com/docs/reference/configuration. Whether `admin.*` is honoured from a local system file is UNVERIFIED
- The trivial run loaded that config and reached the API, which returned 402 RESOURCE_EXHAUSTED (prepay credits depleted), so no model answer was obtained — verified 2026-10-18 against a local run
- `-m, --model` — verified 2026-10-18 against local `--help`

### xAI Grok Build CLI 1.0.46

- Headless is `grok -p "<prompt>"` (`--single`), `--prompt-file`, `--prompt-json` — verified 2026-10-18 against local `grok --help`
- `--output-format plain|json|streaming-json|streaming-messages-json` — verified 2026-10-18 against local `--help`
- `--json-schema '<schema>'` constrains the output and implies json; the result is in `structured_output` — verified 2026-10-18 against local `--help` and xai-org/grok-build@2bdd1d6a63 docs/user-guide/14-headless-mode.md
- `--max-turns N`, `--tools` (built-in allowlist), `--disallowed-tools`, `--deny RULE`, `--disable-web-search`, `--no-subagents`, `-m, --model` — verified 2026-10-18 against local `--help`
- `--tools` does not remove MCP: "MCP meta-tools remain available unless denied" — verified 2026-10-18 against xai-org/grok-build@2bdd1d6a63 14-headless-mode.md
- There is no flag to skip config/MCP loading. On this machine grok imports MCP servers from `~/.claude.json` and plugins, 569 allow rules from `~/.claude/settings.local.json`, and hooks. Zero tools CANNOT be confirmed — verified 2026-10-18 against local `grok inspect --json`. No trivial run was done.
- Semantics of `--tools ""` — UNVERIFIED (undocumented)
