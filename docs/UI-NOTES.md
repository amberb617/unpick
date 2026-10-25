# UI notes: the patterns unpick follows

unpick is a free, offline scanner, so its layout follows a public quickstart flow (paste something, get a
result page), not a signed-in admin app.

## Patterns taken

| Pattern | unpick |
|---|---|
| Hero: white eyebrow pill with a red dot, 64px headline with one pink-underlined word, muted subcopy, pink-dash bullets that say what is and is not checked | Start screen |
| One input card (dark 1px border, offset shadow) with a recessed segmented control, a "Try:" example, and a grey footer strip saying what is kept | Start screen: "On this computer" / "From the web" in one card; samples as "Try:" links |
| Result page: back link, chip row (status pill · source in mono), title, one-sentence summary, then verdict, evidence, findings; an aside with "Scan details" and one "next" card | Scan result |
| Verdict as a solid colour block with a label, one word and the action it implies, beside a one-line TL;DR and severity counts | Verdict, with one change: "NO WARNINGS" is neutral, not green, and never says "clear" or "safe" |
| Section title with a 3px pink bar and a mono count badge; rows of severity chip + title; evidence behind a disclosure | Warnings list: one row per warning, the first open one expanded |
| 26px title, 14px muted subtitle, actions on the right; no eyebrow on inner pages | Every other screen |
| Soft-tinted pills (red, orange, green, muted) for status | Severity, decisions, kinds |
| Offset shadow only on primary buttons and the one card a page is about; quiet 1px borders elsewhere | Fewer shadows and dashed borders |

## Not taken

- A sidebar: unpick has five places, which fit in a top bar.
- Icons on tabs: unpick's rules say no decorative icons.
- Account and upsell cards, bot checks: nothing to sign up for.
