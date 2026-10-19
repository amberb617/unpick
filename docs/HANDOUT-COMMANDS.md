# Read the raw bytes, with nothing to install

Six commands for the handout and slide 23: three for macOS and Linux, three for Windows PowerShell 5.1
and PowerShell 7. Every line is 60 characters or narrower. Replace `SKILL.md` with the file you are
checking. Each one was run on demo sample A (`unpick demo`), and must find its planted problem; CI runs
them again on every push (tests/handout/, job `handout-commands`). Outputs below are the real recorded
output, cut to fit the page.

## macOS and Linux (bash or zsh)

**1. Show hidden characters.** `cat -v` prints invisible bytes as `M-` sequences; `LC_ALL=C` makes it do so
for UTF-8 too.

```sh
LC_ALL=C cat -v SKILL.md | grep -n 'M-'
```

**2. Find invisible Unicode:** zero-width characters, bidirectional controls and Unicode tag characters.

```sh
LC_ALL=C grep -nE \
  $'\xe2\x80[\x8b-\x8f\xaa-\xae]|\xf3\xa0' SKILL.md
```

**3. Grep for the red-flag words:** prerequisite, pipe to a shell, base64, `.ssh`, `.env`, "tell the user".

```sh
grep -niE \
 'prereq|\| *(ba)?sh|base64|\.ssh|\.env|tell the user' \
 SKILL.md
```

Recorded output (identical on all three):

```text
== Darwin arm64, GNU bash, version 3.2.57 (macOS 26, CI macos-latest); zsh 5.9 on macOS 26.6 (local)
== Linux x86_64, GNU bash 5.2.21 (CI ubuntu-latest); Linux aarch64, bash 5.2.21, GNU grep 3.11 (Docker ubuntu:24.04)
--- 1
24:3. Use the standard page size for the user's region.M-s
--- 2
24:3. Use the standard page size for the
--- 3
12:## Prerequisites
17:echo ZWNobyAiaGVsbG8gZnJvbSB0aGUgdW5waWNrIGRlbW8i | bas
```

Notes: macOS grep has no `-P`, so command 2 matches the UTF-8 bytes directly; that is why it needs
`LC_ALL=C`. In zsh, write it exactly as shown (`-E` with a plain `|`); `\|` inside `$'...'` silently
matches nothing.

## Windows PowerShell 5.1 and PowerShell 7

**1. Show hidden characters.** Every character that is not plain printable ASCII becomes `<?>`.

```powershell
gc SKILL.md -Enc UTF8 | % { $_ -replace '[^\t -~]','<?>' }
```

**2. Find invisible Unicode.** `-Enc UTF8` matters in 5.1, which otherwise reads the file as ANSI.

```powershell
sls -Enc UTF8 '[\u200B-\u200F\u202A-\u202E]|\uDB40' SKILL.md
```

**3. Grep for the red-flag words.** `sls` (Select-String) is case-insensitive by default.

```powershell
sls -Path SKILL.md -Pattern `
 'prereq|\|\s*(ba)?sh|base64|\.ssh|\.env|tell the user'
```

Recorded output (identical on both):

```text
== PowerShell 5.1.26100.33438 (Desktop) on Microsoft Windows NT 10.0.26100.0 (CI windows-latest)
== PowerShell 7.6.6 (Core) on Microsoft Windows NT 10.0.26100.0 (CI windows-latest)
== PowerShell 7.4.21 (Core) on Linux aarch64 (Docker mcr.microsoft.com/dotnet/sdk:8.0)
--- 1
3. Use the standard page size for the user's region.<?><?>
--- 2
SKILL.md:24:3. Use the standard page siz
--- 3
SKILL.md:12:## Prerequisites
SKILL.md:17:echo ZWNobyAiaGVsbG8gZnJvbSB0aGUgdW5waWNrIGRlb
```

Notes: type the `\u` escapes exactly as shown; they are text, not the characters themselves. Command 1's
`<?>` count is per character on screen; a Unicode tag character is one `<?>` pair because PowerShell
strings store it as two halves of a surrogate pair.
