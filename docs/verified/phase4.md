# Phase 4: verified claims (rotation, agent logs, egress, abuse channels, processes)

One claim per line. UNVERIFIED means we could not confirm it, not that it is false.
"Local" means a key-only inspection on this machine (macOS 26, 2026-10-18). No values were printed.
The `matches` regexes in `data/rotation.json` are unpick's own detection heuristics, not claims made by the providers.

## 1. Rotation checklist

### GitHub

- Delete a PAT (classic or fine-grained): profile picture > Settings > Developer settings > Personal access tokens > Fine-grained tokens or Tokens (classic) > Delete — verified 2026-10-18 against https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens
- Deleting a PAT that was used to create a deploy key also deletes that deploy key — verified 2026-10-18 against https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens
- Someone else's exposed GitHub token can be submitted for revocation through the REST API — verified 2026-10-18 against https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens
- Direct URLs `github.com/settings/tokens` and `github.com/settings/personal-access-tokens`: UNVERIFIED (the docs only describe menu navigation; `/settings/personal-access-tokens/new` appears only as a creation-template example) — checked 2026-10-18 against https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens
- Remove SSH keys: Settings > Access > SSH and GPG keys > Delete; compare against local `ssh-add -l -E sha256` — verified 2026-10-18 against https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/reviewing-your-ssh-keys
- Revoke an authorized OAuth app: Settings > Integrations > Applications > Authorized OAuth Apps > (kebab) > Revoke, or Revoke all — verified 2026-10-18 against https://docs.github.com/en/apps/oauth-apps/using-oauth-apps/reviewing-your-authorized-oauth-apps
- `gh auth logout` removes credentials locally only and "does not revoke authentication tokens" — verified 2026-10-18 against https://cli.github.com/manual/gh_auth_logout
- To invalidate gh tokens server-side, revoke the "GitHub CLI" app under Settings > Applications; this kills every token the CLI created on all devices — verified 2026-10-18 against https://cli.github.com/manual/gh_auth_logout
- `gh auth refresh` re-runs browser auth to expand or fix scopes on the active account; `--reset-scopes` returns to the minimum set (`repo`, `read:org`, `gist`) — verified 2026-10-18 against https://cli.github.com/manual/gh_auth_refresh
- Whether `gh auth refresh` issues a new token and invalidates the old one: UNVERIFIED (manual does not say) — checked 2026-10-18 against https://cli.github.com/manual/gh_auth_refresh
- Web sessions: Settings > Sessions > Revoke session; mobile devices have a separate Revoke — verified 2026-10-18 against https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/viewing-and-managing-your-sessions

### GitLab

- PAT rotate or revoke: avatar > Edit profile > Access > Personal access tokens > (ellipsis) > Rotate or Revoke; both are immediate and irreversible — verified 2026-10-18 against https://docs.gitlab.com/user/profile/personal_access_tokens/
- Rotate creates a new token with the same scopes and makes the original inactive immediately — verified 2026-10-18 against https://docs.gitlab.com/user/profile/personal_access_tokens/
- The settings page path is `/-/user_settings/personal_access_tokens` (seen in the docs' prefill example) — verified 2026-10-18 against https://docs.gitlab.com/user/profile/personal_access_tokens/
- A glab CLI command for revoking a PAT: UNVERIFIED (not on the PAT page) — checked 2026-10-18 against https://docs.gitlab.com/user/profile/personal_access_tokens/

### npm

- CLI synopsis is `npm token list`, `npm token revoke <id|token>`, `npm token create` — verified 2026-10-18 against https://docs.npmjs.com/cli/v11/commands/npm-token
- `npm token revoke` does not accept the truncated token shown by `npm token list`; pass the id or full token — verified 2026-10-18 against https://docs.npmjs.com/cli/v11/commands/npm-token
- The "Revoking access tokens" how-to page uses `npm token delete <id>` instead; the two npm pages disagree on the subcommand name — verified 2026-10-18 against https://docs.npmjs.com/revoking-access-tokens
- Website: profile picture > Access Tokens > x next to the token (or Delete Selected Tokens) — verified 2026-10-18 against https://docs.npmjs.com/revoking-access-tokens
- Revocation can take up to an hour to take effect — verified 2026-10-18 against https://docs.npmjs.com/revoking-access-tokens

### PyPI

- API tokens live in account settings > API tokens — verified 2026-10-18 against https://pypi.org/help/
- PyPI automatically revokes tokens it finds posted publicly and emails the owner — verified 2026-10-18 against https://pypi.org/help/
- After suspicious activity: reset your password and contact admin@pypi.org — verified 2026-10-18 against https://pypi.org/help/
- The exact UI steps for a user to remove their own API token: UNVERIFIED (the help page does not describe them) — checked 2026-10-18 against https://pypi.org/help/

### AWS

- Rotation: create a second key (`aws iam create-access-key`), switch apps over, check `aws iam get-access-key-last-used`, set the old key Inactive (`aws iam update-access-key`), then `aws iam delete-access-key` — verified 2026-10-18 against https://docs.aws.amazon.com/IAM/latest/UserGuide/id-credentials-access-keys-update.html
- Console: IAM console > Users > (user) > Security credentials > Access keys > Actions > Deactivate, then Delete — verified 2026-10-18 against https://docs.aws.amazon.com/IAM/latest/UserGuide/id-credentials-access-keys-update.html
- A lost secret access key cannot be retrieved; delete it and create a new one — verified 2026-10-18 against https://docs.aws.amazon.com/IAM/latest/UserGuide/id-credentials-access-keys-update.html
- `aws sso logout` removes all cached IAM Identity Center tokens and the temporary credentials derived from them, across all profiles — verified 2026-10-18 against https://docs.aws.amazon.com/cli/latest/reference/sso/logout.html
- Whether `aws sso logout` ends the session server-side: UNVERIFIED (reference page does not say) — checked 2026-10-18 against https://docs.aws.amazon.com/cli/latest/reference/sso/logout.html

### Google Cloud

- `gcloud auth revoke` revokes user-account tokens on the server, then removes the local credential; `--all` applies this to every account — verified 2026-10-18 against https://docs.cloud.google.com/sdk/gcloud/reference/auth/revoke
- For service accounts and workload identity pools, `gcloud auth revoke` only deletes the local credential because "service account tokens are not revocable"; the key stays valid — verified 2026-10-18 against https://docs.cloud.google.com/sdk/gcloud/reference/auth/revoke
- Disable a service-account key with `gcloud iam service-accounts keys disable KEY_ID --iam-account=SA_NAME@PROJECT_ID.iam.gserviceaccount.com --project=PROJECT_ID`; disable first, delete once unused — verified 2026-10-18 against https://docs.cloud.google.com/iam/docs/keys-disable-enable
- Disabling a key does not revoke short-lived credentials already issued from it — verified 2026-10-18 against https://docs.cloud.google.com/iam/docs/keys-disable-enable
- Exact syntax of `gcloud iam service-accounts keys delete`: UNVERIFIED (the disable page links elsewhere) — checked 2026-10-18 against https://docs.cloud.google.com/iam/docs/keys-disable-enable

### Azure

- `az account clear` clears all subscriptions from the CLI's local cache; to clear the current one, use `az logout` — verified 2026-10-18 against https://learn.microsoft.com/en-us/cli/azure/account?view=azure-cli-latest
- `az ad app credential list --id <app>` lists credential metadata; `az ad app credential delete --id <app> --key-id <keyId>` deletes one — verified 2026-10-18 against https://learn.microsoft.com/en-us/cli/azure/ad/app/credential?view=azure-cli-latest
- `az ad app credential reset --id <app>` clears all passwords and keys by default and generates a new password; `--append` adds one instead of overwriting — verified 2026-10-18 against https://learn.microsoft.com/en-us/cli/azure/ad/app/credential?view=azure-cli-latest

### OpenAI

- API keys are managed at https://platform.openai.com/settings/organization/api-keys — verified 2026-10-18 against https://developers.openai.com/api/reference/overview
- Revoking an API key takes effect within a few seconds — verified 2026-10-18 against https://developers.openai.com/api/reference/overview
- Step-by-step key deletion in the dashboard: UNVERIFIED (help.openai.com returned 403) — checked 2026-10-18 against https://help.openai.com/en/articles/9047852-how-can-i-delete-my-api-key

### Anthropic

- If a key may be exposed, revoke it immediately: Claude Console > platform.claude.com/settings/keys > (three dots) > Delete API Key, then Create Key — verified 2026-10-18 against https://support.claude.com/en/articles/8384961-what-should-i-do-if-i-suspect-my-api-key-has-been-compromised

### Google AI Studio / Gemini

- Keys are managed at aistudio.google.com/apikey — verified 2026-10-18 against https://ai.google.dev/gemini-api/docs/api-key
- Compromised key: create a replacement, deploy it, then disable the leaked key in the Cloud console; review billing and API usage — verified 2026-10-18 against https://ai.google.dev/gemini-api/docs/api-key
- Env vars are `GEMINI_API_KEY` or `GOOGLE_API_KEY`; if both are set, `GOOGLE_API_KEY` wins — verified 2026-10-18 against https://ai.google.dev/gemini-api/docs/api-key

### xAI

- Leaked key: console.x.ai > (correct team) > API Keys > (three dots) > Disable key or Delete key, then create a replacement — verified 2026-10-18 against https://docs.x.ai/console/faq/security
- xAI disables keys found through GitHub Secret Scanning and emails the owner — verified 2026-10-18 against https://docs.x.ai/console/faq/security

### Hugging Face

- Leaked token: delete or refresh it from the Access Tokens tab (huggingface.co/settings/tokens) via Manage — verified 2026-10-18 against https://huggingface.co/docs/hub/security-tokens
- Anyone can invalidate a found token with `POST https://huggingface.co/api/credentials/revoke` and body `{"credentials": [...]}`; it always returns 202 — verified 2026-10-18 against https://huggingface.co/docs/hub/security-tokens

### Slack

- Token prefixes: bot `xoxb-`, user `xoxp-`, app-level `xapp-`; rotating app-level `xoxe.xapp-`; workflow `xwfp-` — verified 2026-10-18 against https://docs.slack.dev/authentication/tokens
- A new token can be obtained via OAuth or, for internal integrations, the app management console; `auth.revoke` on a legacy bot token does not uninstall the bot user — verified 2026-10-18 against https://docs.slack.dev/authentication/tokens
- A general "revoke every token type" procedure: UNVERIFIED (the tokens page does not give one) — checked 2026-10-18 against https://docs.slack.dev/authentication/tokens

### Stripe

- Rotate: dashboard.stripe.com/apikeys > (overflow) > Rotate key > Expiration; choosing Now deletes the old key — verified 2026-10-18 against https://docs.stripe.com/keys
- Rotation is the documented response to a compromised secret or restricted key; by default old and new keys both work for up to 7 days — verified 2026-10-18 against https://docs.stripe.com/keys
- Live prefixes are `sk_live_`, `rk_live_`, `pk_live_`; organization keys `sk_org_`; publishable keys are safe to expose — verified 2026-10-18 against https://docs.stripe.com/keys

### Docker Hub

- PAT: app.docker.com > avatar > Account settings > Personal access tokens > actions menu > Deactivate or Delete — verified 2026-10-18 against https://docs.docker.com/security/access-tokens/personal-access-tokens/

### Cloudflare

- Roll a token: My Profile > API Tokens (dash.cloudflare.com/profile/api-tokens) > (three dots) > Roll > Confirm; the previous token is invalidated — verified 2026-10-18 against https://developers.cloudflare.com/fundamentals/api/how-to/roll-token/
- Deleting an API token: UNVERIFIED (not on the roll page) — checked 2026-10-18 against https://developers.cloudflare.com/fundamentals/api/how-to/roll-token/

### SSH keys in general

- Generate a new key with `ssh-keygen -t ed25519 -C "email"`; fallback `ssh-keygen -t rsa -b 4096 -C "email"` — verified 2026-10-18 against https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent
- sshd reads `~/.ssh/authorized_keys` and `~/.ssh/authorized_keys2` by default, one key per line, `#` lines are comments; delete the old key's line on every host — verified 2026-10-18 against https://man.openbsd.org/sshd.8
- Then remove the old public key from each service (GitHub: see above) — verified 2026-10-18 against https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/reviewing-your-ssh-keys

### Browser saved passwords after infostealer exposure

- Chrome: Passwords and autofill > Google Password Manager > Checkup finds breached or weak passwords; Google says to change compromised passwords as soon as you can — verified 2026-10-18 against https://support.google.com/chrome/answer/95606
- Chrome: delete one password, or Settings > Delete all Google Password Manager data — verified 2026-10-18 against https://support.google.com/chrome/answer/95606
- Safari/macOS: Password Monitoring marks passwords "leaked" when found in a data leak; on macOS they are shown in the password list — verified 2026-10-18 against https://support.apple.com/guide/security/password-security-recommendations-sec7f0432063/web
- macOS Passwords app: select the account > Edit > Delete Password; deleted items are recoverable for 30 days — verified 2026-10-18 against https://support.apple.com/guide/passwords/delete-a-password-or-passkey-mchl4c57fbf8/mac
- Firefox: deleting logins in about:logins and Primary Password: UNVERIFIED (support.mozilla.org served a client challenge) — checked 2026-10-18 against https://support.mozilla.org/en-US/kb/edit-or-delete-login-firefox-password-manager
- After an account compromise: change the password, change it on every account that reused it, log out all devices and apps, set up 2-step verification — verified 2026-10-18 against https://www.ncsc.gov.uk/guidance/recovering-a-hacked-account
- An official vendor step list written specifically for infostealer victims: UNVERIFIED (none found from CISA or NCSC) — checked 2026-10-18 against https://www.ncsc.gov.uk/guidance/data-breaches

### Session cookies: sign out everywhere

- Google: Google Account > Security & sign-in > Your devices > Manage all devices > (device) > Sign out; sign out every session with the same device name; shortcut google.com/devices — verified 2026-10-18 against https://support.google.com/accounts/answer/3067630
- Microsoft account: Advanced security options > Sign out everywhere > Sign out; can take up to 24 hours; Xbox needs a separate sign-out — verified 2026-10-18 against https://support.microsoft.com/en-us/accounts-billing/manage/how-to-sign-out-of-your-microsoft-account-everywhere
- GitHub: Settings > Sessions > Revoke session — verified 2026-10-18 against https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/viewing-and-managing-your-sessions

### Crypto wallets (security only)

- MetaMask, compromised Secret Recovery Phrase: create a new wallet on a different browser, profile or device; record the new phrase offline; send remaining funds to it; stop using the old wallet and its accounts — verified 2026-10-18 against https://support.metamask.io/stay-safe/protect-yourself/ive-been-hacked-scammed-unauthorized-transactions-on-my-account/
- MetaMask: unlimited token approvals granted to a dapp are a listed cause of loss; the page links to a guide on revoking them — verified 2026-10-18 against https://support.metamask.io/stay-safe/protect-yourself/ive-been-hacked-scammed-unauthorized-transactions-on-my-account/
- MetaMask: transactions cannot be reversed — verified 2026-10-18 against https://support.metamask.io/stay-safe/protect-yourself/ive-been-hacked-scammed-unauthorized-transactions-on-my-account/
- Ledger, exposed recovery phrase (reset the device, set it up as new, move funds): UNVERIFIED (support.ledger.com pages render client-side and returned no text) — checked 2026-10-18 against https://support.ledger.com/article/4404382075537-zd

## 2. Agent session logs

### Claude Code

- Transcript path is `~/.claude/projects/<project>/<session>.jsonl`: "every message, tool call, and tool result" — verified 2026-10-18 against https://code.claude.com/docs/en/claude-directory
- Subagent transcripts are in `projects/<project>/<session>/subagents/`; large tool outputs spill to `projects/<project>/<session>/tool-results/` — verified 2026-10-18 against https://code.claude.com/docs/en/claude-directory
- Set-aside transcripts are named `<session>.orphaned-<timestamp>-<suffix>.jsonl` and `<session>.jsonl.superseded-<timestamp>` — verified 2026-10-18 against https://code.claude.com/docs/en/claude-directory
- On Windows `~/.claude` is `%USERPROFILE%\.claude`; `CLAUDE_CONFIG_DIR` relocates all of it — verified 2026-10-18 against https://code.claude.com/docs/en/claude-directory
- Transcripts are deleted after `cleanupPeriodDays` (default 30, minimum 1); they are plaintext, not encrypted at rest, and contain any secret a tool read or printed — verified 2026-10-18 against https://code.claude.com/docs/en/claude-directory
- `~/.claude/history.jsonl` holds every typed prompt with timestamp and project path — verified 2026-10-18 against https://code.claude.com/docs/en/claude-directory
- The record schema is not documented — checked 2026-10-18 against https://code.claude.com/docs/en/claude-directory
- One JSON object per line. Top-level `type` values seen: `user`, `assistant`, `attachment`, `mode`, `permission-mode`, `last-prompt`, `ai-title`, `api-request`, `api-request-blob`, `queue-operation`, `atis-latch` — verified 2026-10-18 against local ~/.claude/projects/*/*.jsonl (3 most recent files)
- `user` and `assistant` lines carry `uuid`, `parentUuid`, `sessionId`, `timestamp`, `cwd`, `gitBranch`, `version`, `isSidechain`, `message` — verified 2026-10-18 against local ~/.claude/projects/*/*.jsonl
- Tool call: a `type == "assistant"` line where `message.content[]` contains `{type: "tool_use", id, name, input, caller}` — verified 2026-10-18 against local ~/.claude/projects/*/*.jsonl
- Tool result: a `type == "user"` line where `message.content[]` contains `{type: "tool_result", tool_use_id, content, is_error?}`; the line also has top-level `toolUseResult` and `sourceToolAssistantUUID` — verified 2026-10-18 against local ~/.claude/projects/*/*.jsonl
- `timestamp` is ISO 8601 UTC with milliseconds and `Z` (24 chars, e.g. `YYYY-MM-DDTHH:MM:SS.mmmZ`) — verified 2026-10-18 against local ~/.claude/projects/*/*.jsonl
- These field names are observed, not documented, and may change between versions — verified 2026-10-18 against https://code.claude.com/docs/en/claude-directory

### OpenAI Codex CLI

- Session transcripts are in `$CODEX_HOME/sessions` (default `~/.codex/sessions`); archived ones are in `$CODEX_HOME/archived_sessions` — verified 2026-10-18 against https://learn.chatgpt.com/docs/reference/troubleshooting
- `CODEX_HOME` defaults to `~/.codex`; `history.jsonl` there holds transcripts when history persistence is on (`[history] persistence = "none"` disables it) — verified 2026-10-18 against https://learn.chatgpt.com/docs/config-file/config-advanced
- macOS app logs are in `~/Library/Logs/com.openai.codex/YYYY/MM/DD` — verified 2026-10-18 against https://learn.chatgpt.com/docs/reference/troubleshooting
- File layout `sessions/YYYY/MM/DD/rollout-YYYY-MM-DDTHH-MM-SS-<uuid>.jsonl` — verified 2026-10-18 against local ~/.codex/sessions (not in official docs; also reported by users in https://github.com/openai/codex/issues/24948)
- Windows location of `CODEX_HOME`: UNVERIFIED (docs give no Windows path) — checked 2026-10-18 against https://learn.chatgpt.com/docs/config-file/config-advanced
- Each line has `timestamp`, `type`, `payload` and `ordinal`. Top-level `type` values: `session_meta`, `turn_context`, `response_item`, `event_msg`, `token_usage_record`, `world_state` — verified 2026-10-18 against local ~/.codex/sessions (3 most recent files)
- Function tool call: `type == "response_item"` with `payload.type == "function_call"` and fields `name`, `arguments` (a JSON-encoded string), `call_id`, `id`, optional `namespace` — verified 2026-10-18 against local ~/.codex/sessions (last 60 files)
- Freeform tool call: `payload.type == "custom_tool_call"` with `name` (e.g. `exec`), `input` (string), `call_id`, `status`; result is `custom_tool_call_output` with `call_id`, `output` — verified 2026-10-18 against local ~/.codex/sessions
- Function result: `payload.type == "function_call_output"` with `call_id`, `output`; pair it to the call by `call_id` — verified 2026-10-18 against local ~/.codex/sessions
- In the newest local rollouts the shell tool is logged as `custom_tool_call` named `exec`, not `function_call`; parsers must handle both — verified 2026-10-18 against local ~/.codex/sessions
- `timestamp` is ISO 8601 UTC with milliseconds and `Z` (24 chars); `event_msg` `item_completed` payloads also carry `started_at_ms` and `completed_at_ms` — verified 2026-10-18 against local ~/.codex/sessions

### Cursor

- Logs are opened via the Command Palette "Developer: Open Logs Folder"; Windows parent is `%APPDATA%\Cursor\logs` — community forum only, UNVERIFIED in official docs — checked 2026-10-18 against https://forum.cursor.com/t/cursor-local-logs/12787
- Official Cursor docs do not document a local chat or tool-call log location — checked 2026-10-18 against https://cursor.com/docs and https://cursor.com/llms.txt
- Per-session on-disk tool-call log: UNVERIFIED / none documented. Agent hooks (`~/.cursor/hooks.json`, `<project>/.cursor/hooks.json`) can write one; the docs' own example appends hook JSON to `/tmp/agent-audit.log` — verified 2026-10-18 against https://cursor.com/docs/hooks.md
- Locally, chat state sits in `~/Library/Application Support/Cursor/User/globalStorage/state.vscdb` (SQLite) and `~/.cursor/chats/<hash>/<uuid>/meta.json`; `~/.cursor/projects/<slug>/` holds `worker.log`, `terminals/`, `mcps/` — verified 2026-10-18 against local file names only (contents not read)

### Gemini CLI

- Sessions are stored in `~/.gemini/tmp/<project_hash>/chats/`, per project; each session records prompts, replies, all tool executions (inputs and outputs) and token usage — verified 2026-10-18 against https://geminicli.com/docs/cli/session-management/
- Session retention defaults to 30 days (`general.sessionRetention.maxAge`, default `"30d"`) — verified 2026-10-18 against https://geminicli.com/docs/cli/session-management/
- Checkpoints: git snapshots in `~/.gemini/history/<project_hash>`, conversation JSON in `~/.gemini/tmp/<project_hash>/checkpoints` — verified 2026-10-18 against https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/checkpointing.md
- v0.39.0 switched chat recording from monolithic `chats/session-*.json` to append-only `chats/session-*.jsonl`: metadata header on line 1, then message objects appended; old `.json` still readable — verified 2026-10-18 against https://github.com/google-gemini/gemini-cli/pull/23749
- Local `chats/session-<date>-<id>.jsonl` lines: one header line (`sessionId`, `projectHash`, `startTime`, `lastUpdated`, `kind`); `$set` metadata-update lines; message lines with `id`, `timestamp`, `type` (`user`, `gemini`, `info`, `warning`), `content` — verified 2026-10-18 against local ~/.gemini/tmp/<user>/chats
- Tool call: a `type == "gemini"` line with `toolCalls[]`, each `{id, name, args, result, resultDisplay, status, timestamp, displayName, description, renderOutputAsMarkdown}` — verified 2026-10-18 against local ~/.gemini/tmp/<user>/chats
- `~/.gemini/tmp/<hash>/logs.json` is a JSON array of `{sessionId, messageId, timestamp, type, message}` (user prompts) — verified 2026-10-18 against local ~/.gemini/tmp (not in official docs)
- `$rewindTo` records: UNVERIFIED (third-party description only, not seen locally) — checked 2026-10-18 against https://github.com/google-gemini/gemini-cli/pull/23749
- Windows location: UNVERIFIED — checked 2026-10-18 against https://geminicli.com/docs/cli/session-management/

### OpenCode

- Data dir is `~/.local/share/opencode/` (Windows `%USERPROFILE%\.local\share\opencode`), holding `auth.json` (API keys, OAuth tokens), `log/`, `project/` — verified 2026-10-18 against https://opencode.ai/docs/troubleshooting/
- Session and message data goes in `project/<project-slug>/storage/` for git repos, else `project/global/storage/` — verified 2026-10-18 against https://opencode.ai/docs/troubleshooting/
- Logs are timestamped files (e.g. `2025-01-09T123456.log`) in `log/`; the newest 10 are kept — verified 2026-10-18 against https://opencode.ai/docs/troubleshooting/
- OpenCode storage record and tool-call schema: UNVERIFIED (not documented; OpenCode not installed here) — checked 2026-10-18 against https://opencode.ai/docs/troubleshooting/

## 3. Egress logging going forward

- LuLu (Objective-See, macOS 10.15+, GPL-3.0): install by opening LuLu.dmg, dragging LuLu.app to /Applications, then approving its System Extension and Network Filter — verified 2026-10-18 against https://objective-see.org/products/lulu.html
- LuLu blocks unknown outgoing connections and alerts on each new one. Recommended defaults allow Apple and already-installed programs without alerts. Rules cover outbound only and apply per program — verified 2026-10-18 against https://objective-see.org/products/lulu.html
- LuLu log file and rules file locations: UNVERIFIED (not documented; rules can be exported from the Rules menu) — checked 2026-10-18 against https://objective-see.org/products/lulu.html and https://github.com/objective-see/LuLu
- Little Snitch is commercial with a 30-day trial (demo mode runs 3 hours, restartable); it keeps traffic history up to 12 months and its CLI can log all deny/allow events — verified 2026-10-18 against https://www.obdev.at/products/littlesnitch/index.html
- OpenSnitch install: `sudo apt install ./opensnitch*.deb ./python3-opensnitch-ui*.deb` (Debian/Ubuntu), `sudo dnf install ./opensnitch-*.rpm ./opensnitch-ui-*.rpm`, `sudo pacman -S opensnitch`; then `sudo systemctl enable --now opensnitch` and `opensnitch-ui` — verified 2026-10-18 against https://github.com/evilsocket/opensnitch/wiki/Installation
- OpenSnitch config is `/etc/opensnitchd/default-config.json`, `LogFile` is `/var/log/opensnitchd.log` in the sample config, rules are in `/etc/opensnitchd/rules/` — verified 2026-10-18 against https://github.com/evilsocket/opensnitch/wiki/Configurations
- OpenSnitch GUI connection-event database path: UNVERIFIED — checked 2026-10-18 against https://github.com/evilsocket/opensnitch/wiki/Configurations
- Windows Firewall by default blocks unsolicited incoming traffic and allows all outgoing traffic unless a rule matches — verified 2026-10-18 against https://learn.microsoft.com/en-us/windows/security/operating-system-security/network-security/windows-firewall/
- `-DefaultOutboundAction` defaults to Allow when managing a computer — verified 2026-10-18 against https://learn.microsoft.com/en-us/powershell/module/netsecurity/set-netfirewallprofile
- netsh: `netsh advfirewall set allprofiles logging allowedconnections enable` and `... logging droppedconnections enable` — verified 2026-10-18 against https://learn.microsoft.com/en-us/windows/security/operating-system-security/network-security/windows-firewall/configure-logging
- netsh: `netsh advfirewall set allprofiles logging filename %SystemRoot%\System32\LogFiles\Firewall\pfirewall.log` is a separate command — verified 2026-10-18 against https://learn.microsoft.com/en-us/windows/security/operating-system-security/network-security/windows-firewall/configure-with-command-line
- netsh: `netsh advfirewall set allprofiles logging maxfilesize <KB>` — UNVERIFIED (search-result summary of the 2008 R2 netsh reference; page not read) — checked 2026-10-18 against https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-server-2008-R2-and-2008/cc771920(v=ws.10)
- PowerShell: `Set-NetFirewallProfile -All -LogAllowed True -LogBlocked True -LogFileName %SystemRoot%\System32\LogFiles\Firewall\pfirewall.log -LogMaxSizeKilobytes 20480`; `-LogAllowed True` logs every allowed incoming or outgoing connection — verified 2026-10-18 against https://learn.microsoft.com/en-us/powershell/module/netsecurity/set-netfirewallprofile
- `-LogAllowed` and `-LogBlocked` default to False; default log is `%windir%\system32\logfiles\firewall\pfirewall.log`; `-LogMaxSizeKilobytes` takes 1-32767, default 4096 — verified 2026-10-18 against https://learn.microsoft.com/en-us/powershell/module/netsecurity/set-netfirewallprofile
- Microsoft recommends at least 20,480 KB and one log file per profile — verified 2026-10-18 against https://learn.microsoft.com/en-us/windows/security/operating-system-security/network-security/windows-firewall/configure-logging
- The log folder must grant write access to `NT SERVICE\mpssvc`, or no file is written — verified 2026-10-18 against https://learn.microsoft.com/en-us/windows/security/operating-system-security/network-security/windows-firewall/configure-logging
- Admin is required: "To change the configuration of Windows Firewall on a device, you must have administative rights" — verified 2026-10-18 against https://learn.microsoft.com/en-us/windows/security/operating-system-security/network-security/windows-firewall/tools
- The pfirewall.log records connections but not the process that made them; mapping to a process needs another source — UNVERIFIED — not checked against a sample log

## 4. Registry abuse channels

- npm: on the package page, click Report malware, fill in the form, Send Report; general support at https://npmjs.com/support/ — verified 2026-10-18 against https://docs.npmjs.com/reporting-malware-in-an-npm-package/
- PyPI: sign in, open the project page, click "Report project as malware" at the bottom of the sidebar; include an inspector.pypi.io link to the bad lines — verified 2026-10-18 against https://pypi.org/security/
- PyPI: security@pypi.org is for vulnerabilities in PyPI itself, not for malicious projects — verified 2026-10-18 against https://pypi.org/security/
- GitHub: repo page > About sidebar > Report repository; content "..." > Report content; or the form at https://support.github.com/contact/report-abuse — verified 2026-10-18 against https://docs.github.com/en/communities/maintaining-your-safety-on-github/reporting-abuse-or-spam
- Open VSX: email openvsx@eclipse-foundation.org; Eclipse vulnerability reporting is at eclipse.org/security/ — verified 2026-10-18 against https://blogs.eclipse.org/post/mika%C3%ABl-barbero/open-vsx-security-update-october-2025
- Open VSX in-site report button: UNVERIFIED — checked 2026-10-18 against https://blogs.eclipse.org/post/mika%C3%ABl-barbero/open-vsx-security-update-october-2025
- VS Code Marketplace: extension page > More Info section > Report a concern; first reply within one business day — verified 2026-10-18 against https://code.visualstudio.com/docs/configure/extensions/extension-runtime-security
- ClawHub / OpenClaw: signed-in users use the Report skill button on the skill page; packages have a reporting command/API (name not given) — verified 2026-10-18 against https://docs.openclaw.ai/clawhub/moderation
- skills.sh: report through Vercel's coordinated disclosure at https://security.vercel.com/ and include the skill URL — verified 2026-10-18 against https://www.skills.sh/contact
- Official MCP Registry: report abuse to the underlying package registry (npm, PyPI, Docker Hub) and open a GitHub issue on modelcontextprotocol/registry titled `Abuse report: ...` — verified 2026-10-18 against https://modelcontextprotocol.io/registry/faq
- Smithery: none published (no abuse, security or report channel in docs or llms.txt) — checked 2026-10-18 against https://smithery.ai/docs and https://smithery.ai/docs/llms.txt
- Hugging Face: repo three-dot menu > Report the repository; this opens a public discussion — verified 2026-10-18 against https://huggingface.co/docs/hub/moderation
- Hugging Face private email channel (safety@ / security@huggingface.co): UNVERIFIED (search-result summary only) — checked 2026-10-18 against https://huggingface.co/content-policy

## 5. Running processes by executable path, without psutil

- Linux procps `ps`: `-A`/`-e` select all; `-o` takes a list; if every header is empty (`pid=`) no header line is printed; `args` (aliases `command`, `cmd`) is the full command line and `comm` is only the executable name — verified 2026-10-18 against https://man7.org/linux/man-pages/man1/ps.1.html
- Linux `ps`: piped output width is undefined, so use `-ww` for unlimited width; unavailable args show as `[name]` — verified 2026-10-18 against https://man7.org/linux/man-pages/man1/ps.1.html
- Portable command: `ps -axww -o pid=,command=`, where `a` with `x` lists all processes on both procps and BSD — verified 2026-10-18 against https://man7.org/linux/man-pages/man1/ps.1.html and https://man.freebsd.org/cgi/man.cgi?query=ps&manpath=macOS+15.0
- BSD `ps`: `-a` shows all users' processes, `-x` adds ones without a controlling terminal, an empty `=` header suppresses the header line, `command` is "command and arguments", `-w` twice means unlimited width — verified 2026-10-18 against https://man.freebsd.org/cgi/man.cgi?query=ps&manpath=macOS+15.0 (served FreeBSD 15.1's page, not Apple's)
- macOS `ps` matches the BSD behaviour above: UNVERIFIED against an Apple-published manpage (Apple does not host one; local `man` not read per instructions)
- `command` is argv, not a resolved executable path; argv[0] can be relative or spoofed. On Linux, `/proc/<pid>/exe` gives the real path — UNVERIFIED in this pass
- Windows: `Get-CimInstance -ClassName Win32_Process | Select-Object ProcessId, ExecutablePath, CommandLine`; the cmdlet is Windows-only and documented for PowerShell 5.1, 7.4, 7.5, 7.6, 7.7 — verified 2026-10-18 against https://learn.microsoft.com/en-us/powershell/module/cimcmdlets/get-ciminstance
- `Win32_Process.ExecutablePath` is "Path to the executable file of the process" and carries the `SeDebugPrivilege` qualifier; `CommandLine` is the command line "if applicable"; `ProcessId` values are reused after exit — verified 2026-10-18 against https://learn.microsoft.com/en-us/windows/win32/cimwin32prov/win32-process
- Without elevation, ExecutablePath/CommandLine come back null for other users' and protected processes — UNVERIFIED (inferred from the SeDebugPrivilege qualifier, not stated)

## Notes on data/rotation.json

- Direct URLs not quoted by the provider's docs: `https://pypi.org/manage/account/`, `https://gitlab.com/-/user_settings/personal_access_tokens` (path from the GitLab docs' prefill example), `https://api.slack.com/apps`, `https://passwords.google.com/`: UNVERIFIED as exact landing pages
- MetaMask's Chrome extension id `nkbihfbeogaeaoehlefnkodbefgpgknn` in the `metamask-srp` matcher: UNVERIFIED in this pass
- Browser credential file names in the matchers (`Login Data`, `Cookies`, `logins.json`, `key4.db`, `cookies.sqlite`, `Cookies.binarycookies`): UNVERIFIED in this pass; they are detection heuristics only
- No Ledger entry is included because its guidance could not be read (see section 1)
