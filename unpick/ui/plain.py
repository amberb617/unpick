"""Plain-language copy for the web UI: what each finding means and what to do, for someone with no security background.

One dict, so it can be swapped for a shared module (unpick/explain.py) without touching the page. Every entry is
title (the card heading), short (the verdict's reason, one sentence), means and todo. Rules without an entry,
including other scanners and AI reviewers, fall back by severity, so nothing renders without an explanation.
"""

from __future__ import annotations

RULES: dict[str, dict[str, str]] = {
    "RT-PREREQ": {
        "title": "Asks you to paste a command into your terminal",
        "short": "It asks you to paste and run a command yourself during setup.",
        "means": "The setup text tells you to copy a command into Terminal. Harmful add-ons use this trick so the "
                 "dangerous part never appears in the add-on itself: you run it for them.",
        "todo": "Don't run the command. If you need the tool it mentions, install it from its official website or "
                "package manager instead."},
    "RT-ENCODED-EXEC": {
        "title": "Runs a command you cannot read",
        "short": "It downloads or unscrambles a command and runs it straight away, so you never see what runs.",
        "means": "The command that actually runs is not the one written here. It is scrambled (encoded) or fetched from "
                 "the internet at the moment it runs.",
        "todo": "Don't install it, and don't run the command. An honest add-on can show you the exact command instead."},
    "RT-UNICODE": {
        "title": "Contains invisible text",
        "short": "It contains invisible text that your AI reads but you cannot see.",
        "means": "Some characters on this line do not show on screen, but your AI still reads them. That is a way to "
                 "hide instructions in plain sight. What unpick decoded is shown under \"What unpick saw\".",
        "todo": "Read the hidden text. If it asks your AI to do anything you did not expect, don't install it. Emoji and "
                "right-to-left languages sometimes use these characters harmlessly."},
    "RT-RENDER-DIVERGE": {
        "title": "Hides text from the page you read",
        "short": "It hides text from the page you read, but your AI still sees it.",
        "means": "A normal preview of this file, on GitHub or in a Markdown viewer, would not show this line the way "
                 "your AI reads it.",
        "todo": "Compare both columns under \"Read it raw\". If the hidden part gives your AI instructions, don't install it."},
    "RT-SECRECY": {
        "title": "Tries to keep something from you",
        "short": "It tells your AI to keep something from you or to ignore its usual rules.",
        "means": "Asking your AI to hide something from you, or to drop the rules it normally follows, only makes sense "
                 "if the add-on wants your AI to act behind your back.",
        "todo": "Don't install it, unless the text is clearly an example: security training material quotes these phrases."},
    "RT-SENSITIVE-PATH": {
        "title": "Points at passwords, keys or private files",
        "short": "It points your AI at files that hold passwords, keys or other private data.",
        "means": "This line names a place where secrets live, such as your SSH keys or a file of API keys. An AI following this "
                 "add-on could read them or send them somewhere.",
        "todo": "Ask why it needs that file. If the add-on's job has nothing to do with keys or secrets, don't install it."},
    "RT-PASTE-HOST": {
        "title": "Uses a throwaway website",
        "short": "It uses a throwaway website whose content can change after you check it.",
        "means": "Paste sites, anonymous file hosts and bare IP addresses can change what they serve at any time, and "
                 "anything sent there can be read by a stranger.",
        "todo": "Don't install it if it downloads from or sends data to that address. A link in a tutorial is usually fine."},
    "RT-LOOKALIKE": {
        "title": "Name imitates a well-known brand",
        "short": "Its name imitates a well-known brand, a common way to get the wrong thing installed.",
        "means": "The name is a near-miss of a known company's, or borrows it. Fake packages do this so people install "
                 "them by mistake.",
        "todo": "Check who published it. If it is not the company it names, and you did not mean to pick a community "
                "project, don't install it."},
    "RT-MCP-LAUNCH": {
        "title": "Starts a tool server in a risky way",
        "short": "It starts a tool server for your AI in a way that lets what runs change without you knowing.",
        "means": "An MCP server (a small program that gives your AI extra tools) is set to run whatever the latest "
                 "version is, over plain unencrypted web, or from a hidden program. What runs tomorrow may not be what "
                 "you checked today.",
        "todo": "Pin it to a version you have checked, for example name@1.2.3, or don't add it."},
    "RT-TOOL-DESC": {
        "title": "A tool's description gives your AI orders",
        "short": "One of its tools carries orders for your AI in its description.",
        "means": "Your AI reads every tool's description as instructions. This one is far longer than its job needs, or "
                 "talks about files, the internet, other tools or you.",
        "todo": "Read the description under \"Read it raw\". If it says anything beyond what the tool does, don't install it."},
    "RT-RULES-FILE": {
        "title": "A rules file pulls in outside instructions",
        "short": "Its rules file, which your AI loads in every session, pulls in outside content or weakens safety.",
        "means": "A rules file (instructions your AI reads at the start of every session) applies to everything you "
                 "do. This line loads content from elsewhere, or tells your AI to skip its safety checks.",
        "todo": "Remove the line, or don't add the file, unless the link and commands are your own team's."},
    "RT-AUTORUN": {
        "title": "Runs a command as soon as you open it",
        "short": "It runs a command by itself when you open the folder or start a session, before you have read anything.",
        "means": "A hook (a command your editor or AI runs automatically when something happens) is set to fire when "
                 "the folder opens or a session starts.",
        "todo": "Don't open this folder with your AI until you have read the command. If you don't recognise it, delete "
                "the setting."},
    "RT-GIT-AUTORUN": {
        "title": "Git settings that run programs",
        "short": "Its Git settings run a program by themselves whenever the folder is used.",
        "means": "Git will run this program without asking, every time your editor or AI touches the project.",
        "todo": "Don't open it with your AI. Delete the setting unless you added it yourself."},
    "RT-AGENT-SETTINGS": {
        "title": "Turns off approvals or reroutes your AI",
        "short": "It turns off your AI's \"are you sure?\" prompts, or sends its traffic and your API key somewhere else.",
        "means": "With approvals off, your AI acts without asking you. With traffic rerouted, a server you do not know "
                 "sees your code and your key.",
        "todo": "Don't use this folder's settings. Those choices belong in your own settings, not in something you downloaded."},
    "RT-CI-AGENT": {
        "title": "Lets strangers give orders to an AI in your project",
        "short": "It lets anyone who opens an issue or comment give orders to an AI that holds your project's keys.",
        "means": "This automated workflow (CI, which runs on GitHub's servers) starts an AI on events strangers can "
                 "create, so their text becomes the AI's instructions.",
        "todo": "Limit it to maintainers, and give the AI read-only access and no secrets."},
    "RT-INSTALL-REDIRECT": {
        "title": "Steers you away from the official download",
        "short": "It steers you away from the official download to another source.",
        "means": "Look-alike sources and attacker-run copies rely on being picked instead of the official one.",
        "todo": "Install from the official registry or the project's own site instead."},
    "RT-UNREAD": {
        "title": "A file unpick could not read",
        "short": "It contains files unpick could not read, so they were not checked.",
        "means": "Bundled, compiled or WebAssembly files cannot be read as text. They may be fine, but nothing checked them.",
        "todo": "Treat them as unchecked. Test-run it in a sealed box, or install it only if you trust who made it."},
    "RT-JUDGE-FAILED": {
        "title": "The AI reviewer could not finish",
        "short": "The optional AI reviewer could not finish.",
        "means": "The AI second opinion failed on this file. The built-in checks still ran.",
        "todo": "Nothing to do about the add-on. Try again, or turn the AI reviewer off under Advanced on the start page."},
}

_SERIOUS = {
    "title": "Something that could harm you",
    "short": "A check flagged something it treats as dangerous.",
    "means": "{who} flagged this line as dangerous. \"What unpick saw\" and the technical details say what it found.",
    "todo": "Don't install it until you understand this line. Read it under \"Read it raw\"."}
_OTHER = {
    "title": "Something worth a look",
    "short": "A check flagged something worth reading before you install it.",
    "means": "{who} flagged this line. \"What unpick saw\" and the technical details say what it found.",
    "todo": "Read the line under \"Read it raw\". If it asks your AI to do something you did not expect, don't install it."}


def explain(finding: dict) -> dict[str, str]:
    """Plain-language copy for one finding dict (Finding.to_dict())."""
    if finding["rule_id"] in RULES:
        return dict(RULES[finding["rule_id"]])
    source = finding.get("source", "")
    who = "An AI reviewer (a second opinion, never the verdict)" if source.startswith("judge") else "Another scanner"
    base = _SERIOUS if finding.get("severity") == "high" else _OTHER
    return {k: v.format(who=who) for k, v in base.items()}


def annotate(result: dict) -> dict:
    """Adds finding["plain"] to every finding in a scan result, in place, and returns it."""
    for f in result.get("findings", []) + result.get("accepted", []):
        f["plain"] = explain(f)
    return result
