# Verified claims

Every file path, config key, CLI flag, API and registry URL unpick relies on, with where and when it was checked.
Format: `<claim> — verified <date> against <URL or repo@commit>`. Lines marked UNVERIFIED are gated behind a warning in code and README.

## inventory


One claim per line. Generated from data/locations.json plus a few path-less claims.

- claude-code: user skills-root at `~/.claude/skills` on mac/linux — verified 2026-10-18 against https://code.claude.com/docs/en/skills
- claude-code: user skills-root at `%USERPROFILE%\.claude\skills` on windows — verified 2026-10-18 against https://code.claude.com/docs/en/skills
- claude-code: project skills-root at `.claude/skills` on mac/linux/windows — verified 2026-10-18 against https://code.claude.com/docs/en/skills
- claude-code: user skills-root at `/Library/Application Support/ClaudeCode/.claude/skills` on mac — verified 2026-10-18 against https://code.claude.com/docs/en/skills
- claude-code: user skills-root at `/etc/claude-code/.claude/skills` on linux — verified 2026-10-18 against https://code.claude.com/docs/en/skills
- claude-code: user skills-root at `C:\Program Files\ClaudeCode\.claude\skills` on windows — verified 2026-10-18 against https://code.claude.com/docs/en/skills
- claude-code: user plugin-root at `~/.claude/plugins/cache` on mac/linux — verified 2026-10-18 against https://code.claude.com/docs/en/plugins/loading
- claude-code: user plugin-root at `%USERPROFILE%\.claude\plugins\cache` on windows — verified 2026-10-18 against https://code.claude.com/docs/en/plugins/loading
- claude-code: user plugin-root at `~/.claude/plugins/marketplaces` on mac/linux — verified 2026-10-18 against https://code.claude.com/docs/en/plugins/loading
- claude-code: user plugin-root at `%USERPROFILE%\.claude\plugins\marketplaces` on windows — verified 2026-10-18 against https://code.claude.com/docs/en/plugins/loading
- claude-code: user plugin-root at `~/.claude/plugins/synced` on mac/linux — verified 2026-10-18 against https://code.claude.com/docs/en/plugins/loading
- claude-code: user plugin-root at `%USERPROFILE%\.claude\plugins\synced` on windows — verified 2026-10-18 against https://code.claude.com/docs/en/plugins/loading
- claude-code: user plugin-root at `~/.claude/plugins/known_marketplaces.json` on mac/linux — verified 2026-10-18 against https://code.claude.com/docs/en/plugins/loading
- claude-code: user plugin-root at `%USERPROFILE%\.claude\plugins\known_marketplaces.json` on windows — verified 2026-10-18 against https://code.claude.com/docs/en/plugins/loading
- claude-code: user plugin-root at `~/.claude/plugins/installed_plugins.json` on mac/linux — verified 2026-10-18 against https://code.claude.com/docs/en/plugins/loading
- claude-code: user plugin-root at `%USERPROFILE%\.claude\plugins\installed_plugins.json` on windows — verified 2026-10-18 against https://code.claude.com/docs/en/plugins/loading
- claude-code: user settings-hooks at `~/.claude/settings.json` on mac/linux, hooks key `hooks` — verified 2026-10-18 against https://code.claude.com/docs/en/hooks
- claude-code: user settings-hooks at `%USERPROFILE%\.claude\settings.json` on windows, hooks key `hooks` — verified 2026-10-18 against https://code.claude.com/docs/en/hooks
- claude-code: project settings-hooks at `.claude/settings.json` on mac/linux/windows, hooks key `hooks` — verified 2026-10-18 against https://code.claude.com/docs/en/hooks
- claude-code: project settings-hooks at `.claude/settings.local.json` on mac/linux/windows, hooks key `hooks` — verified 2026-10-18 against https://code.claude.com/docs/en/hooks
- claude-code: user mcp-config at `~/.claude.json` on mac/linux, MCP key `mcpServers` — verified 2026-10-18 against https://code.claude.com/docs/en/mcp
- claude-code: user mcp-config at `%USERPROFILE%\.claude.json` on windows, MCP key `mcpServers` — verified 2026-10-18 against https://code.claude.com/docs/en/mcp
- claude-code: project mcp-config at `.mcp.json` on mac/linux/windows, MCP key `mcpServers` — verified 2026-10-18 against https://code.claude.com/docs/en/mcp
- claude-code: user settings-hooks at `/Library/Application Support/ClaudeCode/managed-settings.json` on mac, hooks key `hooks` — verified 2026-10-18 against https://code.claude.com/docs/en/managed-settings
- claude-code: user mcp-config at `/Library/Application Support/ClaudeCode/managed-mcp.json` on mac, MCP key `mcpServers` — verified 2026-10-18 against https://code.claude.com/docs/en/managed-mcp
- claude-code: user instructions-file at `/Library/Application Support/ClaudeCode/CLAUDE.md` on mac — verified 2026-10-18 against https://code.claude.com/docs/en/memory
- claude-code: user settings-hooks at `/etc/claude-code/managed-settings.json` on linux, hooks key `hooks` — verified 2026-10-18 against https://code.claude.com/docs/en/managed-settings
- claude-code: user mcp-config at `/etc/claude-code/managed-mcp.json` on linux, MCP key `mcpServers` — verified 2026-10-18 against https://code.claude.com/docs/en/managed-mcp
- claude-code: user instructions-file at `/etc/claude-code/CLAUDE.md` on linux — verified 2026-10-18 against https://code.claude.com/docs/en/memory
- claude-code: user settings-hooks at `C:\Program Files\ClaudeCode\managed-settings.json` on windows, hooks key `hooks` — verified 2026-10-18 against https://code.claude.com/docs/en/managed-settings
- claude-code: user mcp-config at `C:\Program Files\ClaudeCode\managed-mcp.json` on windows, MCP key `mcpServers` — verified 2026-10-18 against https://code.claude.com/docs/en/managed-mcp
- claude-code: user instructions-file at `C:\Program Files\ClaudeCode\CLAUDE.md` on windows — verified 2026-10-18 against https://code.claude.com/docs/en/memory
- claude-code: user instructions-file at `~/.claude/CLAUDE.md` on mac/linux — verified 2026-10-18 against https://code.claude.com/docs/en/memory
- claude-code: user instructions-file at `%USERPROFILE%\.claude\CLAUDE.md` on windows — verified 2026-10-18 against https://code.claude.com/docs/en/memory
- claude-code: project instructions-file at `CLAUDE.md` on mac/linux/windows — verified 2026-10-18 against https://code.claude.com/docs/en/memory
- claude-code: project instructions-file at `.claude/CLAUDE.md` on mac/linux/windows — verified 2026-10-18 against https://code.claude.com/docs/en/memory
- claude-code: project instructions-file at `CLAUDE.local.md` on mac/linux/windows — verified 2026-10-18 against https://code.claude.com/docs/en/memory
- claude-code: project instructions-file at `AGENTS.md` on mac/linux/windows — verified 2026-10-18 against https://code.claude.com/docs/en/memory
- claude-code: project rules-dir at `.claude/rules` on mac/linux/windows — verified 2026-10-18 against https://code.claude.com/docs/en/memory
- claude-code: user rules-dir at `~/.claude/rules` on mac/linux — verified 2026-10-18 against https://code.claude.com/docs/en/memory
- claude-code: user rules-dir at `%USERPROFILE%\.claude\rules` on windows — verified 2026-10-18 against https://code.claude.com/docs/en/memory
- claude-desktop: user mcp-config at `~/Library/Application Support/Claude/claude_desktop_config.json` on mac, MCP key `mcpServers` — verified 2026-10-18 against https://modelcontextprotocol.io/docs/develop/connect-local-servers
- claude-desktop: user mcp-config at `%APPDATA%\Claude\claude_desktop_config.json` on windows, MCP key `mcpServers` — verified 2026-10-18 against https://modelcontextprotocol.io/docs/develop/connect-local-servers
- claude-desktop: user mcp-config at `~/.config/Claude/claude_desktop_config.json` on linux, MCP key `mcpServers` — UNVERIFIED 2026-10-18 against https://hooklayer.dev/guides/claude-desktop-config-json (Official MCP doc says Claude Desktop ships for Linux but gives only macOS and Windows paths. Linux path is from third-party guides only.)
- cursor: project rules-file at `.cursorrules` on mac/linux/windows — verified 2026-10-18 against https://forum.cursor.com/t/project-rule-in-cursorrules-not-applied-in-agent-chat-works-in-cursor-rules/154309/3
- cursor: project rules-dir at `.cursor/rules/**/*.mdc` on mac/linux/windows — verified 2026-10-18 against https://cursor.com/docs/context/rules
- cursor: project instructions-file at `AGENTS.md` on mac/linux/windows — verified 2026-10-18 against https://cursor.com/docs/context/rules
- cursor: user mcp-config at `~/.cursor/mcp.json` on mac/linux, MCP key `mcpServers` — verified 2026-10-18 against https://cursor.com/docs/context/mcp
- cursor: user mcp-config at `%USERPROFILE%\.cursor\mcp.json` on windows, MCP key `mcpServers` — verified 2026-10-18 against https://cursor.com/docs/context/mcp
- cursor: project mcp-config at `.cursor/mcp.json` on mac/linux/windows, MCP key `mcpServers` — verified 2026-10-18 against https://cursor.com/docs/context/mcp
- cursor: user skills-root at `~/.cursor/skills` on mac/linux — verified 2026-10-18 against https://cursor.com/help/customization/skills
- cursor: user skills-root at `%USERPROFILE%\.cursor\skills` on windows — verified 2026-10-18 against https://cursor.com/help/customization/skills
- cursor: project skills-root at `.cursor/skills` on mac/linux/windows — verified 2026-10-18 against https://cursor.com/help/customization/skills
- cursor: user settings-hooks at `~/.cursor/hooks.json` on mac/linux, hooks key `hooks` — verified 2026-10-18 against https://cursor.com/docs/agent/hooks
- cursor: user settings-hooks at `%USERPROFILE%\.cursor\hooks.json` on windows, hooks key `hooks` — verified 2026-10-18 against https://cursor.com/docs/agent/hooks
- cursor: project settings-hooks at `.cursor/hooks.json` on mac/linux/windows, hooks key `hooks` — verified 2026-10-18 against https://cursor.com/docs/agent/hooks
- cursor: user settings-hooks at `/Library/Application Support/Cursor/hooks.json` on mac, hooks key `hooks` — verified 2026-10-18 against https://cursor.com/docs/agent/hooks
- cursor: user settings-hooks at `/etc/cursor/hooks.json` on linux, hooks key `hooks` — verified 2026-10-18 against https://cursor.com/docs/agent/hooks
- cursor: user settings-hooks at `C:\ProgramData\Cursor\hooks.json` on windows, hooks key `hooks` — verified 2026-10-18 against https://cursor.com/docs/agent/hooks
- github-copilot: project instructions-file at `.github/copilot-instructions.md` on mac/linux/windows — verified 2026-10-18 against https://docs.github.com/en/copilot/how-tos/configure-custom-instructions/add-repository-instructions
- github-copilot: project rules-dir at `.github/instructions/**/*.instructions.md` on mac/linux/windows — verified 2026-10-18 against https://docs.github.com/en/copilot/how-tos/configure-custom-instructions/add-repository-instructions
- github-copilot: project instructions-file at `AGENTS.md` on mac/linux/windows — verified 2026-10-18 against https://docs.github.com/en/copilot/how-tos/configure-custom-instructions/add-repository-instructions
- github-copilot: project instructions-file at `CLAUDE.md` on mac/linux/windows — verified 2026-10-18 against https://docs.github.com/en/copilot/how-tos/configure-custom-instructions/add-repository-instructions
- github-copilot: project instructions-file at `GEMINI.md` on mac/linux/windows — verified 2026-10-18 against https://docs.github.com/en/copilot/how-tos/configure-custom-instructions/add-repository-instructions
- github-copilot: project rules-dir at `.github/prompts/*.prompt.md` on mac/linux/windows — verified 2026-10-18 against https://code.visualstudio.com/docs/copilot/customization/prompt-files
- github-copilot: user instructions-file at `~/.copilot/copilot-instructions.md` on mac/linux — verified 2026-10-18 against https://code.visualstudio.com/docs/copilot/customization/custom-instructions
- github-copilot: user instructions-file at `%USERPROFILE%\.copilot\copilot-instructions.md` on windows — verified 2026-10-18 against https://code.visualstudio.com/docs/copilot/customization/custom-instructions
- github-copilot: user rules-dir at `~/.copilot/instructions` on mac/linux — verified 2026-10-18 against https://code.visualstudio.com/docs/copilot/customization/custom-instructions
- github-copilot: user rules-dir at `%USERPROFILE%\.copilot\instructions` on windows — verified 2026-10-18 against https://code.visualstudio.com/docs/copilot/customization/custom-instructions
- github-copilot: project skills-root at `.github/skills` on mac/linux/windows — verified 2026-10-18 against https://code.visualstudio.com/docs/copilot/customization/agent-skills
- github-copilot: user skills-root at `~/.copilot/skills` on mac/linux — verified 2026-10-18 against https://code.visualstudio.com/docs/copilot/customization/agent-skills
- github-copilot: user skills-root at `%USERPROFILE%\.copilot\skills` on windows — verified 2026-10-18 against https://code.visualstudio.com/docs/copilot/customization/agent-skills
- github-copilot: user mcp-config at `~/.copilot/mcp-config.json` on mac/linux, MCP key `mcpServers` — verified 2026-10-18 against https://code.visualstudio.com/docs/copilot/customization/mcp-servers
- github-copilot: user mcp-config at `%USERPROFILE%\.copilot\mcp-config.json` on windows, MCP key `mcpServers` — verified 2026-10-18 against https://code.visualstudio.com/docs/copilot/customization/mcp-servers
- vscode: project mcp-config at `.vscode/mcp.json` on mac/linux/windows, MCP key `servers` — verified 2026-10-18 against https://code.visualstudio.com/docs/copilot/customization/mcp-servers
- vscode: project mcp-config at `.mcp.json` on mac/linux/windows, MCP key `mcpServers` — verified 2026-10-18 against https://code.visualstudio.com/docs/copilot/customization/mcp-servers
- vscode: user mcp-config at `~/Library/Application Support/Code/User/mcp.json` on mac, MCP key `servers` — verified 2026-10-18 against microsoft/vscode@1694e2264f0a4406d813d50aa23f176e5484b344 (src/vs/platform/userDataProfile/common/userDataProfile.ts) + https://code.visualstudio.com/docs/configure/settings
- vscode: user rules-dir at `~/Library/Application Support/Code/User/prompts` on mac — verified 2026-10-18 against microsoft/vscode@1694e2264f0a4406d813d50aa23f176e5484b344 (src/vs/platform/userDataProfile/common/userDataProfile.ts) + https://code.visualstudio.com/docs/copilot/customization/prompt-files
- vscode: user mcp-config at `~/Library/Application Support/Code/User/settings.json` on mac, MCP key `mcp` — UNVERIFIED 2026-10-18 against https://code.visualstudio.com/docs/configure/settings (settings.json path verified. A legacy 'mcp' key inside settings.json is not confirmed in current docs; scan it anyway.)
- vscode: user mcp-config at `~/.config/Code/User/mcp.json` on linux, MCP key `servers` — verified 2026-10-18 against microsoft/vscode@1694e2264f0a4406d813d50aa23f176e5484b344 (src/vs/platform/userDataProfile/common/userDataProfile.ts) + https://code.visualstudio.com/docs/configure/settings
- vscode: user rules-dir at `~/.config/Code/User/prompts` on linux — verified 2026-10-18 against microsoft/vscode@1694e2264f0a4406d813d50aa23f176e5484b344 (src/vs/platform/userDataProfile/common/userDataProfile.ts) + https://code.visualstudio.com/docs/copilot/customization/prompt-files
- vscode: user mcp-config at `~/.config/Code/User/settings.json` on linux, MCP key `mcp` — UNVERIFIED 2026-10-18 against https://code.visualstudio.com/docs/configure/settings (settings.json path verified. A legacy 'mcp' key inside settings.json is not confirmed in current docs; scan it anyway.)
- vscode: user mcp-config at `%APPDATA%\Code\User\mcp.json` on windows, MCP key `servers` — verified 2026-10-18 against microsoft/vscode@1694e2264f0a4406d813d50aa23f176e5484b344 (src/vs/platform/userDataProfile/common/userDataProfile.ts) + https://code.visualstudio.com/docs/configure/settings
- vscode: user rules-dir at `%APPDATA%\Code\User\prompts` on windows — verified 2026-10-18 against microsoft/vscode@1694e2264f0a4406d813d50aa23f176e5484b344 (src/vs/platform/userDataProfile/common/userDataProfile.ts) + https://code.visualstudio.com/docs/copilot/customization/prompt-files
- vscode: user mcp-config at `%APPDATA%\Code\User\settings.json` on windows, MCP key `mcp` — UNVERIFIED 2026-10-18 against https://code.visualstudio.com/docs/configure/settings (settings.json path verified. A legacy 'mcp' key inside settings.json is not confirmed in current docs; scan it anyway.)
- vscode: project mcp-config at `.devcontainer/devcontainer.json` on mac/linux/windows, MCP key `customizations.vscode.mcp.servers` — verified 2026-10-18 against https://code.visualstudio.com/docs/copilot/customization/mcp-servers
- codex: user mcp-config at `~/.codex/config.toml` on mac/linux, MCP key `mcp_servers`, hooks key `hooks` — verified 2026-10-18 against https://learn.chatgpt.com/docs/extend/mcp?surface=cli
- codex: user mcp-config at `%USERPROFILE%\.codex\config.toml` on windows, MCP key `mcp_servers`, hooks key `hooks` — verified 2026-10-18 against https://learn.chatgpt.com/docs/extend/mcp?surface=cli
- codex: project mcp-config at `.codex/config.toml` on mac/linux/windows, MCP key `mcp_servers`, hooks key `hooks` — verified 2026-10-18 against https://learn.chatgpt.com/docs/extend/mcp?surface=cli
- codex: user settings-hooks at `~/.codex/hooks.json` on mac/linux, hooks key `hooks` — verified 2026-10-18 against https://learn.chatgpt.com/docs/hooks
- codex: user settings-hooks at `%USERPROFILE%\.codex\hooks.json` on windows, hooks key `hooks` — verified 2026-10-18 against https://learn.chatgpt.com/docs/hooks
- codex: project settings-hooks at `.codex/hooks.json` on mac/linux/windows, hooks key `hooks` — verified 2026-10-18 against https://learn.chatgpt.com/docs/hooks
- codex: user instructions-file at `~/.codex/AGENTS.md` on mac/linux — verified 2026-10-18 against https://learn.chatgpt.com/docs/agent-configuration/agents-md
- codex: user instructions-file at `%USERPROFILE%\.codex\AGENTS.md` on windows — verified 2026-10-18 against https://learn.chatgpt.com/docs/agent-configuration/agents-md
- codex: project instructions-file at `AGENTS.md` on mac/linux/windows — verified 2026-10-18 against https://learn.chatgpt.com/docs/agent-configuration/agents-md
- codex: project instructions-file at `AGENTS.override.md` on mac/linux/windows — verified 2026-10-18 against https://learn.chatgpt.com/docs/agent-configuration/agents-md
- codex: user skills-root at `~/.agents/skills` on mac/linux — verified 2026-10-18 against https://learn.chatgpt.com/docs/build-skills
- codex: user skills-root at `%USERPROFILE%\.agents\skills` on windows — verified 2026-10-18 against https://learn.chatgpt.com/docs/build-skills
- codex: project skills-root at `.agents/skills` on mac/linux/windows — verified 2026-10-18 against https://learn.chatgpt.com/docs/build-skills
- codex: user skills-root at `/etc/codex/skills` on mac/linux — verified 2026-10-18 against https://learn.chatgpt.com/docs/build-skills
- codex: user skills-root at `~/.codex/skills` on mac/linux — verified 2026-10-18 against openai/codex@8c076942cb70fba8e5c4732c23f1faabc4aed484 (codex-rs/exec-server/src/discoverV2/capability_locations.rs)
- codex: user skills-root at `%USERPROFILE%\.codex\skills` on windows — verified 2026-10-18 against openai/codex@8c076942cb70fba8e5c4732c23f1faabc4aed484 (codex-rs/exec-server/src/discoverV2/capability_locations.rs)
- codex: user plugin-root at `~/.codex/plugins/cache` on mac/linux — verified 2026-10-18 against openai/codex@8c076942cb70fba8e5c4732c23f1faabc4aed484 (codex-rs/core-plugin-common/src/installed.rs PLUGINS_CACHE_DIR)
- codex: user plugin-root at `%USERPROFILE%\.codex\plugins\cache` on windows — verified 2026-10-18 against openai/codex@8c076942cb70fba8e5c4732c23f1faabc4aed484 (codex-rs/core-plugin-common/src/installed.rs PLUGINS_CACHE_DIR)
- windsurf: user mcp-config at `~/.config/devin/mcp_config.json` on mac/linux, MCP key `mcpServers` — verified 2026-10-18 against https://docs.devin.ai/desktop/cascade/mcp
- windsurf: user mcp-config at `%APPDATA%\devin\mcp_config.json` on windows, MCP key `mcpServers` — verified 2026-10-18 against https://docs.devin.ai/desktop/cascade/mcp
- windsurf: user mcp-config at `~/.codeium/windsurf/mcp_config.json` on mac/linux, MCP key `mcpServers` — UNVERIFIED 2026-10-18 against https://fast.io/resources/windsurf-mcp-setup-guide/ (Pre-rename Windsurf path. Current official docs no longer list it; only third-party guides do. Whether Devin Desktop still reads it is unconfirmed. Keep scanning: older installs have it.)
- windsurf: user mcp-config at `%USERPROFILE%\.codeium\windsurf\mcp_config.json` on windows, MCP key `mcpServers` — UNVERIFIED 2026-10-18 against https://fast.io/resources/windsurf-mcp-setup-guide/ (Pre-rename Windsurf path. Current official docs no longer list it; only third-party guides do. Whether Devin Desktop still reads it is unconfirmed. Keep scanning: older installs have it.)
- windsurf: user rules-file at `~/.codeium/windsurf/memories/global_rules.md` on mac/linux — verified 2026-10-18 against https://docs.devin.ai/desktop/cascade/memories
- windsurf: user rules-file at `%USERPROFILE%\.codeium\windsurf\memories\global_rules.md` on windows — verified 2026-10-18 against https://docs.devin.ai/desktop/cascade/memories
- windsurf: project rules-dir at `.devin/rules/*.md` on mac/linux/windows — verified 2026-10-18 against https://docs.devin.ai/desktop/cascade/memories
- windsurf: project rules-dir at `.windsurf/rules/*.md` on mac/linux/windows — verified 2026-10-18 against https://docs.devin.ai/desktop/cascade/memories
- windsurf: project rules-file at `.windsurfrules` on mac/linux/windows — verified 2026-10-18 against https://docs.devin.ai/desktop/cascade/memories
- windsurf: project instructions-file at `AGENTS.md` on mac/linux/windows — verified 2026-10-18 against https://docs.devin.ai/desktop/cascade/memories
- windsurf: user rules-dir at `/Library/Application Support/Devin/rules/*.md` on mac — verified 2026-10-18 against https://docs.devin.ai/desktop/cascade/memories
- windsurf: user rules-dir at `/Library/Application Support/Windsurf/rules/*.md` on mac — verified 2026-10-18 against https://docs.devin.ai/desktop/cascade/memories
- windsurf: user rules-dir at `/etc/devin/rules/*.md` on linux — verified 2026-10-18 against https://docs.devin.ai/desktop/cascade/memories
- windsurf: user rules-dir at `/etc/windsurf/rules/*.md` on linux — verified 2026-10-18 against https://docs.devin.ai/desktop/cascade/memories
- windsurf: user rules-dir at `C:\ProgramData\Devin\rules\*.md` on windows — verified 2026-10-18 against https://docs.devin.ai/desktop/cascade/memories
- windsurf: user rules-dir at `C:\ProgramData\Windsurf\rules\*.md` on windows — verified 2026-10-18 against https://docs.devin.ai/desktop/cascade/memories
- windsurf: user skills-root at `~/.codeium/windsurf/skills` on mac/linux — verified 2026-10-18 against https://docs.devin.ai/desktop/cascade/skills
- windsurf: user skills-root at `%USERPROFILE%\.codeium\windsurf\skills` on windows — verified 2026-10-18 against https://docs.devin.ai/desktop/cascade/skills
- windsurf: user skills-root at `~/.config/devin/skills` on mac/linux — verified 2026-10-18 against https://docs.devin.ai/desktop/cascade/skills
- windsurf: project skills-root at `.devin/skills` on mac/linux/windows — verified 2026-10-18 against https://docs.devin.ai/desktop/cascade/skills
- windsurf: project skills-root at `.windsurf/skills` on mac/linux/windows — verified 2026-10-18 against https://docs.devin.ai/desktop/cascade/skills
- windsurf: user settings-hooks at `~/.codeium/windsurf/hooks.json` on mac/linux, hooks key `hooks` — verified 2026-10-18 against https://docs.devin.ai/desktop/cascade/hooks
- windsurf: user settings-hooks at `%USERPROFILE%\.codeium\windsurf\hooks.json` on windows, hooks key `hooks` — verified 2026-10-18 against https://docs.devin.ai/desktop/cascade/hooks
- windsurf: project settings-hooks at `.devin/hooks.json` on mac/linux/windows, hooks key `hooks` — verified 2026-10-18 against https://docs.devin.ai/desktop/cascade/hooks
- windsurf: project settings-hooks at `.windsurf/hooks.json` on mac/linux/windows, hooks key `hooks` — verified 2026-10-18 against https://docs.devin.ai/desktop/cascade/hooks
- cline: user mcp-config at `~/.cline/data/settings/cline_mcp_settings.json` on mac/linux, MCP key `mcpServers` — verified 2026-10-18 against https://docs.cline.bot/getting-started/config
- cline: user mcp-config at `%USERPROFILE%\.cline\data\settings\cline_mcp_settings.json` on windows, MCP key `mcpServers` — verified 2026-10-18 against https://docs.cline.bot/getting-started/config
- cline: user mcp-config at `~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json` on mac, MCP key `mcpServers` — verified 2026-10-18 against cline/cline@a42df8c8d5fd9d9f9a9073589baffe32ea9bb2f0 (apps/vscode/src/hosts/vscode/mcp-settings-legacy-migration.ts)
- cline: user mcp-config at `~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json` on linux, MCP key `mcpServers` — verified 2026-10-18 against cline/cline@a42df8c8d5fd9d9f9a9073589baffe32ea9bb2f0 (apps/vscode/src/hosts/vscode/mcp-settings-legacy-migration.ts)
- cline: user mcp-config at `%APPDATA%\Code\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json` on windows, MCP key `mcpServers` — verified 2026-10-18 against cline/cline@a42df8c8d5fd9d9f9a9073589baffe32ea9bb2f0 (apps/vscode/src/hosts/vscode/mcp-settings-legacy-migration.ts)
- cline: user mcp-config at `~/Documents/Cline/MCP/cline_mcp_settings.json` on mac/linux, MCP key `mcpServers` — verified 2026-10-18 against cline/cline@a42df8c8d5fd9d9f9a9073589baffe32ea9bb2f0 (apps/vscode/src/hosts/vscode/mcp-settings-legacy-migration.ts)
- cline: user mcp-config at `%USERPROFILE%\Documents\Cline\MCP\cline_mcp_settings.json` on windows, MCP key `mcpServers` — verified 2026-10-18 against cline/cline@a42df8c8d5fd9d9f9a9073589baffe32ea9bb2f0 (apps/vscode/src/hosts/vscode/mcp-settings-legacy-migration.ts)
- cline: project rules-dir at `.clinerules` on mac/linux/windows — verified 2026-10-18 against https://docs.cline.bot/features/cline-rules
- cline: project rules-dir at `.cline/rules` on mac/linux/windows — verified 2026-10-18 against https://docs.cline.bot/features/cline-rules
- cline: user rules-dir at `~/Documents/Cline/Rules` on mac/linux — verified 2026-10-18 against https://docs.cline.bot/features/cline-rules
- cline: user rules-dir at `%USERPROFILE%\Documents\Cline\Rules` on windows — verified 2026-10-18 against https://docs.cline.bot/features/cline-rules
- cline: user rules-dir at `~/.cline/rules` on mac/linux — verified 2026-10-18 against https://docs.cline.bot/features/cline-rules
- cline: user rules-dir at `%USERPROFILE%\.cline\rules` on windows — verified 2026-10-18 against https://docs.cline.bot/features/cline-rules
- cline: user instructions-file at `~/.agents/AGENTS.md` on mac/linux — verified 2026-10-18 against https://docs.cline.bot/features/cline-rules
- cline: user instructions-file at `%USERPROFILE%\.agents\AGENTS.md` on windows — verified 2026-10-18 against https://docs.cline.bot/features/cline-rules
- cline: user skills-root at `~/.cline/skills` on mac/linux — verified 2026-10-18 against https://docs.cline.bot/getting-started/config
- cline: user skills-root at `%USERPROFILE%\.cline\skills` on windows — verified 2026-10-18 against https://docs.cline.bot/getting-started/config
- cline: project skills-root at `.cline/skills` on mac/linux/windows — verified 2026-10-18 against https://docs.cline.bot/getting-started/config
- cline: user settings-hooks at `~/.cline/hooks` on mac/linux — verified 2026-10-18 against https://docs.cline.bot/getting-started/config
- cline: user settings-hooks at `%USERPROFILE%\.cline\hooks` on windows — verified 2026-10-18 against https://docs.cline.bot/getting-started/config
- cline: project settings-hooks at `.cline/hooks` on mac/linux/windows — verified 2026-10-18 against https://docs.cline.bot/getting-started/config
- continue: user mcp-config at `~/.continue/config.yaml` on mac/linux, MCP key `mcpServers` — verified 2026-10-18 against https://docs.continue.dev/customize/deep-dives/configuration
- continue: user mcp-config at `%USERPROFILE%\.continue\config.yaml` on windows, MCP key `mcpServers` — verified 2026-10-18 against https://docs.continue.dev/customize/deep-dives/configuration
- continue: project mcp-config at `.continue/mcpServers/*` on mac/linux/windows, MCP key `mcpServers` — verified 2026-10-18 against https://docs.continue.dev/customize/deep-dives/mcp
- continue: project rules-dir at `.continue/rules` on mac/linux/windows — verified 2026-10-18 against https://docs.continue.dev/customize/deep-dives/rules
- gemini-cli: user mcp-config at `~/.gemini/settings.json` on mac/linux, MCP key `mcpServers`, hooks key `hooks` — verified 2026-10-18 against https://github.com/google-gemini/gemini-cli/blob/main/docs/reference/configuration.md (google-gemini/gemini-cli@ed96faedfd5571f055c44f2c9509d62321d1138d)
- gemini-cli: user mcp-config at `%USERPROFILE%\.gemini\settings.json` on windows, MCP key `mcpServers`, hooks key `hooks` — verified 2026-10-18 against https://github.com/google-gemini/gemini-cli/blob/main/docs/reference/configuration.md (google-gemini/gemini-cli@ed96faedfd5571f055c44f2c9509d62321d1138d)
- gemini-cli: project mcp-config at `.gemini/settings.json` on mac/linux/windows, MCP key `mcpServers`, hooks key `hooks` — verified 2026-10-18 against https://github.com/google-gemini/gemini-cli/blob/main/docs/reference/configuration.md (google-gemini/gemini-cli@ed96faedfd5571f055c44f2c9509d62321d1138d)
- gemini-cli: user mcp-config at `/etc/gemini-cli/settings.json` on linux, MCP key `mcpServers`, hooks key `hooks` — verified 2026-10-18 against https://github.com/google-gemini/gemini-cli/blob/main/docs/reference/configuration.md (google-gemini/gemini-cli@ed96faedfd5571f055c44f2c9509d62321d1138d)
- gemini-cli: user mcp-config at `C:\ProgramData\gemini-cli\settings.json` on windows, MCP key `mcpServers`, hooks key `hooks` — verified 2026-10-18 against https://github.com/google-gemini/gemini-cli/blob/main/docs/reference/configuration.md (google-gemini/gemini-cli@ed96faedfd5571f055c44f2c9509d62321d1138d)
- gemini-cli: user mcp-config at `/Library/Application Support/GeminiCli/settings.json` on mac, MCP key `mcpServers`, hooks key `hooks` — verified 2026-10-18 against https://github.com/google-gemini/gemini-cli/blob/main/docs/reference/configuration.md (google-gemini/gemini-cli@ed96faedfd5571f055c44f2c9509d62321d1138d)
- gemini-cli: user instructions-file at `~/.gemini/GEMINI.md` on mac/linux — verified 2026-10-18 against https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/gemini-md.md (google-gemini/gemini-cli@ed96faedfd5571f055c44f2c9509d62321d1138d)
- gemini-cli: user instructions-file at `%USERPROFILE%\.gemini\GEMINI.md` on windows — verified 2026-10-18 against https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/gemini-md.md (google-gemini/gemini-cli@ed96faedfd5571f055c44f2c9509d62321d1138d)
- gemini-cli: project instructions-file at `GEMINI.md` on mac/linux/windows — verified 2026-10-18 against https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/gemini-md.md (google-gemini/gemini-cli@ed96faedfd5571f055c44f2c9509d62321d1138d)
- gemini-cli: user extension-root at `~/.gemini/extensions` on mac/linux, MCP key `mcpServers` — verified 2026-10-18 against https://github.com/google-gemini/gemini-cli/blob/main/docs/extensions/reference.md (google-gemini/gemini-cli@ed96faedfd5571f055c44f2c9509d62321d1138d)
- gemini-cli: user extension-root at `%USERPROFILE%\.gemini\extensions` on windows, MCP key `mcpServers` — verified 2026-10-18 against https://github.com/google-gemini/gemini-cli/blob/main/docs/extensions/reference.md (google-gemini/gemini-cli@ed96faedfd5571f055c44f2c9509d62321d1138d)
- gemini-cli: user skills-root at `~/.gemini/skills` on mac/linux — verified 2026-10-18 against https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/skills.md (google-gemini/gemini-cli@ed96faedfd5571f055c44f2c9509d62321d1138d)
- gemini-cli: user skills-root at `%USERPROFILE%\.gemini\skills` on windows — verified 2026-10-18 against https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/skills.md (google-gemini/gemini-cli@ed96faedfd5571f055c44f2c9509d62321d1138d)
- gemini-cli: project skills-root at `.gemini/skills` on mac/linux/windows — verified 2026-10-18 against https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/skills.md (google-gemini/gemini-cli@ed96faedfd5571f055c44f2c9509d62321d1138d)
- jetbrains-junie: user mcp-config at `~/.junie/mcp/mcp.json` on mac/linux, MCP key `mcpServers` — verified 2026-10-18 against https://junie.jetbrains.com/docs/junie-cli-mcp-configuration.html
- jetbrains-junie: user mcp-config at `%USERPROFILE%\.junie\mcp\mcp.json` on windows, MCP key `mcpServers` — verified 2026-10-18 against https://junie.jetbrains.com/docs/junie-cli-mcp-configuration.html
- jetbrains-junie: project mcp-config at `.junie/mcp/mcp.json` on mac/linux/windows, MCP key `mcpServers` — verified 2026-10-18 against https://junie.jetbrains.com/docs/junie-cli-mcp-configuration.html
- jetbrains-junie: project instructions-file at `.junie/AGENTS.md` on mac/linux/windows — verified 2026-10-18 against https://junie.jetbrains.com/docs/guidelines-and-memory.html
- jetbrains-junie: project rules-dir at `.junie/rules/*.md` on mac/linux/windows — verified 2026-10-18 against https://junie.jetbrains.com/docs/guidelines-and-memory.html
- jetbrains-junie: project instructions-file at `.junie/guidelines.md` on mac/linux/windows — verified 2026-10-18 against https://junie.jetbrains.com/docs/guidelines-and-memory.html
- jetbrains-junie: user instructions-file at `~/.junie/AGENTS.md` on mac/linux — verified 2026-10-18 against https://junie.jetbrains.com/docs/guidelines-and-memory.html
- jetbrains-junie: user instructions-file at `%USERPROFILE%\.junie\AGENTS.md` on windows — verified 2026-10-18 against https://junie.jetbrains.com/docs/guidelines-and-memory.html
- jetbrains-junie: user skills-root at `~/.junie/skills` on mac/linux — verified 2026-10-18 against https://junie.jetbrains.com/docs/agent-skills.html
- jetbrains-junie: user skills-root at `%USERPROFILE%\.junie\skills` on windows — verified 2026-10-18 against https://junie.jetbrains.com/docs/agent-skills.html
- jetbrains-junie: project skills-root at `.junie/skills` on mac/linux/windows — verified 2026-10-18 against https://junie.jetbrains.com/docs/agent-skills.html
- zed: user mcp-config at `~/.config/zed/settings.json` on mac/linux, MCP key `context_servers` — verified 2026-10-18 against https://github.com/zed-industries/zed/blob/main/docs/src/configuring-zed.md (zed-industries/zed@56934ec0560bce8929025497411de7f5322fb6ca)
- zed: user mcp-config at `%APPDATA%\Zed\settings.json` on windows, MCP key `context_servers` — verified 2026-10-18 against https://github.com/zed-industries/zed/blob/main/docs/src/configuring-zed.md (zed-industries/zed@56934ec0560bce8929025497411de7f5322fb6ca)
- zed: project mcp-config at `.zed/settings.json` on mac/linux/windows, MCP key `context_servers` — verified 2026-10-18 against https://github.com/zed-industries/zed/blob/main/docs/src/configuring-zed.md (zed-industries/zed@56934ec0560bce8929025497411de7f5322fb6ca)
- zed: user instructions-file at `~/.config/zed/AGENTS.md` on mac/linux — verified 2026-10-18 against https://github.com/zed-industries/zed/blob/main/docs/src/ai/instructions.md (zed-industries/zed@56934ec0560bce8929025497411de7f5322fb6ca)
- zed: user instructions-file at `%APPDATA%\Zed\AGENTS.md` on windows — verified 2026-10-18 against https://github.com/zed-industries/zed/blob/main/docs/src/ai/instructions.md (zed-industries/zed@56934ec0560bce8929025497411de7f5322fb6ca)
- zed: project rules-file at `.rules` on mac/linux/windows — verified 2026-10-18 against https://github.com/zed-industries/zed/blob/main/docs/src/ai/rules.md (zed-industries/zed@56934ec0560bce8929025497411de7f5322fb6ca)
- zed: project rules-file at `.cursorrules` on mac/linux/windows — verified 2026-10-18 against https://github.com/zed-industries/zed/blob/main/docs/src/ai/rules.md (zed-industries/zed@56934ec0560bce8929025497411de7f5322fb6ca)
- zed: project rules-file at `.windsurfrules` on mac/linux/windows — verified 2026-10-18 against https://github.com/zed-industries/zed/blob/main/docs/src/ai/rules.md (zed-industries/zed@56934ec0560bce8929025497411de7f5322fb6ca)
- zed: project rules-file at `.clinerules` on mac/linux/windows — verified 2026-10-18 against https://github.com/zed-industries/zed/blob/main/docs/src/ai/rules.md (zed-industries/zed@56934ec0560bce8929025497411de7f5322fb6ca)
- zed: project rules-file at `.github/copilot-instructions.md` on mac/linux/windows — verified 2026-10-18 against https://github.com/zed-industries/zed/blob/main/docs/src/ai/rules.md (zed-industries/zed@56934ec0560bce8929025497411de7f5322fb6ca)
- zed: project rules-file at `AGENTS.md` on mac/linux/windows — verified 2026-10-18 against https://github.com/zed-industries/zed/blob/main/docs/src/ai/rules.md (zed-industries/zed@56934ec0560bce8929025497411de7f5322fb6ca)
- zed: project rules-file at `CLAUDE.md` on mac/linux/windows — verified 2026-10-18 against https://github.com/zed-industries/zed/blob/main/docs/src/ai/rules.md (zed-industries/zed@56934ec0560bce8929025497411de7f5322fb6ca)
- zed: project rules-file at `GEMINI.md` on mac/linux/windows — verified 2026-10-18 against https://github.com/zed-industries/zed/blob/main/docs/src/ai/rules.md (zed-industries/zed@56934ec0560bce8929025497411de7f5322fb6ca)
- zed: user skills-root at `~/.agents/skills` on mac/linux — verified 2026-10-18 against https://github.com/zed-industries/zed/blob/main/docs/src/ai/skills.md (zed-industries/zed@56934ec0560bce8929025497411de7f5322fb6ca)
- zed: user skills-root at `%USERPROFILE%\.agents\skills` on windows — verified 2026-10-18 against https://github.com/zed-industries/zed/blob/main/docs/src/ai/skills.md (zed-industries/zed@56934ec0560bce8929025497411de7f5322fb6ca)
- zed: project skills-root at `.agents/skills` on mac/linux/windows — verified 2026-10-18 against https://github.com/zed-industries/zed/blob/main/docs/src/ai/skills.md (zed-industries/zed@56934ec0560bce8929025497411de7f5322fb6ca)
- zed: user extension-root at `~/Library/Application Support/Zed/extensions/installed` on mac — verified 2026-10-18 against https://zed.dev/docs/configuring-zed
- zed: user extension-root at `~/.local/share/zed/extensions/installed` on linux — verified 2026-10-18 against https://zed.dev/docs/configuring-zed
- zed: user extension-root at `%LOCALAPPDATA%\Zed\extensions\installed` on windows — verified 2026-10-18 against https://zed.dev/docs/configuring-zed
- openclaw: project skills-root at `skills` on mac/linux/windows — verified 2026-10-18 against https://docs.openclaw.ai/tools/skills
- openclaw: project skills-root at `.agents/skills` on mac/linux/windows — verified 2026-10-18 against https://docs.openclaw.ai/tools/skills
- openclaw: user skills-root at `~/.openclaw/skills` on mac/linux — verified 2026-10-18 against https://docs.openclaw.ai/tools/skills
- openclaw: user skills-root at `%USERPROFILE%\.openclaw\skills` on windows — verified 2026-10-18 against https://docs.openclaw.ai/tools/skills
- openclaw: user mcp-config at `~/.openclaw/openclaw.json` on mac/linux, MCP key `mcp.servers` — verified 2026-10-18 against https://docs.openclaw.ai/gateway/configuration + https://docs.openclaw.ai/cli/mcp
- openclaw: user mcp-config at `%USERPROFILE%\.openclaw\openclaw.json` on windows, MCP key `mcp.servers` — verified 2026-10-18 against https://docs.openclaw.ai/gateway/configuration + https://docs.openclaw.ai/cli/mcp
- kiro: user mcp-config at `~/.kiro/settings/mcp.json` on mac/linux, MCP key `mcpServers` — verified 2026-10-18 against https://kiro.dev/docs/mcp/configuration/
- kiro: user mcp-config at `%USERPROFILE%\.kiro\settings\mcp.json` on windows, MCP key `mcpServers` — verified 2026-10-18 against https://kiro.dev/docs/mcp/configuration/
- kiro: project mcp-config at `.kiro/settings/mcp.json` on mac/linux/windows, MCP key `mcpServers` — verified 2026-10-18 against https://kiro.dev/docs/mcp/configuration/
- kiro: user rules-dir at `~/.kiro/steering` on mac/linux — verified 2026-10-18 against https://kiro.dev/docs/steering/
- kiro: user rules-dir at `%USERPROFILE%\.kiro\steering` on windows — verified 2026-10-18 against https://kiro.dev/docs/steering/
- kiro: project rules-dir at `.kiro/steering` on mac/linux/windows — verified 2026-10-18 against https://kiro.dev/docs/steering/
- kiro: project instructions-file at `AGENTS.md` on mac/linux/windows — verified 2026-10-18 against https://kiro.dev/docs/steering/
- kiro: user skills-root at `~/.kiro/skills` on mac/linux — verified 2026-10-18 against https://kiro.dev/docs/skills/
- kiro: user skills-root at `%USERPROFILE%\.kiro\skills` on windows — verified 2026-10-18 against https://kiro.dev/docs/skills/
- kiro: project skills-root at `.kiro/skills` on mac/linux/windows — verified 2026-10-18 against https://kiro.dev/docs/skills/
- amazon-q: project rules-dir at `.amazonq/rules` on mac/linux/windows — verified 2026-10-18 against https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/context-project-rules.html
- amazon-q: user mcp-config at `~/.aws/amazonq/default.json` on mac/linux, MCP key `mcpServers` — verified 2026-10-18 against https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/mcp-ide.html
- amazon-q: user mcp-config at `%USERPROFILE%\.aws\amazonq\default.json` on windows, MCP key `mcpServers` — verified 2026-10-18 against https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/mcp-ide.html
- amazon-q: project mcp-config at `.amazonq/default.json` on mac/linux/windows, MCP key `mcpServers` — verified 2026-10-18 against https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/mcp-ide.html
- amazon-q: user mcp-config at `~/.aws/amazonq/mcp.json` on mac/linux, MCP key `mcpServers` — verified 2026-10-18 against https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/mcp-ide.html
- amazon-q: user mcp-config at `%USERPROFILE%\.aws\amazonq\mcp.json` on windows, MCP key `mcpServers` — verified 2026-10-18 against https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/mcp-ide.html
- amazon-q: project mcp-config at `.amazonq/mcp.json` on mac/linux/windows, MCP key `mcpServers` — verified 2026-10-18 against https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/mcp-ide.html
- amazon-q: user mcp-config at `~/.aws/amazonq/cli-agents` on mac/linux, MCP key `mcpServers` — verified 2026-10-18 against https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/qdev-mcp.html
- amazon-q: user mcp-config at `%USERPROFILE%\.aws\amazonq\cli-agents` on windows, MCP key `mcpServers` — verified 2026-10-18 against https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/qdev-mcp.html
- amazon-q: user mcp-config at `~/.aws/amazonq/agents/default.json` on mac/linux, MCP key `mcpServers` — verified 2026-10-18 against https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/qdev-mcp.html
- amazon-q: user mcp-config at `%USERPROFILE%\.aws\amazonq\agents\default.json` on windows, MCP key `mcpServers` — verified 2026-10-18 against https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/qdev-mcp.html
- roo-code: project mcp-config at `.roo/mcp.json` on mac/linux/windows, MCP key `mcpServers` — verified 2026-10-18 against https://roocodeinc.github.io/Roo-Code/features/mcp/using-mcp-in-roo
- roo-code: user mcp-config at `~/Library/Application Support/Code/User/globalStorage/rooveterinaryinc.roo-cline/settings/mcp_settings.json` on mac, MCP key `mcpServers` — UNVERIFIED 2026-10-18 against https://roocodeinc.github.io/Roo-Code/features/mcp/using-mcp-in-roo (Docs name the file mcp_settings.json but give no path; extension ID and directory not confirmed.)
- roo-code: user mcp-config at `~/.config/Code/User/globalStorage/rooveterinaryinc.roo-cline/settings/mcp_settings.json` on linux, MCP key `mcpServers` — UNVERIFIED 2026-10-18 against https://roocodeinc.github.io/Roo-Code/features/mcp/using-mcp-in-roo (Docs name the file mcp_settings.json but give no path; extension ID and directory not confirmed.)
- roo-code: user mcp-config at `%APPDATA%\Code\User\globalStorage\rooveterinaryinc.roo-cline\settings\mcp_settings.json` on windows, MCP key `mcpServers` — UNVERIFIED 2026-10-18 against https://roocodeinc.github.io/Roo-Code/features/mcp/using-mcp-in-roo (Docs name the file mcp_settings.json but give no path; extension ID and directory not confirmed.)
- roo-code: project rules-dir at `.roo/rules` on mac/linux/windows — verified 2026-10-18 against https://roocodeinc.github.io/Roo-Code/features/custom-instructions
- roo-code: user rules-dir at `~/.roo/rules` on mac/linux — verified 2026-10-18 against https://roocodeinc.github.io/Roo-Code/features/custom-instructions
- roo-code: user rules-dir at `%USERPROFILE%\.roo\rules` on windows — verified 2026-10-18 against https://roocodeinc.github.io/Roo-Code/features/custom-instructions
- roo-code: project rules-file at `.roorules` on mac/linux/windows — verified 2026-10-18 against https://roocodeinc.github.io/Roo-Code/features/custom-instructions
- roo-code: project instructions-file at `AGENTS.md` on mac/linux/windows — verified 2026-10-18 against https://roocodeinc.github.io/Roo-Code/features/custom-instructions
- opencode: user mcp-config at `~/.config/opencode/opencode.json` on mac/linux, MCP key `mcp` — verified 2026-10-18 against https://opencode.ai/docs/config/
- opencode: user mcp-config at `%USERPROFILE%\.config\opencode\opencode.json` on windows, MCP key `mcp` — verified 2026-10-18 against https://opencode.ai/docs/config/
- opencode: project mcp-config at `opencode.json` on mac/linux/windows, MCP key `mcp` — verified 2026-10-18 against https://opencode.ai/docs/config/
- opencode: user skills-root at `~/.config/opencode/skills` on mac/linux — verified 2026-10-18 against https://opencode.ai/docs/skills/
- opencode: user skills-root at `%USERPROFILE%\.config\opencode\skills` on windows — verified 2026-10-18 against https://opencode.ai/docs/skills/
- opencode: project skills-root at `.opencode/skills` on mac/linux/windows — verified 2026-10-18 against https://opencode.ai/docs/skills/
- opencode: user plugin-root at `~/.config/opencode/plugins` on mac/linux — verified 2026-10-18 against https://opencode.ai/docs/config/
- opencode: user plugin-root at `%USERPROFILE%\.config\opencode\plugins` on windows — verified 2026-10-18 against https://opencode.ai/docs/config/
- opencode: project plugin-root at `.opencode/plugins` on mac/linux/windows — verified 2026-10-18 against https://opencode.ai/docs/config/
- opencode: project instructions-file at `AGENTS.md` on mac/linux/windows — verified 2026-10-18 against https://opencode.ai/docs/rules/
- opencode: user instructions-file at `~/.config/opencode/AGENTS.md` on mac/linux — verified 2026-10-18 against https://opencode.ai/docs/rules/
- opencode: user instructions-file at `%USERPROFILE%\.config\opencode\AGENTS.md` on windows — verified 2026-10-18 against https://opencode.ai/docs/rules/
- goose: user mcp-config at `~/.config/goose/config.yaml` on mac/linux, MCP key `extensions` — verified 2026-10-18 against https://goose-docs.ai/docs/guides/config-files/
- goose: user mcp-config at `%APPDATA%\Block\goose\config\config.yaml` on windows, MCP key `extensions` — verified 2026-10-18 against https://goose-docs.ai/docs/guides/config-files/
- goose: user instructions-file at `~/.config/goose/.goosehints` on mac/linux — verified 2026-10-18 against https://goose-docs.ai/docs/guides/context-engineering/using-goosehints/
- goose: project instructions-file at `.goosehints` on mac/linux/windows — verified 2026-10-18 against https://goose-docs.ai/docs/guides/context-engineering/using-goosehints/
- goose: project instructions-file at `AGENTS.md` on mac/linux/windows — verified 2026-10-18 against https://goose-docs.ai/docs/guides/context-engineering/using-goosehints/
- goose: user skills-root at `~/.agents/skills` on mac/linux — verified 2026-10-18 against https://goose-docs.ai/docs/guides/context-engineering/using-skills/
- goose: user skills-root at `%USERPROFILE%\.agents\skills` on windows — verified 2026-10-18 against https://goose-docs.ai/docs/guides/context-engineering/using-skills/
- goose: project skills-root at `.agents/skills` on mac/linux/windows — verified 2026-10-18 against https://goose-docs.ai/docs/guides/context-engineering/using-skills/
- aider: user instructions-file at `~/.aider.conf.yml` on mac/linux — verified 2026-10-18 against https://aider.chat/docs/config/aider_conf.html
- aider: user instructions-file at `%USERPROFILE%\.aider.conf.yml` on windows — verified 2026-10-18 against https://aider.chat/docs/config/aider_conf.html
- aider: project instructions-file at `.aider.conf.yml` on mac/linux/windows — verified 2026-10-18 against https://aider.chat/docs/config/aider_conf.html
- aider: project instructions-file at `CONVENTIONS.md` on mac/linux/windows — verified 2026-10-18 against https://aider.chat/docs/usage/conventions.html
- grok-build: user mcp-config at `~/.grok/config.toml` on mac/linux, MCP key `mcp_servers` — verified 2026-10-18 against https://docs.x.ai/build/settings
- grok-build: user mcp-config at `%USERPROFILE%\.grok\config.toml` on windows, MCP key `mcp_servers` — verified 2026-10-18 against https://docs.x.ai/build/settings
- grok-build: project mcp-config at `.grok/config.toml` on mac/linux/windows, MCP key `mcp_servers` — verified 2026-10-18 against https://docs.x.ai/build/settings
- grok-build: user skills-root at `~/.grok/skills` on mac/linux — verified 2026-10-18 against https://docs.x.ai/build/features/skills-plugins-marketplaces
- grok-build: user skills-root at `%USERPROFILE%\.grok\skills` on windows — verified 2026-10-18 against https://docs.x.ai/build/features/skills-plugins-marketplaces
- grok-build: project skills-root at `.grok/skills` on mac/linux/windows — verified 2026-10-18 against https://docs.x.ai/build/features/skills-plugins-marketplaces
- grok-build: user plugin-root at `~/.grok/plugins` on mac/linux — verified 2026-10-18 against https://docs.x.ai/build/features/skills-plugins-marketplaces
- grok-build: user plugin-root at `%USERPROFILE%\.grok\plugins` on windows — verified 2026-10-18 against https://docs.x.ai/build/features/skills-plugins-marketplaces
- grok-build: project plugin-root at `.grok/plugins` on mac/linux/windows — verified 2026-10-18 against https://docs.x.ai/build/features/skills-plugins-marketplaces
- grok-build: user settings-hooks at `~/.grok/hooks/*.json` on mac/linux, hooks key `hooks` — verified 2026-10-18 against https://docs.x.ai/build/features/hooks
- grok-build: user settings-hooks at `%USERPROFILE%\.grok\hooks\*.json` on windows, hooks key `hooks` — verified 2026-10-18 against https://docs.x.ai/build/features/hooks
- grok-build: project settings-hooks at `.grok/hooks/*.json` on mac/linux/windows, hooks key `hooks` — verified 2026-10-18 against https://docs.x.ai/build/features/hooks
- grok-build: project instructions-file at `AGENTS.md` on mac/linux/windows — verified 2026-10-18 against https://docs.x.ai/build/features/skills-plugins-marketplaces
- augment: user mcp-config at `~/.augment/settings.json` on mac/linux, MCP key `mcpServers`, hooks key `hooks` — verified 2026-10-18 against https://docs.augmentcode.com/cli/integrations
- augment: user mcp-config at `%USERPROFILE%\.augment\settings.json` on windows, MCP key `mcpServers`, hooks key `hooks` — verified 2026-10-18 against https://docs.augmentcode.com/cli/integrations
- augment: project settings-hooks at `.augment/settings.json` on mac/linux/windows, hooks key `hooks` — verified 2026-10-18 against https://docs.augmentcode.com/cli/hooks.md
- augment: project settings-hooks at `.augment/settings.local.json` on mac/linux/windows, hooks key `hooks` — verified 2026-10-18 against https://docs.augmentcode.com/cli/hooks.md
- augment: user settings-hooks at `/etc/augment/settings.json` on mac/linux, hooks key `hooks` — verified 2026-10-18 against https://docs.augmentcode.com/cli/hooks.md
- augment: user settings-hooks at `C:\ProgramData\Augment\settings.json` on windows, hooks key `hooks` — verified 2026-10-18 against https://docs.augmentcode.com/cli/hooks.md
- augment: project rules-dir at `.augment/rules` on mac/linux/windows — verified 2026-10-18 against https://docs.augmentcode.com/cli/rules.md
- augment: user rules-dir at `~/.augment/rules` on mac/linux — verified 2026-10-18 against https://docs.augmentcode.com/cli/rules.md
- augment: user rules-dir at `%USERPROFILE%\.augment\rules` on windows — verified 2026-10-18 against https://docs.augmentcode.com/cli/rules.md
- augment: project rules-file at `.augment-guidelines` on mac/linux/windows — verified 2026-10-18 against https://docs.augmentcode.com/cli/rules.md
- augment: user skills-root at `~/.augment/skills` on mac/linux — verified 2026-10-18 against https://docs.augmentcode.com/cli/skills.md
- augment: user skills-root at `%USERPROFILE%\.augment\skills` on windows — verified 2026-10-18 against https://docs.augmentcode.com/cli/skills.md
- augment: project skills-root at `.augment/skills` on mac/linux/windows — verified 2026-10-18 against https://docs.augmentcode.com/cli/skills.md
- amp: user mcp-config at `~/.config/amp/settings.json` on mac/linux, MCP key `amp.mcpServers` — verified 2026-10-18 against https://ampcode.com/docs/cli/settings + https://ampcode.com/docs/customize/mcp
- amp: user mcp-config at `%USERPROFILE%\.config\amp\settings.json` on windows, MCP key `amp.mcpServers` — verified 2026-10-18 against https://ampcode.com/docs/cli/settings + https://ampcode.com/docs/customize/mcp
- amp: project mcp-config at `.amp/settings.json` on mac/linux/windows, MCP key `amp.mcpServers` — verified 2026-10-18 against https://ampcode.com/docs/customize/mcp
- amp: user instructions-file at `~/.config/amp/AGENTS.md` on mac/linux — verified 2026-10-18 against https://ampcode.com/docs/customize/agents-md
- amp: user instructions-file at `%USERPROFILE%\.config\amp\AGENTS.md` on windows — verified 2026-10-18 against https://ampcode.com/docs/customize/agents-md
- amp: project instructions-file at `AGENTS.md` on mac/linux/windows — verified 2026-10-18 against https://ampcode.com/docs/customize/agents-md
- amp: user skills-root at `~/.config/agents/skills` on mac/linux — verified 2026-10-18 against https://ampcode.com/docs/customize/skills
- amp: user skills-root at `%USERPROFILE%\.config\agents\skills` on windows — verified 2026-10-18 against https://ampcode.com/docs/customize/skills
- amp: user skills-root at `~/.config/amp/skills` on mac/linux — verified 2026-10-18 against https://ampcode.com/docs/customize/skills
- amp: user skills-root at `%USERPROFILE%\.config\amp\skills` on windows — verified 2026-10-18 against https://ampcode.com/docs/customize/skills
- amp: project skills-root at `.agents/skills` on mac/linux/windows — verified 2026-10-18 against https://ampcode.com/docs/customize/skills
- JetBrains AI Assistant MCP servers are configured in Settings | Tools | AI Assistant | Model Context Protocol (MCP); the docs give no on-disk file (global or project level, JSON key mcpServers in the dialog) — verified 2026-10-18 against https://www.jetbrains.com/help/ai-assistant/mcp.html
- JetBrains AI Assistant on-disk storage of MCP server config (IDE options XML location) — UNVERIFIED 2026-10-18 against not documented; not checked in source
- Cursor user rules are stored in app settings (Customize > Rules), not in a documented file — verified 2026-10-18 against https://cursor.com/docs/context/rules
- Windsurf has been renamed Devin Desktop; docs.windsurf.com redirects to docs.devin.ai — verified 2026-10-18 against https://docs.devin.ai/desktop/cascade/mcp
- developers.openai.com/codex/* now 308-redirects to learn.chatgpt.com/docs/* — verified 2026-10-18 against https://developers.openai.com/codex/mcp
- Claude Code does not scan a project's .claude/plugins/ directory — verified 2026-10-18 against https://code.claude.com/docs/en/plugins/loading
- Continue global ~/.continue/rules directory — UNVERIFIED 2026-10-18 against not in current docs

## backends


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

## judges


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

## fallback-judge


One line per claim. UNVERIFIED means we could not confirm it, not that it is false.
No model weights were downloaded. Sizes and sha256 come from the Hugging Face tree API LFS metadata (`/api/models/<repo>/tree/main`); params, architecture and context come from `/api/models/<repo>` and `?expand[]=gguf`.

## Recommendation

- Pick: `ibm-granite/granite-4.1-3b` via `ibm-granite/granite-4.1-3b-GGUF` file `granite-4.1-3b-Q4_K_M.gguf`. It meets every requirement: Apache-2.0, 3.40B, non-reasoning instruct, GGUF published by IBM, 2.10 GB, released April 2026. Its chat template has no `<think>` block, so the JSON grammar does not have to fight a reasoning preamble.
- Alternate 1: `Qwen/Qwen3-4B-Instruct-2507` via `unsloth/Qwen3-4B-Instruct-2507-GGUF`. It has the highest IFEval score of the group, but 4.02B params is just over the 4B cap, and Qwen publishes no GGUF of it.
- Alternate 2: `mistralai/Ministral-3-3B-Instruct-2512` via `mistralai/Ministral-3-3B-Instruct-2512-GGUF`. Apache-2.0, GGUF from Mistral itself, but Mistral publishes no IFEval number for it.

## Pick: IBM Granite 4.1 3B

- Repo `ibm-granite/granite-4.1-3b` at commit `c0650403e44e78ec0262dab1c90914c65b196c4e` (lastModified 2026-05-04) — verified 2026-10-18 against https://huggingface.co/api/models/ibm-granite/granite-4.1-3b
- License apache-2.0 (card metadata). The repo has no LICENSE file; the card links https://www.apache.org/licenses/LICENSE-2.0 — verified 2026-10-18 against ibm-granite/granite-4.1-3b@c0650403e4 README.md and the tree listing
- 3,402,836,480 params (safetensors total; GGUF metadata agrees) — verified 2026-10-18 against https://huggingface.co/api/models/ibm-granite/granite-4.1-3b and https://huggingface.co/api/models/ibm-granite/granite-4.1-3b-GGUF?expand[]=gguf
- "3B parameter long-context instruct model", release date April 29th, 2026 — verified 2026-10-18 against ibm-granite/granite-4.1-3b@c0650403e4 README.md
- IFEval Avg 82.30 for 3B (8B 87.06, 30B 89.65) — verified 2026-10-18 against ibm-granite/granite-4.1-3b@c0650403e4 README.md
- Context length 131072 (config `max_position_embeddings` and GGUF `context_length`) — verified 2026-10-18 against ibm-granite/granite-4.1-3b@c0650403e4 config.json and the GGUF metadata API
- The GGUF chat template has no `think` / `enable_thinking` handling — verified 2026-10-18 against the `gguf.chat_template` field of https://huggingface.co/api/models/ibm-granite/granite-4.1-3b-GGUF?expand[]=gguf
- GGUF architecture `granite` — verified 2026-10-18 against https://huggingface.co/api/models/ibm-granite/granite-4.1-3b-GGUF?expand[]=gguf
- GGUF repo `ibm-granite/granite-4.1-3b-GGUF` at commit `ab4701481089b58a082ef63cc1cee738887293ff` (lastModified 2026-04-20) — verified 2026-10-18 against https://huggingface.co/api/models/ibm-granite/granite-4.1-3b-GGUF
- `granite-4.1-3b-Q4_K_M.gguf`: 2,099,501,664 bytes, sha256 `662b0626cd58f443baea23559b469df6576a81d349649c59413b36a9fb32eb29` — verified 2026-10-18 against ibm-granite/granite-4.1-3b-GGUF@ab47014810 tree LFS metadata
- `granite-4.1-3b-Q4_0.gguf`: 1,984,608,864 bytes, sha256 `d7e739eb4572c43d20dd6536c12fa29e1fc81b8f48e64048265d558e0441cb0e` — verified 2026-10-18 against ibm-granite/granite-4.1-3b-GGUF@ab47014810 tree LFS metadata
- Pin download URL form: `https://huggingface.co/ibm-granite/granite-4.1-3b-GGUF/resolve/ab4701481089b58a082ef63cc1cee738887293ff/granite-4.1-3b-Q4_K_M.gguf` — UNVERIFIED (URL pattern only; not fetched, because no weights were to be downloaded)
- Runs end to end in llama-cpp-python 0.3.36 with `response_format` JSON schema — UNVERIFIED (not executed; no weights downloaded)

## Alternate 1: Qwen3-4B-Instruct-2507

- Repo `Qwen/Qwen3-4B-Instruct-2507` at commit `cdbee75f17c01a7cc42f958dc650907174af0554` (lastModified 2025-09-17) — verified 2026-10-18 against https://huggingface.co/api/models/Qwen/Qwen3-4B-Instruct-2507
- License apache-2.0, LICENSE file https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507/blob/main/LICENSE (HTTP 200, "Apache License Version 2.0, January 2004") — verified 2026-10-18 against Qwen/Qwen3-4B-Instruct-2507@cdbee75f17
- 4,022,468,096 params. That is 0.6% over a strict 4.0B cap — verified 2026-10-18 against https://huggingface.co/api/models/Qwen/Qwen3-4B-Instruct-2507
- IFEval 83.4 (Qwen3-4B non-thinking 81.2) — verified 2026-10-18 against Qwen/Qwen3-4B-Instruct-2507@cdbee75f17 README.md
- Context 262144 — verified 2026-10-18 against Qwen/Qwen3-4B-Instruct-2507@cdbee75f17 config.json
- `Qwen/Qwen3-4B-Instruct-2507-GGUF` and `ggml-org/Qwen3-4B-Instruct-2507-GGUF` do not exist (API returns 401) — verified 2026-10-18 against https://huggingface.co/api/models/Qwen/Qwen3-4B-Instruct-2507-GGUF
- GGUF repo `unsloth/Qwen3-4B-Instruct-2507-GGUF` at commit `a06e946bb6b655725eafa393f4a9745d460374c9` — verified 2026-10-18 against https://huggingface.co/api/models/unsloth/Qwen3-4B-Instruct-2507-GGUF
- `Qwen3-4B-Instruct-2507-Q4_K_M.gguf`: 2,497,281,120 bytes, sha256 `3605803b982cb64aead44f6c1b2ae36e3acdb41d8e46c8a94c6533bc4c67e597` — verified 2026-10-18 against unsloth/Qwen3-4B-Instruct-2507-GGUF@a06e946bb6 tree LFS metadata
- Second source: `lmstudio-community/Qwen3-4B-Instruct-2507-GGUF@4edb920b6f14e3b9284d4502a6485103d72cde05`, `Qwen3-4B-Instruct-2507-Q4_K_M.gguf`, 2,497,280,448 bytes, sha256 `8cdb57cbb880d313736a9bc4e3d3d2485f145b5e19cf33783746e753e82641fc` — verified 2026-10-18 against its tree LFS metadata

## Alternate 2: Ministral 3 3B Instruct 2512

- Repo `mistralai/Ministral-3-3B-Instruct-2512` at commit `b35d4dfe56c142746f54dbd64f579faab2744308` (lastModified 2026-07-15) — verified 2026-10-18 against https://huggingface.co/api/models/mistralai/Ministral-3-3B-Instruct-2512
- License apache-2.0 (card metadata). There is no LICENSE file in either the model repo or the GGUF repo; the canonical text is https://www.apache.org/licenses/LICENSE-2.0 — verified 2026-10-18 against the tree listings
- 3,849,090,048 params total: a 3.4B language model plus a 0.4B vision encoder. The GGUF holds 3,429,006,336 params (text only) — verified 2026-10-18 against the model API, README.md, and the GGUF metadata API
- Card recommends temperature below 0.1 for production — verified 2026-10-18 against mistralai/Ministral-3-3B-Instruct-2512@b35d4dfe56 README.md
- Context 262144; GGUF arch `mistral3` — verified 2026-10-18 against https://huggingface.co/api/models/mistralai/Ministral-3-3B-Instruct-2512-GGUF?expand[]=gguf
- GGUF repo `mistralai/Ministral-3-3B-Instruct-2512-GGUF` at commit `eb599d408350ea2bb60452cb86be7c7b2fc28227` — verified 2026-10-18 against https://huggingface.co/api/models/mistralai/Ministral-3-3B-Instruct-2512-GGUF
- `Ministral-3-3B-Instruct-2512-Q4_K_M.gguf`: 2,147,023,008 bytes, sha256 `9ed150d4367e68df0ac8e1540f6ddc65b42d0ee26378329d1ecbca60f93fc5f8` — verified 2026-10-18 against mistralai/Ministral-3-3B-Instruct-2512-GGUF@eb599d4083 tree LFS metadata
- IFEval or JSON benchmark published for Ministral 3 3B — UNVERIFIED (none in the model card)

## Other candidates checked

- `ibm-granite/granite-4.2-3b@e459acceac81e5fe67c07d9cfc72329a332e7eb1`: Apache-2.0, 3,659,737,600 params, released 2026-08-25. It is a reasoning model whose thinking mode is the default; the template appends `<think>\n` unless `enable_thinking=False` — verified 2026-10-18 against its README.md. GGUF `ibm-granite/granite-4.2-3b-GGUF@c40945d71cd90f249a56985e8155551a9188dc30` `granite-4.2-3b-Q4_K_M.gguf` is 2,244,011,552 bytes, sha256 `e0406663965846ae22a403456eb826ccce5f450840491f71952f18a7cb78e7d5` — verified 2026-10-18 against its tree LFS metadata. Not picked: the default thinking prefix conflicts with a JSON-only grammar.
- `microsoft/Phi-4-mini-instruct@cfbefacb99257ffa30c83adab238a50856ac3083`: MIT (https://huggingface.co/microsoft/Phi-4-mini-instruct/resolve/main/LICENSE), 3,836,021,760 params, context 131072. `bartowski/microsoft_Phi-4-mini-instruct-GGUF@7ff82c2aaa4dde30121698a973765f39be5288c0` `microsoft_Phi-4-mini-instruct-Q4_K_M.gguf` is 2,491,874,688 bytes, sha256 `01999f17c39cc3074afae5e9c539bc82d45f2dd7faa3917c66cbef76fce8c0c2` — verified 2026-10-18 against the HF API and tree LFS metadata. Qualifies, but the GGUF is from February 2025.
- `HuggingFaceTB/SmolLM3-3B@a07cc9a04f16550a088caea529712d1d335b0ac1`: Apache-2.0, 3,075,098,624 params, context 65536, extended thinking on by default (`/no_think` turns it off). `ggml-org/SmolLM3-3B-GGUF@4965cb60b150737b68a0408c36aeefb65078f894` `SmolLM3-Q4_K_M.gguf` is 1,915,305,312 bytes, sha256 `8334b850b7bd46238c16b0c550df2138f0889bf433809008cc17a8b05761863e` — verified 2026-10-18 against the HF API, README.md and tree LFS metadata
- `Qwen/Qwen3.5-2B@15852e8c16360a2fea060d615a32b45270f8a8fc`: Apache-2.0, 2,274,069,824 params, pipeline `image-text-to-text`. `Qwen/Qwen3.5-4B` has 4,659,865,088 params (over the cap) — verified 2026-10-18 against the HF API. Not evaluated further.
- `google/gemma-4-E4B-it` has 7,996,156,490 params and `gemma-4-E2B-it` has 5,123,178,051, both over the cap. Card metadata says `license: apache-2.0` with `license_link` https://ai.google.dev/gemma/docs/gemma_4_license — verified 2026-10-18 against the HF API. Whether that page grants plain Apache-2.0 is UNVERIFIED (the page text did not resolve the question); moot, since both exceed 4B.
- LiquidAI LFM2.5 small models — license not checked; UNVERIFIED.

## llama-cpp-python

- Latest is 0.3.36, uploaded 2026-10-01; PyPI has only an sdist (no wheels) for 0.3.25 through 0.3.36 — verified 2026-10-18 against https://pypi.org/pypi/llama-cpp-python/json
- The README lists a C compiler as a requirement (Windows: Visual Studio or MinGW; macOS: Xcode) and says `pip install llama-cpp-python` builds llama.cpp from source — verified 2026-10-18 against abetlen/llama-cpp-python@v0.3.36 README.md
- Prebuilt CPU wheels for 0.3.36 are on `--extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu`: `win_amd64`, `manylinux2014_x86_64`, `manylinux2014_aarch64`, `musllinux_1_2_{x86_64,aarch64}`, `macosx_11_0_arm64`, `linux_riscv64`, all tagged `py3-none` (one wheel per platform covers any Python 3.8+) — verified 2026-10-18 against https://abetlen.github.io/llama-cpp-python/whl/cpu/llama-cpp-python/
- No wheel exists for macOS x86_64 (the last was 0.3.2) or Windows arm64; those platforms compile from source — verified 2026-10-18 against the same index
- 0.3.36 release asset digests: win_amd64 7,767,370 bytes `sha256:ae5e88a2cf464e5a2dde7c8898c2d5c71cc24d03cac6396bf7509456bde0b9fb`; manylinux x86_64 `sha256:c8a3e98093e950d7a770f794842e36f2db82b2933e8762ed7b5ffd435011e8e4`; manylinux aarch64 `sha256:410bdf3cf66478f55de0ad51dd6ab241424591bdd36aff086b000d155ac182c6`; macosx arm64 `sha256:1bec5e1d9fc7c4919aaece647bbd3e1a7f36ac8fd2714c8cda7e6991a544557b` — verified 2026-10-18 against GitHub release abetlen/llama-cpp-python v0.3.36 (tag commit 1652066e0a)
- Add `--only-binary=llama-cpp-python` so pip never falls back to the PyPI sdist and compiles — UNVERIFIED (standard pip flag; not tested against this index)
- v0.3.36 vendors llama.cpp commit `0c1e57098bba43ac29e6e3b677cdceebdd22334f` (2026-10-01), between llama.cpp v0.5.0 and v0.6.0 — verified 2026-10-18 against abetlen/llama-cpp-python@v0.3.36 vendor/ and the ggml-org/llama.cpp compare API
- `create_chat_completion(..., temperature=0.2 default, response_format=..., grammar=..., seed=...)` — verified 2026-10-18 against abetlen/llama-cpp-python@v0.3.36 llama_cpp/llama.py:2011-2030
- `response_format` type is `Literal["text","json_object"]` plus an optional `schema`; there is no `"json_schema"` type — verified 2026-10-18 against abetlen/llama-cpp-python@v0.3.36 llama_cpp/llama_types.py:176-180
- `{"type":"json_object","schema":S}` becomes `LlamaGrammar.from_json_schema(json.dumps(S))`. If schema conversion raises, it silently falls back to generic JSON (`fallback_to_json=True`), so validate the output against the schema afterwards anyway — verified 2026-10-18 against abetlen/llama-cpp-python@v0.3.36 llama_cpp/llama_chat_format.py:1005-1028
- Explicit alternative: `grammar=LlamaGrammar.from_json_schema(json.dumps(S))` passed to `create_chat_completion` — verified 2026-10-18 against the same files (signature at llama.py:2030; constructor used at llama_chat_format.py:1009)
- `temperature=0.0` selects the greedy sampler (`sampler.add_greedy()`); a negative value selects `add_dist(seed)` — verified 2026-10-18 against abetlen/llama-cpp-python@v0.3.36 llama_cpp/llama.py:761-764
- With no `chat_format`, the GGUF's `tokenizer.chat_template` is used via `Jinja2ChatFormatter`, which renders in `jinja2.sandbox.ImmutableSandboxedEnvironment` — verified 2026-10-18 against abetlen/llama-cpp-python@v0.3.36 llama.py:512-560 and llama_chat_format.py:27,221

## CVEs (2024-2026) and the minimum safe version

- CVE-2024-34359 (GHSA-56xg-wfcc-g829, critical): RCE through Jinja2 SSTI in the GGUF chat template, affecting llama-cpp-python 0.2.30 through 0.2.71, fixed in 0.2.72 — verified 2026-10-18 against the GitHub Advisory DB (`gh api advisories?ecosystem=pip&affects=llama-cpp-python`)
- GGUF-parser and model-load advisories in llama.cpp, with the patched build: CVE-2024-32878 b2740; CVE-2024-41130 b3427; CVE-2024-42477 b3561; CVE-2025-49847 b5662 (vocab); CVE-2025-52566 b5721 (tokenizer); GHSA-g4cc-763q-h9h6 c33fe8b8 (llama_model_load); CVE-2025-53630 26a48ad (gguf integer overflow); CVE-2026-33298 b7824 (`ggml_nbytes` overflow, heap overflow); CVE-2026-27940 b8146 (bypass of the 53630 fix, demonstrated to RCE) — verified 2026-10-18 against `gh api repos/ggml-org/llama.cpp/security-advisories` and NVD
- CVE-2026-52131: reachable assertion in `gguf_reader::read`, affects b5693 and earlier — verified 2026-10-18 against NVD keywordSearch=llama.cpp
- b7824 = 4e5b83b226 (2026-01-24); b8146 = 418dea39ce (2026-02-24) — verified 2026-10-18 against the ggml-org/llama.cpp commits API
- llama-cpp-python 0.3.16 (2025-08-15) vendors a llama.cpp older than b8146; 0.3.17 (2026-03-23) is the first release whose vendored commit (49bfddeca1) contains b8146 — verified 2026-10-18 against abetlen/llama-cpp-python vendor/ at each tag and the compare API
- **Minimum safe for GGUF parsing: llama-cpp-python 0.3.17. Pin 0.3.36**, the latest release and the first with wheels on every target platform except Intel Mac and Windows arm64 — derived from the lines above
- CVE-2026-43627 (`llama_batch_init` integer overflow, "b1283 through b9058"). Only reachable with attacker-chosen batch parameters, which a fixed-config judge does not have. Whether upstream has a fix is UNVERIFIED (NVD cites only third-party patches; tag b9059 does not exist) — verified 2026-10-18 against NVD
- CVE-2026-2069 (stack overflow in `llama_grammar_advance_stack`): fix PR #18993 is unmerged and issue #18988 is open. Only reachable with an attacker-controlled grammar; the judge's schema is ours, not the input file's — verified 2026-10-18 against ggml-org/llama.cpp issues/18988 and pulls/18993
- CVE-2026-17500/17501 (`common/json-schema-to-grammar.cpp`), CVE-2026-18581 (`common/jinja/parser.cpp`) and CVE-2026-107183 (llama-server chat-peg, fixed b11393 = dbe4c3ed42, 2026-10-04, newer than 0.3.36's vendored commit) are in llama.cpp's `common/` or server code. llama-cpp-python converts schemas in Python (`llama_grammar.py`) and renders templates in Python Jinja2. Whether the 0.3.36 wheel links any of that `common/` code is UNVERIFIED — verified 2026-10-18 against NVD and abetlen/llama-cpp-python@v0.3.36 source
- RPC and server CVEs (CVE-2024-42479, CVE-2026-34159, CVE-2026-21869, CVE-2026-43631/43632, CVE-2026-78147/78148, CVE-2026-86317) do not apply to in-process CPU use — verified 2026-10-18 against the advisory and NVD descriptions (each names the RPC backend or llama-server)

## Pure-wheel alternative: onnxruntime-genai

- onnxruntime-genai 0.18.0 (2026-10-14, MIT) ships wheels for cp311-cp314 on win_amd64, win_arm64, manylinux_2_28 x86_64 and aarch64, and macosx_12_0_arm64. There are no cp310 or macOS x86_64 wheels — verified 2026-10-18 against https://pypi.org/pypi/onnxruntime-genai/json
- The latest GitHub release/tag is v0.17.0, although PyPI has 0.18.0 — verified 2026-10-18 against `gh api repos/microsoft/onnxruntime-genai/releases`
- Constrained decoding goes through `params.set_guidance(guidance_type, guidance_data)` with type `"json_schema"` (or `"lark_grammar"`) — verified 2026-10-18 against microsoft/onnxruntime-genai@v0.17.0 examples/python/model-qa.py:92 and common.py:565-580
- No qualifying model at 3 GB or less: `microsoft/Phi-4-mini-instruct-onnx@fc04c8f93d` CPU int4 `model.onnx.data` is 4,856,573,952 bytes; `onnx-community/Qwen3-4B-Instruct-2507-ONNX` is a multi-shard fp32/fp16 transformers.js export (each shard about 2 GB); `onnx-community/granite-4.1-3b-ONNX` does not exist — verified 2026-10-18 against the HF tree API. A user would have to build an int4 ONNX themselves, so this route is not viable for a one-file pinned download.

## jiffy backend

- `jiffy scanner scan <path> --json` exits 0 pass/review, 2 block, 1 unverified; JSON has `findings[]` with severity, ruleId, ruleName, file, line, message — verified 2026-10-18 against Jiffy-Labs-AI/jiffy-cli@b724e01 README.md and src/commands/scanner.ts
- `jiffy scanner scan` hashes first and uploads files only when the hash is unknown to Jiffy — verified 2026-10-18 against Jiffy-Labs-AI/jiffy-cli@b724e01 README.md (Local mode)

## api judge tier

- Provider API endpoints and request shapes in unpick/judges/api.py — UNVERIFIED (not yet checked against each provider's current API reference)
