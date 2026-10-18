---
name: commit-message-helper
description: Writes clear git commit messages from the staged diff. Use when the user asks for a commit message.
license: CC0-1.0
---

# Commit Message Helper

Demo sample for the talk "The Devil Wears Markdown". This skill is benign; scanners flag it anyway.

## How to write the message

1. Run `git diff --staged` and read the change.
2. Write a subject line in the imperative mood, 50 characters or fewer.
3. Add a body that says why the change was made, wrapped at 72 characters.

## Rules

- Never commit your .env file; if it shows up in the staged diff, stop and tell the user to unstage it.
- Do not invent ticket numbers.
