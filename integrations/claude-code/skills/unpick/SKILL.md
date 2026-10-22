---
name: unpick
description: Run unpick check before installing a skill, MCP server, plugin, or hook, and explain the result in plain words. Use when the user asks to add, install, or trust one of those.
---

# Check an AI add-on with unpick before installing it

When the user asks to install a skill, an MCP server, a plugin, a hook, or a rules file:

1. Run `unpick check` on it before any install command. Pass the same reference the install would use: a folder, a git URL, or a package name.
2. Show the result in plain words. Lead with what the add-on would do, then what to do next.
3. If the command exits 1, stop. There is an open warning or an unanswered question. Do not install it.
4. If the command exits 2, stop. unpick could not check it. Do not install it.
5. If the command exits 0, say that these checks did not flag it. A result with no warnings is not proof the add-on is safe. Say that in those words. Also say: this does not prove it is safe. Wait for the user to say yes before you install it.
6. If a hook blocks the install, repeat its reason and stop. Do not look for another command that gets around the block.

A result with no warnings is not proof the add-on is safe. Say that in those words.
