# UX references and running unpick inside an agent

Compiled 2026-10-22 for unpick 0.2.0, on branch `ux/jiffy-layout`. Audience: a developer or hobbyist
with no security background who wants one answer: is this safe to install, and if not, what do I do?

This note does two jobs. Part A names UX patterns worth copying from tools that already speak to
that person, and ranks the five changes still missing. Part B compares the ways to put unpick in
front of Claude Code, Codex, and Cursor, and recommends a default. Every claim about an agent's
behaviour was checked against that agent's docs on 2026-10-22. The URLs are in the Sources list.
The threat examples these patterns exist for are in `docs/research/2026-10-landscape.md` (compiled
2026-10-18). This note does not repeat that catalogue.

The hook is already the control (`unpick hook install claude-code|codex|cursor`). The watcher is
the backstop after a file has landed. This note does not propose a second hook.

## What this branch already shows

The local UI (`unpick ui`, `unpick/ui/static/app.js`) already does the parts below. The ranked list
does not ask for them again.

- A verdict block: STOP, REVIEW, or NOTHING FOUND, with the action line "This does not prove it is
  safe" (`VERDICT_ACTION` in `app.js`). A failed scan says FAILED and leaves the previous result
  labelled as previous.
- A serious result headlines "Do not install yet: N serious warning(s)".
- Each warning has "Why it matters", "When it is harmless", then a decision. The note under the
  buttons says a choice is saved for this exact line, and that if the line changes the warning
  comes back. The rule id is printed after the agreement text.
- "Move it to quarantine" is a confirm step. Restore is described as putting it back from
  "Something got in?".
- The Changes screen says a match against the saved copy is not a safety verdict, and a new
  version with no warnings is not the same as safe.

One mismatch with a decision already written down: DECISIONS.md item 46 and `docs/UI-NOTES.md` name
the neutral word "NO WARNINGS". This branch's screen says "NOTHING FOUND", and "YOUR CALL" when
every warning was marked a false alarm. The action line under the word is the one that keeps the
result from reading as a pass. The word itself is the UI worker's file.

Screens used below: Scan (`#start`, `#scan`, `#check`), Installed (`#inventory`), Test run
(`#rehearse`), Changes (`#verify`), Something got in? (`#recover`).

---

## Part A. UX references

Eight tools. For each: the one pattern worth copying, why it works for a layperson, and the unpick
command or screen it maps to.

### 1. Malwarebytes quarantine

**Pattern.** Take the item out of reach, keep it, and say how to put it back or delete it.
Quarantine is the action. Delete is a second, separate choice.

**Why it works.** The person does not have to decide "is this malware?" before the dangerous thing
stops being loaded. The undo is named in the same place as the action, so quarantine does not feel
like a shredder.

**Where.** When the add-on is already on disk: the Scan aside "What to do next", and
`unpick quarantine` / `unpick restore`. The button exists. It is not yet the first verb on that
screen. Source: https://help.malwarebytes.com/hc/en-us/articles/31589479169179-Manage-quarantined-items-in-Windows-and-Mac
(page dated 2026-06-30).

### 2. VirusTotal

**Pattern.** Each engine contributes a named label and a detail, and a count of zero is not a
verdict. VirusTotal's own guidance to vendors: a low detection count does not automatically mean
bad, and zero detections does not always mean good.

**Why it works.** A ratio looks like a score. A layperson treats 0/70 as "safe" and 5/70 as
"infected". Naming the behaviour ("this file drops a program") gives them something to act on. The
zero case needs a sentence that the absence is about these engines, not about the file.

**Where.** The verdict action line already says "This does not prove it is safe". Keep that, on the
neutral word as well as on Changes. Do not add a detection ratio, and do not turn zero warnings
green. Sources: https://docs.virustotal.com/docs/false-positive-contacts and
https://docs.virustotal.com/docs/how-it-works and https://docs.virustotal.com/docs/results-reports.

### 3. Socket

**Pattern.** The alert is named by what the package would do, and the page says the one next step
for that kind of alert: known malware means remove it; an install script or native code means look
at that script; a look-alike name means confirm the publisher. The link goes to the exact script.

**Why it works.** "High severity" is not an action. "This runs a program during install; open that
script, or remove the package" is an action. The person never has to translate a rule id first.

**Where.** The warning card on `#scan`. Today the summary line is the checker's own message, and
the first question is "What do you make of it?" (false alarm, real problem, or ask the author).
Lead the summary with what the add-on would do and one install verb (leave it, move it to
quarantine, or read this line and then decide). Keep the judgment buttons after that, where
DECISIONS.md item 47 already puts them. Sources: https://docs.socket.dev/docs/what-to-do-with-socket-alerts
and https://docs.socket.dev/docs/alert-types and https://docs.socket.dev/docs/socket-for-github.

### 4. 1Password Watchtower

**Pattern.** A category appears only when there is something to fix. Each category has one action,
"show items". Empty categories are absent, so a quiet page is an empty list, not a green score.
The check runs locally.

**Why it works.** A dashboard of healthy rows teaches the person that silence means "all clear".
Hiding the empty rows removes that reading. One action per row removes a menu.

**Where.** Installed (`#inventory`, `unpick inventory`). Today it lists every add-on and the count
of what the filters show. Show only add-ons that need a look, with one action each (review the
warnings, or move that one to quarantine). Keep the full list one step away for someone who wants
it. Say on the empty page that these checks did not flag the installed set, and that this is not
proof it is safe. Sources: https://support.1password.com/watchtower/ and
https://1password.com/watchtower/ and https://support.1password.com/watchtower-privacy/.

### 5. Have I Been Pwned

**Pattern.** One sentence, then the cards. On Pwned Passwords the indexed case says to change the
password immediately. The not-indexed case says, in the same view, that "not indexed here" is not
the same as "this is a good password". Breach pages name what happened, which data was involved,
and what to do.

**Why it works.** The structure is right: one sentence, then evidence, then an action. The
not-indexed headline is the trap. "Good news" is what a layperson remembers, and the caveat under
it loses.

**Where.** Copy the structure onto `#scan`: one sentence (the verdict), then the warning cards,
then the aside. Do not copy a good-news headline onto a scan that found nothing. The action line
"This does not prove it is safe" is the caveat, and it has to be the sentence the person reads,
not a footnote. Source: https://haveibeenpwned.com/Passwords (wording checked 2026-10-22) and
https://haveibeenpwned.com/.

### 6. Chrome Safe Browsing

**Pattern.** A full-page "Dangerous site" interrupt. Continuing is not a button next to Back. The
person opens Details, then chooses "Visit this unsafe site". The proceed path names the risk in
the control itself.

**Why it works.** Two equal buttons ("back" and "continue") get mis-clicked. Burying the proceed
path, and labelling it with the risk, makes the safe action the obvious one.

**Where.** The hook's block message, and the CLI summary of a scan that found something at high.
Today `unpick/hook.py` `_summary` joins `severity`, rule id, path, line, and the first 80
characters of the message. That is a log line. The block should be one verb ("Do not install it"),
the plain title of the finding, and a second line for how to review (`unpick check <ref>`).
Proceeding stays possible, because the person can uninstall the hook or accept the finding, and
that path should say what they are accepting. Primary sources:
https://support.google.com/chrome/answer/99020 and https://support.google.com/chrome/answer/9890866.
A secondary write-up of a two-tier "suspicious" versus "dangerous" warning (2026-10-21,
https://www.chromegeek.com/chrome-enhanced-protection-suspicious-site-warnings-clickfix/) is not
the pattern to copy; the support pages are.

### 7. npm audit and GitHub Dependabot

**Pattern.** npm prints the impact and a remediation, and exits 0 only when it found nothing.
Applying a fix is a separate command from printing the report. Dependabot opens one alert per
problem, with severity, the affected file, the vulnerability, and a fixed version when one exists.
The docs say the alerts cannot catch every security issue. Dismissing an alert asks for a reason.

**Why it works.** The report and the change to the machine are different steps, so "I ran audit"
is not "I fixed it". One alert per problem matches how a person decides. A dismiss without a
reason becomes invisible later.

**Where.** `unpick check` already fetches and scans without running the install, and
`unpick check --approve` prints an install command and does not run it. Keep that split. Do not
add a "fix all" that rewrites the add-on or the config. `unpick decide accept|reject|ask-author`
is the dismiss-with-a-reason: the note is the reason, and it is stored next to the line. Dependabot's
"cannot catch every issue" is the same sentence as "This does not prove it is safe". Sources:
https://docs.npmjs.com/cli/v11/commands/npm-audit (CLI 11.21.1, page edited 2026-03-18) and
https://docs.github.com/en/code-security/concepts/supply-chain-security/about-dependabot-alerts.

### 8. Little Snitch

**Pattern.** A connection alert names the program and the remote host, then Allow or Deny, and the
choice has a lifetime: once, until the program quits, or until you change it.

**Why it works.** The person can answer "this program, that host" without knowing what a socket is.
The lifetime stops a one-time allow from becoming a permanent allow by accident.

**Where.** Test run (`#rehearse`, `unpick rehearse`) should lead with that sentence: it tried to
contact this host, or it opened this path. Today the timeline prints the tool name and a slice of
the tool's JSON. The hook block is the Allow/Deny moment, and a recorded decision already has a
lifetime (until that line changes). Say the lifetime in the hook message too, in those words, so
the person sees it at the moment they accept.

Source: https://help.obdev.at/littlesnitch6/alert-overview.

### What not to copy

- A green zero, or a detection ratio (VirusTotal's browser extension treats zero as green; the
  product docs say not to). unpick's neutral verdict stays off green.
- Have I Been Pwned's "Good news" headline on the not-indexed password. The caveat is the part to
  keep. The headline is the part to leave.
- `npm audit fix` as a model. unpick must not grow a command that "fixes" an add-on by rewriting it.

### Ranked changes

These five are the gaps. They are ordered by when the person meets them: the block first, then the
warning, then the list of what is already installed, then an update, then the case where the file
is already on disk.

1. **Say the block in one verb.** `unpick hook run` and the CLI scan summary still lead with
   `severity`, rule id, path, and line (`_summary` in `unpick/hook.py`). Lead with "Do not install
   it" and the finding's plain title. Put the rule id and the review command on the next line.
   This is the Little Snitch alert plus the Safe Browsing interrupt. Files: `unpick/hook.py` and
   the CLI render. This note does not edit them.
2. **One next step on each warning.** On `#scan`, lead the card with what the add-on would do and
   one verb (leave it, move it to quarantine, or read the line and then decide). Keep "Why it
   matters", the judgment buttons, and the rule id after that. This is the Socket alert.
3. **Installed shows only what needs a look.** On `#inventory` / `unpick inventory`, hide empty
   groups, one action per row, and a sentence that an empty list is not a clean bill of health.
   This is Watchtower.
4. **Changes leads with a sentence.** On `#verify` / `unpick verify` / `unpick outdated`, say what
   the update added before the file diff and the commit ids. A hash match stays labelled as not a
   safety verdict, which the screen already does.
5. **Quarantine is the first verb when it is already installed, and the test run leads with
   behaviour.** On the Scan aside, "Move it to quarantine" comes before the judgment, with restore
   named in the same sentence (Malwarebytes). On `#rehearse`, the first line is "it tried to
   contact X" or "it opened Y", and the JSON timeline is the evidence under that (Little Snitch).

---

## Part B. How an agent can run unpick

Five mechanisms, three agents. "Block" means the agent does not get to run the install unless the
check allows it. "Advise" means the model is told to check, and can ignore that.

Checked 2026-10-22:

- Claude Code skills, memory, hooks, plugins: https://code.claude.com/docs/en/skills ,
  https://code.claude.com/docs/en/memory , https://code.claude.com/docs/en/hooks ,
  https://code.claude.com/docs/en/plugins-reference
- Codex hooks (the developers.openai.com hooks URL redirects here): https://learn.chatgpt.com/docs/hooks.md
- Codex skills, AGENTS.md, plugins: https://developers.openai.com/codex/skills ,
  https://developers.openai.com/codex/guides/agents-md , https://developers.openai.com/codex/plugins
- Cursor hooks, skills, rules, plugins, MCP: https://cursor.com/docs/hooks ,
  https://cursor.com/docs/skills , https://cursor.com/docs/context/rules ,
  https://cursor.com/docs/plugins , https://cursor.com/docs/context/mcp

The install-hook behaviour below is what `unpick/hook.py` does in this tree, not a proposal.

### Comparison

| Mechanism | Claude Code | Codex | Cursor | Blocks an install? | Setup for a novice | What breaks |
|---|---|---|---|---|---|---|
| Hook, before the tool runs | PreToolUse in `~/.claude/settings.json`. Exit 2 blocks; stderr is the reason. Any other exit, a timeout, or exit 0 with no output does not block. | PreToolUse in `~/.codex/hooks.json`. Exit 2 blocks, or JSON `permissionDecision: deny`. The hook must be trusted with `/hooks`. Trust is bound to the command text. | `beforeShellExecution` in `~/.cursor/hooks.json`. Exit 0 plus `{"permission":"deny"}` blocks. Exit 2 blocks. Other failures allow the command unless `failClosed` is set. | Yes. This is the only mechanism here that can stop the install when the model wants to proceed. | One command: `unpick hook install <agent>`. Codex adds a trust prompt. | Listed under "Holes in the hook" below. |
| Skill (`SKILL.md`) | Personal `~/.claude/skills/<name>/SKILL.md`, or `.claude/skills/` in the project. The description is how the model decides to load it. The body loads when the skill is used. `/unpick` invokes it by name. | Official user folder `$HOME/.agents/skills`, repo folder `.agents/skills`. Admin folder `/etc/codex/skills`. Metadata is loaded first; the body is loaded when the skill is chosen. | Project `.agents/skills/` and `.cursor/skills/`, user `~/.cursor/skills/`, plus the compatibility folders `.claude/skills/`, `.codex/skills/`, `~/.claude/skills/`, `~/.codex/skills/`. | No. Instructions. The model can skip them, and a session that never loads the skill never sees them. | Copy one folder. No account, no server. | Claude cloud and Cowork sessions do not read `~/.claude/skills/` on the machine. A second copy in another folder can load two skills with the same name. |
| Rules file (`AGENTS.md`, `CLAUDE.md`) | Context, not configuration. The docs say: to block an action no matter what Claude decides, use a PreToolUse hook. From v2.1.277, `./AGENTS.md` is read only when no `CLAUDE.md` or `CLAUDE.local.md` exists in the working directory or above. If both exist, only `CLAUDE.md` is read, unless it imports the other with a line `@AGENTS.md`. | Global `~/.codex/AGENTS.md` (or `AGENTS.override.md`) and a project walk from the root. The docs say to pair it with a linter or a pre-commit hook when something must be enforced. | `AGENTS.md` is an alternative to `.cursor/rules`. Plain instructions. | No. Advise only. Always in the prompt when that file is the one the agent selected. | Paste a short block once. | Claude ignores a repo `AGENTS.md` when `CLAUDE.md` exists and does not import it. The model can still do the opposite of the block. |
| MCP server | A tool the model may call. It does not run before other tools. | Same. An MCP-tool hook can block when that tool's hook returns a blocking decision. A missing server, or an error in the hook, does not block the other tool. The server has to be connected already. | Tools, prompts, and resources in an MCP config. The model chooses whether to call them. `beforeMCPExecution` is a separate hook from `beforeShellExecution`. | No, not by itself. A tool the model may call cannot stop a different tool. | Highest of the five: the person installs a server, which is the kind of install unpick exists to check. | The model never calls it. On Codex, the server being down does not fail the other call closed. |
| Plugin or package | A plugin can ship `hooks/hooks.json` (including PreToolUse) and skills. Installing the plugin is itself a trust decision. `claude plugin install` run as a shell command is a tool call. | A plugin can bundle skills, MCP, and `hooks/hooks.json`. Plugin hooks are not trusted automatically; `/hooks` still applies. Install is `/plugins`. | Cursor's own plugin format can bundle rules, agents, commands, and hooks. The Agent Plugins format bundles skills and MCP only. A marketplace install is a trust decision. | Only if the plugin's hook is the hook, and only on the events that hook subscribes to. Packaging does not add a new enforcement point. | A marketplace click, which is the decision the hook is meant to gate. The person who does not yet have the hook is asked to install a plugin in order to get the hook. | User-typed `/plugin` in Claude Code is a session command, not a tool call, so PreToolUse does not see it (recorded in `docs/verified/phase3.md`, 2026-10-18; not re-run live on 2026-10-22). |

### Holes in the hook

The hook fails closed on an install it cannot check. `UNPICK_HOOK_FAIL_OPEN=1` allows those
unverifiable installs only. A block is never overridden by that switch. It sees install commands
only when they parse as real shell commands (a heredoc that mentions an install is not one;
DECISIONS.md item 29). Edits are checked only when the file name is in `CONFIG_NAMES` in
`unpick/hook.py` (MCP configs, settings files, hooks files, OpenCode config).

Claude Code:

- Exit 2 is the block. Another non-zero exit, or a timeout, does not block.
- `--bare` skips settings and plugin hooks.
- A plugin install the person types as a session command is not a tool call. The same install as a
  shell command (`claude plugin install ...`) is a Bash tool call, and the hook sees it.
- Without managed settings, a process that can approve its own tool call can approve one a
  PreToolUse hook blocked. The mods documentation says this. The hook is not a guarantee against
  a hostile session that already has permission to edit settings.

Codex, from https://learn.chatgpt.com/docs/hooks.md on 2026-10-22:

- Hooks are on by default. A config switch can turn them off.
- A hook that has not been trusted in `/hooks` is skipped. Project hooks under `.codex/` load only
  when that project layer is trusted. Trust is bound to a hash of the hook, so editing the command
  (`unpick hook run codex`) asks for trust again. A flag exists that skips the trust prompt; using
  it removes the review.
- `permissionDecision: "ask"`, a legacy `decision: "approve"`, `continue: false`, `stopReason`, and
  `suppressOutput` are parsed and not supported yet. Codex marks that hook run as failed, reports
  the error, and continues the tool call. "Ask" does not stop the command.
- Several matching hooks run at the same time, so one hook cannot stop another from starting.
- PreToolUse covers shell (including unified exec), `apply_patch` (match `apply_patch`, `Edit`, or
  `Write`), MCP tools, and other local function tools. Hosted tools such as web search are not
  covered. A later write to the same shell session does not run PreToolUse again. The docs call
  hooks "a useful guardrail, not a complete enforcement boundary", and some tool paths can opt out.
- A hosted or cloud session that does not run local commands does not run this hook.
- unpick's matcher is `Bash|PowerShell|Edit|Write|MultiEdit`. `Edit|Write` matches the `apply_patch`
  aliases. PowerShell may not be a tool name Codex emits.

Cursor, from https://cursor.com/docs/hooks on 2026-10-22:

- unpick subscribes to `beforeShellExecution` only. It does not subscribe to `beforeMCPExecution`,
  so an MCP tool call that is not a shell command is not blocked.
- The installed entry does not set `failClosed`. Invalid JSON on a permission hook blocks even
  then. A crash, a timeout, or an exit code other than 0 or 2 allows the command. The docs
  recommend `failClosed: true` for a security-critical hook. Setting it is a change to
  `unpick/hook.py`, which this note does not make. Any deny wins over ask, and ask wins over
  allow, when several hooks answer.
- User hooks in `~/.cursor/hooks.json` do not run in cloud agents. Project hooks in
  `.cursor/hooks.json` do, except during a read-only exploratory turn. unpick's installer writes
  the user file.
- Third-party Claude hooks are mapped onto Cursor's `preToolUse` only when "Third-party skills"
  is enabled. unpick writes Cursor's own format instead, so it does not depend on that switch.
- Priority is Enterprise, then Team, then Project, then User. A higher layer can ship a different
  answer. Deny still wins over allow when both run.

### Layered default

Use all three of the first layers. Do not start with an MCP server or a plugin.

1. **Enforcement: the existing hook.** `unpick hook install claude-code`, `codex`, or `cursor`.
   `--dry-run` first. This is the only layer that can block. After the Codex install, trust it in
   `/hooks`. The holes above stay holes until someone changes `unpick/hook.py` on purpose.
2. **Explain: the skill.** `integrations/claude-code/skills/unpick/SKILL.md`. It tells the agent
   to run `unpick check` before an install and to say the result in plain words, including that a
   result with no warnings is not proof the add-on is safe. Copy it once (see the README). The
   skill does not register its own hook. One hook definition, the installer, is enough to review.
3. **Remind: the rules snippet.** `integrations/AGENTS.md.snippet`, appended once to `AGENTS.md`.
   Advise only. It is in the prompt whenever that file is the one the agent loaded. Claude Code
   needs the `@AGENTS.md` import when `CLAUDE.md` already exists.
4. **Not an MCP server.** A tool the model may call cannot stop the model's other tools. Installing
   a server in order to vet servers is the risk the hook is there to gate. Codex can attach a hook
   to an MCP tool, and that hook blocks only when the server is already connected and the hook is
   trusted; a missing server or a hook error does not block the other call. Design note, if a
   server is ever built: one local stdio server, one tool named `check`, which runs `unpick check`
   on the reference it is given and returns the plain-language summary and the exit code. No
   network of its own. No other tools. It still would not be the control. This repo does not ship
   that server.
5. **Not a plugin as the first install.** A marketplace plugin is itself the trust decision. Claude
   plugins and Codex plugins can ship a PreToolUse hook, and a Cursor plugin in Cursor's own format
   can ship hooks, but the person is asked to install that package before any of it runs. Codex
   plugin hooks still need `/hooks` trust. The Agent Plugins format (skills plus MCP only) cannot
   ship the Cursor hook. Ship the skill and the snippet as files the person copies. Do not publish
   a plugin for this.

The watcher (`unpick watch`) stays the backstop for an add-on that landed outside the hook. It is
not one of the layers above, and it does not block the install that already happened.

### What the skill and the snippet must say

`unpick check` exits 0 when nothing is left open and it has no question, 1 when a finding is still
open or it has a question, and 2 when it refuses the reference or cannot run the check (`unpick/cli.py`
`cmd_check`). The hook blocks unaccepted findings at or above `--min-severity`, default high, which
is a narrower gate than exit 1. The skill follows the narrower instruction for the model: exit 1
or exit 2 means do not install; exit 0 means say that these checks did not flag it, and wait for
the person to say yes. An unverifiable install is a stop, matching the hook's fail-closed default.

The snippet is written so that, once pasted into `AGENTS.md` or `CLAUDE.md`, it does not itself
match the rules-file check: no URL, and no instruction to turn checks off. The copy in the repo is
named `AGENTS.md.snippet` so the repo's own scan does not treat it as a live rules file.

---

## Sources

Agent docs, fetched 2026-10-22:

- https://code.claude.com/docs/en/skills
- https://code.claude.com/docs/en/memory
- https://code.claude.com/docs/en/hooks
- https://code.claude.com/docs/en/plugins-reference
- https://learn.chatgpt.com/docs/hooks.md
- https://developers.openai.com/codex/skills
- https://developers.openai.com/codex/guides/agents-md
- https://developers.openai.com/codex/plugins
- https://cursor.com/docs/hooks
- https://cursor.com/docs/skills
- https://cursor.com/docs/context/rules
- https://cursor.com/docs/plugins
- https://cursor.com/docs/context/mcp

UX references:

- https://help.malwarebytes.com/hc/en-us/articles/31589479169179-Manage-quarantined-items-in-Windows-and-Mac
- https://docs.virustotal.com/docs/false-positive-contacts
- https://docs.virustotal.com/docs/how-it-works
- https://docs.virustotal.com/docs/results-reports
- https://docs.socket.dev/docs/what-to-do-with-socket-alerts
- https://docs.socket.dev/docs/alert-types
- https://docs.socket.dev/docs/socket-for-github
- https://support.1password.com/watchtower/
- https://1password.com/watchtower/
- https://support.1password.com/watchtower-privacy/
- https://haveibeenpwned.com/Passwords
- https://haveibeenpwned.com/
- https://support.google.com/chrome/answer/99020
- https://support.google.com/chrome/answer/9890866
- https://www.chromegeek.com/chrome-enhanced-protection-suspicious-site-warnings-clickfix/
- https://docs.npmjs.com/cli/v11/commands/npm-audit
- https://docs.github.com/en/code-security/concepts/supply-chain-security/about-dependabot-alerts
- https://help.obdev.at/littlesnitch6/alert-overview

In-repo:

- `unpick/hook.py` (the installer and `_summary`)
- `unpick/ui/static/app.js` (verdict, warning card, inventory, test run, changes)
- `docs/verified/phase3.md` (session command versus shell command, verified 2026-10-18)
- `docs/research/2026-10-landscape.md`
- DECISIONS.md items 26, 29, and 46
