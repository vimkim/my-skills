# Visual and Copy Rules

## Editorial visual system

Default to a crisp light-paper editorial aesthetic rather than dark neon glassmorphism.

| Token | Value | Role |
|---|---|---|
| `--paper-bg` | `#ffffff` | Primary slide surface |
| `--paper-tint` | `#f8fafc` | Subtle table headers and plain tag background |
| `--ink-strong` | `#0f172a` | Headings, emphasis, primary metric numerals |
| `--ink-body` | `#334155` | Body prose and table cells |
| `--ink-muted` | `#64748b` | Lead lines, kickers, metadata captions |
| `--hairline` | `#e2e8f0` | Structural borders and row dividers |
| `--accent` | `#0f766e` | Domain accent (kickers, active indicators, key tags) |
| `--danger` | `#b91c1c` | Semantic error, failure, or conflict highlight |
| `--cli-bg` / `--cli-fg` | `#0f172a` / `#e2e8f0` | High-contrast terminal blocks as deliberate islands |

Typography: pair a clean geometric/Korean sans-serif (`Pretendard`, `Inter`, system sans) with a crisp monospace (`JetBrains Mono`) for CLI output, identifiers, and numeric labels. Keep prose concise and scannable on screen.

Replace these common AI deck tells:

- Dark radial-gradient backgrounds with glowing cyan/emerald borders on every slide.
- Identical rounded SaaS cards repeated slide after slide.
- Tracked ALL-CAPS eyebrow tags above every heading.
- Decorative `01 / 02 / 03` numbering on unordered concepts (reserve numbers for real sequences or sections).
- Click/slide-in entrance animations on every bullet list (use `v-click` only when sequential reveal clarifies a state change or surprise).

## Slide layout repertoire

Vary patterns so consecutive content slides never share the same skeleton. Keep height budgets calibrated for `canvasWidth: 980` at `1280x720`.

1. **Editorial Cover** (`layout: default` or `cover`): left accent bar (`border-l-4`) around kicker, display `<h1>`, and 1–2 line subtitle, followed by a 3-column hairline metadata strip.
2. **2-Up Visual Comparison**: lead sentence, `grid-cols-2 gap-6 h-[305px]` holding labeled `<MediaSlot>` or SVG frames (Before vs. After), and a single-line hairline takeaway at the bottom.
3. **Big-Stat + Rule-List + Terminal** (`grid-cols-12`): 5 columns with `.big-stat` metric and `.rule-list` constraints beside 7 columns of `.cli-block` concrete output.
4. **Full-Width SVG Stage + Takeaway Strip**: `.svg-stage h-[340px]` centered diagram above a 4-column hairline summary row (`border-t pt-2`).
5. **Quiet Section Divider** (`layout: section`): monospace section index (`01`, `02`), centered display title, and one-line topic scope.
6. **7:5 Diagram + CLI/Rule-List Split**: 7-column `.svg-stage h-[335px]` paired with 5 columns stacking a compact `.cli-block` and `.rule-list`.
7. **Diagram + Compact Editorial Table**: top diagram strip (`h-[138px]`) above an `.editorial-table` comparing two approaches across 3–4 concrete rows.
8. **Dual-Column Metric + CLI + Diagram** (`6:6` split): left column stacks a `.svg-stage h-[175px]` and `.rule-list`; right column pairs two `.big-stat` callouts with a `.cli-block` sample.
9. **Vertical Timeline Spine + Demo Slot** (`5:7` split): `.timeline-spine` with `.timeline-step` nodes (using `.timeline-dot.danger` for the failure step) beside a full-height `<MediaSlot>`.
10. **Top CLI + 2-Column Rule-List / Centered Closing** (`layout: center`): top `.cli-block` over two `.rule-list` columns for architecture summaries; `max-w-3xl mx-auto` with 3 numbered takeaways, optional grounded quote, and contact line for the closing slide.

## Anti-slop copy checklist

### English copy

- Cut AI vocabulary: `delve`, `crucial`, `pivotal`, `landscape`, `testament`, `underscore`, `vibrant`, `showcase`, `foster`, `enhance`, `leverage`, `utilize`.
- Use `is` or `has` instead of `serves as`, `stands as`, or `boasts`.
- Cut `not just X, but Y`, forced triads, and trailing `-ing` participial clauses (`ensuring...`, `highlighting...`).
- Replace abstract metaphor nouns (`paradigm`, `flywheel`, `substrate`, `nexus`, `north star`) with concrete mechanisms, files, or numbers.
- Use sentence case headings, straight quotes, periods/commas instead of em dashes, and zero decorative emojis.
- Cut bold-label-colon restatements (`**Performance:** Performance improved...`); state the fact directly.

### Korean copy

- Cut translationese (`~에 있어`, `~을/를 통해 ~을 제공합니다`, `~하는 것이 중요합니다`, `강력한 ~을 경험하세요`).
- Replace excessive nominalization and passive voice (`~됨을 보장합니다`, `~이 수행됩니다`) with active verbs and clear subjects.
- Break forced 3-item symmetry when 2 or 4 items reflect reality.
- Remove em dashes (`—`), curly quotes, decorative emojis, and inflated significance (`혁신적인`, `패러다임 전환`, `게임 체인저`).
- Keep slide headings concrete and claim-driven rather than vague topic labels.

## Conversational presenter notes

Write speaker notes inside HTML comments at the bottom of each slide:

```markdown
<!--
[04:15 - 05:15] Topic label
Natural spoken explanation in short sentences. Connect from the previous slide,
highlight one detail on screen, and avoid reading slide bullets word-for-word.
-->
```

Rules for presenter notes:

- Include realistic `[MM:SS - MM:SS]` timestamps summing to the talk's `duration`.
- Write as the speaker talks: contractions, direct transitions, honest trade-offs, and demo cues.
- Keep technical identifiers accurate (exact command names, flags, metrics) while keeping surrounding prose conversational.
