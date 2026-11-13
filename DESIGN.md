# AI Coding Mentor: design system and handoff

The interface is a game-style learning app: a course path of pressable nodes, a score bar, chunky
tactile controls. All of it lives in `frontend/src/game.css` (loaded last, after `App.css` and
`learning.css`, which keep the layout of each page).

## 1. Critique of the previous UI (why it changed)

| Finding | Severity | What replaced it |
|---|---|---|
| Slate `#0f172a` ground with cyan `#38bdf8` accents: the stock generated-dashboard palette | High | White ground, ink text, flat green / sky / gold / coral fills |
| Body text at 11–12.5px, labels in tiny tracked uppercase | High | 13.5px minimum, 14–15.5px body, sentence case |
| Gradients on banner, progress bars, badge cards; `backdrop-filter` blur on modals; drop shadows | Medium | Flat colour, tone steps, no blur, no shadows |
| Stat icons inside tinted rounded squares | Medium | Bare icon + large number |
| Horizontal top nav that collapsed to unlabeled icons under 1200px | Medium | Labelled side rail, icon rail under 1280px, bottom tab bar on phones |
| Course shown as stacked bordered boxes with nested rows | Medium | A winding path of nodes with one bouncing "Start" node |
| No entry page: visitors landed in the editor | Medium | Landing page for signed-out visitors |
| Copy such as "Gamification & Milestones", "Adaptive Learning Platform" | Low | "Trophy shelf"; subtitle removed |

Kept: every page, route, API call and control. The light/dark toggle stays (new visitors now start in light).

## 2. Tokens (`game.css`, `:root` and `:root[data-theme="dark"]`)

| Token | Light | Dark | Use |
|---|---|---|---|
| `--bg-surface` / `--bg-primary` / `--bg-card` | `#ffffff` | `#15202b` / `#15202b` / `#1a2733` | page, panels, cards |
| `--bg-secondary` | `#f3f5f7` | `#1e2c39` | tone step, bands |
| `--bg-hover` | `#e8ecf0` | `#2a3a49` | hover, bar tracks |
| `--border-color` | `#dce1e7` | `#35475a` | 2px outlines |
| `--text-primary` / `-secondary` / `-muted` | `#26303b` / `#4a5664` / `#667281` | `#eef3f7` / `#c2ccd6` / `#93a1af` | text |
| `--accent-cyan` `-emerald` `-amber` `-rose` `-purple` | `#1667b7` `#1a7f37` `#a15c00` `#c92a2a` `#7b3fc4` | `#6cc4ff` `#6fdc7c` `#ffc93c` `#ff8a80` `#c9a2ff` | coloured **text and icons** only |
| `--green` / `--green-lip` | `#55c764` / `#379e46` | same | primary action, lessons |
| `--sky` / `--sky-lip` | `#63bdf6` / `#3a94d1` | same | submit, tasks, selection |
| `--gold` / `--gold-lip` | `#ffc93c` / `#dba017` | same | XP, level, done, trophies |
| `--coral` / `--coral-lip` | `#ff7a70` / `#d9544b` | same | fourth unit colour, failure edge |
| `--locked` / `--locked-lip` | `#e3e7ec` / `#c4cad2` | `#2a3a49` / `#1c2833` | locked nodes |
| `--on-fill` | `#17222c` | same | text on every fill |
| `--tint-sky` / `--tint-green` | `#e4f3fe` / `#e6f7e9` | `#1d3549` / `#1c3a26` | selected, current, passed |
| `--r-sm` / `--r-md` / `--r-lg` | 10 / 14 / 18px | | radii |
| `--lip` | 4px | | depth of a pressable |
| `--font-sans` | Nunito 600–900 (Google Fonts), rounded system fallback | | all UI text |

Rules:
- Fills always carry `--on-fill` (dark ink). White text on these fills fails contrast; do not use it.
- `--accent-*` are for text and icons, never as a button background.
- No gradients, blur, glows or drop shadows. Depth is the lip only.

## 3. Components

| Component | Classes | Spec |
|---|---|---|
| Filled button | `.btn-primary-action` (+`.lg`), `.btn-run`, `.btn-primary-sm`, `.btn-primary-auth` | green, `--lip` bottom border, radius `--r-md`, weight 800 |
| Filled button, secondary colour | `.btn-submit`, `.filter-pill.active` | sky |
| Outline button | `.btn-secondary-action` (+`.lg`), `.btn-secondary`, `.btn-ghost-sm`, `.btn-tool`, `.icon-btn` | card fill, 2px outline, `--lip` bottom |
| Card | `.dash-card`, `.stat-card`, `.achievement-card`, … | 2px outline, radius `--r-lg` |
| Pressable card | `.course-card`, `.challenge-card`, `.picker-card` | card + `--lip` bottom; hover outline goes sky |
| Meter | `.progress-track` > `.progress-fill`, `.xp-bar` | 14px tall, pill; green for progress, gold for XP |
| Side rail / tab bar | `.side-nav` > `.nav-item` | 232px, 48px items; active = `--tint-sky` + sky outline |
| Score bar | `.hud` > `.stat-pill.streak`, `.lv-badge`, `.xp-bar` | 60px; `.xp-pop` announces XP and level-ups |
| Path | `.path` > `.unit` > `.unit-banner` + `ol.path-steps` > `button.step` | see below |
| Mascot | `<Mascot size bob />` | decorative SVG, `aria-hidden` |

### Path (`AcademyPage.tsx`, `CourseView`)
- One `.unit` per level. Banner colour cycles green, sky, gold, coral; locked units are grey.
- Steps in order: lesson, its practice task, …, level assessment.
- `.step` modifiers: `lesson` (green), `task` (sky), `assessment` (gold), `done` (gold + check), `locked` (grey + lock, `disabled`), `current` (ring + "Start" bubble).
- `current` = first open, not completed item in the course. Exactly one.
- Zig-zag: each `li` sets `--i`; CSS offsets it by `sin(var(--i) * 0.85) * 56px` (22px under 560px).

## 4. States and interactions

| Element | State | Behaviour |
|---|---|---|
| Any pressable | `:active` | face drops 2px onto its lip (transform + border), no layout shift |
| Any pressable | `:disabled` | greyscale, muted text, `not-allowed` |
| Any control | `:focus-visible` | 3px sky outline, 2px offset |
| Filled button | hover | `brightness(1.07)` |
| Path node | current | bubble bobs 6px, 1.4s loop |
| Score bar | XP rises | gold `.xp-pop` for 2.6s; on level-up, confetti + "Level N!" |
| Landing quiz | pick → Check | verdict text (`aria-live`), right answer swaps the button to "Keep going" → Academy |

Motion: `pop-in` 350ms `cubic-bezier(0.2, 1.4, 0.4, 1)`; `bob` ease-in-out. All animation and transition is off under `prefers-reduced-motion: reduce`.

## 5. Responsive

| Width | Shell | Landing |
|---|---|---|
| > 1280px | 232px labelled rail + score bar | two columns |
| 761–1280px | 78px icon rail (labels in `title` / `aria-label`) | two columns until 860px |
| ≤ 1100px | playground panels stack (existing rule) | |
| ≤ 760px | bottom tab bar, 7 equal items ≥ 44px; name and XP number hidden | one column, 16px gutter |

## 6. Routing and edge cases

- `App.tsx`: `currentTab` starts at `landing` when no `mentor_token` is stored, else `playground`.
- Signing in from the landing page goes to `academy`. Signing out returns to `landing`.
- Landing links to guarded tabs (Roadmap, Memory, Dashboard) open the sign-in modal for guests.
- Path with a locked level: all its steps are disabled and the unlock note shows under the banner.
- Course fully complete: no `current` node.
- Long lesson titles wrap inside a 260px label (180px on phones).
- Nunito fails to load: falls back to `ui-rounded` / Segoe UI; layout does not depend on it.

## 7. Accessibility

- Nav is a `<nav aria-label="Main">`; the active item has `aria-current="page"`; icon-only rails keep `aria-label`.
- Streak, level and XP bar carry text labels; the XP pop is in an `aria-live="polite"` region.
- Quiz answers are `aria-pressed` buttons; the verdict is announced.
- Status is never colour alone: done = check icon, locked = lock icon, difficulty = text badge.
