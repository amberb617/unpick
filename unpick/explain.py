"""Shared plain-language explanations for terminal output and UI consumers.

Built-in rules have exact entries. External scanners own an open-ended rule vocabulary,
so each adapter has a category entry that preserves its original rule and evidence below it.
Unknown built-in IDs raise KeyError: adding a detector requires adding an explanation.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Explanation:
    title: str
    what_it_means: str
    what_to_do: str


EXPLANATIONS = {
    "RT-AGENT-SETTINGS": Explanation(
        "Your agent's protections may be disabled",
        "These settings remove approval prompts or send your agent's traffic to a different service. "
        "That traffic can include your code and access keys.",
        "Ask the author to explain the flagged settings before opening this project in your agent."),
    "RT-AUTORUN": Explanation(
        "Code runs when you open this",
        "Opening the folder or starting your agent can run a command before you have reviewed it.",
        "Read the flagged command and its script before opening the folder in your editor."),
    "RT-CI-AGENT": Explanation(
        "Strangers may direct your automated agent",
        "An automated project task lets outside comments or issues reach an AI agent. "
        "That agent may have access to your project's files and access keys.",
        "Ask the maintainer to restrict who can start this automated task."),
    "RT-ENCODED-EXEC": Explanation(
        "Runs code you cannot read first",
        "This command unpacks or downloads code and immediately runs it. "
        "The visible command does not show everything that will run.",
        "Ask the author for the complete readable script before running the command."),
    "RT-PREREQ": Explanation(
        "Setup asks you to run extra code",
        "The setup instructions ask you to run or download another program. "
        "That program could act on your computer with your permissions.",
        "Ask the author for the complete setup script before following this step."),
    "RT-GIT-AUTORUN": Explanation(
        "Git may run an unexpected program",
        "This folder's Git settings can start a program when an editor or agent uses the repository.",
        "Read the program named in the flagged Git setting before using this repository."),
    "RT-UNICODE": Explanation(
        "Hidden characters can conceal instructions",
        "The file contains characters you may not see on screen but your AI can read. "
        "They can hide instructions or change how text appears.",
        "Run `unpick raw <file>` on the flagged file to reveal the hidden characters."),
    "RT-INSTALL-REDIRECT": Explanation(
        "Installation points to a different source",
        "The instructions send you somewhere other than the usual source for this software. "
        "You may receive a different copy than you expected.",
        "Compare the flagged download address with the publisher's official installation instructions."),
    "RT-LOOKALIKE": Explanation(
        "This name resembles a trusted product",
        "The name looks like a known product or publisher. "
        "It may be an unrelated project using a similar name.",
        "Check that the publisher's official website links to this exact project."),
    "RT-MCP-LAUNCH": Explanation(
        "Your agent may start unreviewed software",
        "This tool connection can start changing or unexpected software, or use an unprotected connection.",
        "Ask the author to replace the flagged launch setting with a fixed version from a verified source."),
    "RT-PASTE-HOST": Explanation(
        "An outside address needs checking",
        "The file names a temporary, anonymous or unfamiliar address. "
        "Content there can change, and data sent there may reach someone else.",
        "Ask the author who controls the flagged address and what data goes there."),
    "RT-RENDER-DIVERGE": Explanation(
        "The preview hides part of the file",
        "Your AI reads text that a formatted preview may hide or display differently.",
        "Run `unpick raw <file>` on the flagged file to compare the preview with its full text."),
    "RT-RULES-FILE": Explanation(
        "Project instructions may change your agent's behavior",
        "These instructions load automatically and bring in outside content or weaken your agent's protections.",
        "Read the flagged instruction and its linked content before allowing your agent to use it."),
    "RT-SECRECY": Explanation(
        "Wording about hiding or overriding",
        "The text talks about keeping something out of sight or about replacing an AI's earlier rules. "
        "Aimed at an AI, that can hide actions from you; in code and docs it can also describe ordinary behaviour.",
        "Read the flagged passage in context to check whether it is an instruction or an example."),
    "RT-SENSITIVE-PATH": Explanation(
        "Private files or keys are mentioned",
        "The text names a place that can hold passwords, access keys or private data. "
        "A warning about protecting those files can also trigger this finding.",
        "Read the flagged passage to check whether it requests private data or warns against sharing it."),
    "RT-TOOL-DESC": Explanation(
        "A tool description needs closer review",
        "The description is unusually long or discusses actions beyond the tool's apparent job. "
        "Your AI reads this description when deciding how to use the tool.",
        "Compare the flagged description with the tool's stated purpose before connecting it."),
    "RT-UNREAD": Explanation(
        "This file could not be checked",
        "The file is too large or in a format unpick cannot read. "
        "Its contents have not been checked for problems.",
        "Ask the author for readable source for the flagged file before installing it."),
    "RT-JUDGE": Explanation(
        "An AI reviewer raised a concern",
        "An AI reviewer found something to inspect. Its opinion can be wrong and needs a person to verify it.",
        "Read the flagged passage alongside the reviewer's explanation before installing."),
    "RT-JUDGE-FAILED": Explanation(
        "The AI review did not finish",
        "The AI reviewer did not return a usable answer for this file. "
        "The missing review leaves its safety unknown.",
        "Run `unpick judges` to check which AI reviewers are available before retrying."),
}

BACKEND_EXPLANATIONS = {
    "cisco-skill-scanner": Explanation(
        "An extra scanner found a concern",
        "Cisco's skill scanner flagged this content. Its original rule and evidence appear below.",
        "Read the flagged passage and the scanner's explanation before installing."),
    "cisco-mcp-scanner": Explanation(
        "A tool connection needs review",
        "Cisco's tool scanner flagged this connection or description. Its original evidence appears below.",
        "Compare the flagged behavior with the tool's stated purpose before connecting it."),
    "skillspector": Explanation(
        "An extra scanner found a concern",
        "SkillSpector flagged this content or a software dependency. Its original evidence appears below.",
        "Read the scanner's evidence for the flagged file or dependency before installing."),
    "yara-x": Explanation(
        "A scanner recognized a suspicious pattern",
        "A pattern-matching scanner found text associated with a possible threat. "
        "Examples and documentation can also match these patterns.",
        "Read the matched text in context before deciding whether to trust this file."),
    "jiffy": Explanation(
        "An extra scanner found a concern",
        "Jiffy flagged this content under its scanning rules. Its original evidence appears below.",
        "Read Jiffy's explanation for the flagged content before installing."),
}


def get_explanation(rule_id: str) -> Explanation:
    """Resolve an exact rule or an external scanner's open-ended rule category."""
    if rule_id in EXPLANATIONS:
        return EXPLANATIONS[rule_id]
    backend, separator, rule = rule_id.partition(":")
    if separator and rule and backend in BACKEND_EXPLANATIONS:
        return BACKEND_EXPLANATIONS[backend]
    raise KeyError(rule_id)


UNKNOWN_EXPLANATION = Explanation(
    "This finding needs review",
    "This rule is not in this version's explanation catalog. Its original evidence still needs review.",
    "Read the finding's original explanation before installing.")
