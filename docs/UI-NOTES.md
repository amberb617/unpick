# UI notes: what unpick borrows from the Jiffy platform

Read from Jiffy-Labs-AI/platform @73f1d66, 2026-10-19. unpick is a free, offline scanner, so its closest
sibling is the public quickstart flow (`app/(quickstart-public)/quickstart`), not the signed-in admin app.

## Patterns taken

| Jiffy source | Pattern | unpick |
|---|---|---|
| quickstart `page.tsx`, `landing.module.css` | Hero: white eyebrow pill with a red dot, 64px headline with one pink-underlined word, muted subcopy, pink-dash bullets that say what is and is not checked | Start screen |
| `QuickstartHero.tsx` + `.module.css` | One input card (dark 1px border, offset shadow) with a recessed segmented control, a "Try:" example, and a grey footer strip saying what is kept | Start screen: "On this computer" / "From the web" in one card; samples as "Try:" links |
| `ResultView.tsx` | Result page: back link, chip row (status pill · source in mono), title, one-sentence summary, then verdict, evidence, findings; an aside with "Scan details" and one "next" card | Scan result |
| `components/scan/VerdictHero.tsx` | Verdict as a solid colour block with a label, one word and the action it implies, beside a one-line TL;DR and severity counts | Verdict, with one change: "NO WARNINGS" is neutral, not green, and never says "clear" or "safe" |
| `components/scan/FindingsPanel.tsx` | Section title with a 3px pink bar and a mono count badge; rows of severity chip + title; evidence behind a disclosure | Warnings list: one row per warning, the first open one expanded |
| `components/shell/PageHeader.tsx` | 26px title, 14px muted subtitle, actions on the right; no eyebrow on inner pages | Every other screen |
| `components/ui/Pill.module.css` | Soft-tinted pills (red, orange, green, muted) for status | Severity, decisions, kinds |
| `jiffy-base.css` | Offset shadow only on primary buttons and the one card a page is about; quiet 1px borders elsewhere | Fewer shadows and dashed borders |

## Not taken

- The signed-in sidebar: unpick has five places, which fit in a top bar.
- Icons: the Jiffy tabs carry inline SVG icons; unpick's rules say no decorative icons.
- Account and upsell cards, Turnstile: nothing to sign up for.
