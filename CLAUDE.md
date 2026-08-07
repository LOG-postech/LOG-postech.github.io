# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a static HTML/CSS academic lab website for the **Lee Optimization Group (LOG)** at POSTECH, deployed via GitHub Pages at `opt.postech.ac.kr`. There is no build step — edit HTML files directly and push to deploy.

## Pages

| File | Purpose |
|---|---|
| `index.html` | Home — lab intro, news, acknowledgements |
| `news.html` | Full news archive (linked from the home page) |
| `research.html` | Research areas |
| `publications.html` | Paper list |
| `group.html` | Lab members |
| `hiring.html` | Open positions |
| `contact.html` | Contact info |
| `gallery.html` | Lab photos |

## Architecture

**CSS is inline per-page** — each HTML file contains a full `<style>` block in `<head>`. There is no shared stylesheet. When making a visual change that must apply site-wide (e.g., changing a font size or color), you must update every page's `<style>` block individually.

Spacing is the exception: it is driven by a `:root` block of CSS custom properties that
is duplicated verbatim at the top of every page's `<style>`. See **Layout Tokens** below
before touching any margin, padding, or gap.

**Asset directories:**
- `logo/` — sponsor and collaborator logos (PNG/SVG); referenced in `index.html` and `research.html`
- `research_focus/` — thumbnail images for research area cards in `research.html`
- `stories/` — gallery photos for `gallery.html` (year-prefixed filenames, e.g., `25_iclr.jpg`)
- `stories/thumbs/` — **generated**, never hand-made; see Images below
- `group_profile/` — member headshots for `group.html` (filename = person's name slug)
- `lab_photo/` — home page hero photo

## Images

**Do not resize or compress images by hand.** Drop the original in, commit, and the
pre-commit hook does it — resizing, re-encoding, stripping EXIF (which also removes
GPS coordinates from lab photos), generating the gallery thumbnail, and updating any
HTML path if the extension changes.

```bash
tools/setup-hooks.sh              # once per clone — enables the hook
tools/optimize-images.sh          # optimize everything that needs it
tools/optimize-images.sh --check  # report only, change nothing
```

Requires ImageMagick (`apt install imagemagick` / `brew install imagemagick`). The hook
refuses the commit if it is missing rather than letting a 10MB camera original into
history; `git commit --no-verify` bypasses it.

Targets are ~3x the CSS display size, so images stay sharp on retina screens:

| Directory | Max long edge | Format | Displayed at |
|---|---|---|---|
| `stories/` | 2560px | JPEG q82 | click-through full view |
| `stories/thumbs/` | 600px square | JPEG q80 | 112–180px grid tiles |
| `lab_photo/` | 1600px | JPEG q85 | ≤800px hero |
| `group_profile/` | 512px | JPEG q85 | 140px avatar |
| `research_focus/` | 500px | keep (PNG stays PNG — line art) | 165px card |
| `logo/` | untouched | — | logos must stay crisp |

Processed files carry a `log-opt-v1` marker in their image comment, so re-running is
safe — already-optimized files are skipped, never re-compressed. To force a full
re-pass after changing the rules, bump `MARKER` in `tools/optimize-images.sh`.

Gallery photos are stored as lowercase `.jpg`; the optimizer normalizes `.png`/`.jpeg`/
`.JPG` and rewrites the HTML reference for you.

**Scratch files** (not published pages, do not modify unless explicitly asked): `index_v1.html`, `design_demo.html`, `font_compare.html`

## Layout Tokens (read this before changing any spacing)

Every page opens its `<style>` block with an identical `:root` block of CSS custom
properties. **This block is the single source of truth for spacing** — all chassis
rules (`.inner`, `header`, `.lab-name`, `nav`, `footer`, section headings, body text)
reference it via `var(...)` instead of literal pixel values.

| Token | Value | Controls |
|---|---|---|
| `--content-max` | `800px` | `.inner` max width |
| `--page-pad-top` / `--page-pad-x` / `--page-pad-bottom` | `clamp()` | `.inner` padding |
| `--header-pad-bottom` / `--header-gap` | `28px` / `40px` | header padding + gap to `<main>` |
| `--lab-name-gap` | `18px` | lab name → nav |
| `--nav-gap` | `clamp(10px, 3vw, 24px)` | space between nav links |
| `--section-gap` | `40px` | space **above** a section heading |
| `--heading-gap` | `14px` | space **below** a section heading |
| `--para-gap` | `14px` | space between stacked paragraphs |
| `--footer-gap` / `--footer-pad-top` | `52px` / `20px` | footer offset + padding |
| `--footer-logo-gap` / `--footer-logo-h` | `14px` / `28px` | footer logo row |
| `--text-body` / `--leading-body` | `0.93em` / `1.85` | body text size + line height |
| `--rule-color` | `#e2e6f0` | header/footer hairlines |

**Rules for editing:**
- To change spacing site-wide, edit the token value — in **all 8 pages**, since the
  block is duplicated per page. The blocks must stay byte-identical.
- Never reintroduce a literal `px` for anything a token already covers.
- The `@media (max-width: 900px)` block **redefines tokens on `:root`** rather than
  re-declaring `.inner` / `header` / `.footer-logos img`. Add responsive spacing the
  same way.
- Section headings (`h2`, `h3`, `.year-divider`, `.news-year`) all use
  `margin-top: var(--section-gap)` + `margin-bottom: var(--heading-gap)`, paired with
  a `:first-of-type { margin-top: 0 }` rule so the first heading sits flush.

## Design Conventions (must be preserved)

- **Background**: `#ffffff`
- **Primary color**: `#1B3A8A` (deep blue); hover/accent: `#3B6FD4`
- **No top rule** — the 3px gradient bar was deliberately removed (`6d008de`, `a3a85de`); do not reintroduce it
- **Heading font**: EB Garamond (serif), weight 500
- **Body font**: Inter (sans-serif), weights 300/400/500/600
- **Max content width**: 800px, centered via `.inner` (`--content-max`)
- **Padding**: `clamp()` for responsive spacing (`--page-pad-*`)
- **Text color**: `#111` (headings), `#374151` (body), `#6b7280` (muted)
- **Links**: `#1B3A8A`, underline on hover only

## Should-Be-Satisfied Checklist

When adding or modifying any page, verify all of the following:

### Consistency
- [ ] Navigation links are identical across all pages, with the correct `active` class on the current page
- [ ] Drawer nav has both `nav a.active` and `.nav-drawer a.active` styling
- [ ] Lab name / logo links back to `index.html` on all inner pages
- [ ] Favicon (`logo/log_logo.png`) is referenced in `<head>`
- [ ] Google Fonts `<link>` for EB Garamond + Inter is present
- [ ] Page `<title>` follows the pattern `Page Name | Lee Optimization Group`

### Style
- [ ] No inline styles that override the established color palette
- [ ] No new fonts introduced without approval
- [ ] New sections reuse existing CSS classes (`.inner`, `.news-item`, etc.) before adding new ones
- [ ] Responsive: layout must not break on mobile (≤ 480px) or tablet (≤ 768px)
- [ ] **Font sizes must not shrink on small screens** — never use `body { font-size: 14px }` or reduce `font-size` for text elements inside `@media` queries
- [ ] **Lab name font size is fixed at `2.8em`** — do not use `clamp()` with a viewport unit for `.lab-name`, and do not override it in media queries
- [ ] **Body text uses the tokens** — `p`, `.intro`, `.news-content`, list items and equivalent paragraph elements must use `font-size: var(--text-body)` and `line-height: var(--leading-body)`, never literal values
- [ ] **Spacing uses the tokens** — no literal `px` for page padding, header/footer offsets, section-heading margins, or paragraph gaps; see the Layout Tokens section
- [ ] **The `:root` token block is identical in all 8 pages** — after editing one, propagate it verbatim to the rest
- [ ] **Logo card containers use `flex-wrap: wrap`** so logos reflow to multiple rows on narrow screens instead of shrinking — do not set `flex-wrap: nowrap` or force images to scale down inside logo cards (`.sponsor-logos`, `.collab-logos`)
- [ ] **Members grid keeps fixed avatar size** — member photos must not shrink on small screens; reduce the number of columns instead (`4 → 3 → 2 → 1`) and keep visible spacing between cards
- [ ] **Gallery page uses dynamic grid** — `.gallery-grid` should use `repeat(auto-fit, minmax(..., 1fr))` with consistent `gap`, so tile count adapts smoothly to viewport width

### Content
- [ ] External links open in a new tab (`target="_blank"`) and have `rel="noopener"`
- [ ] Images have descriptive `alt` text
- [ ] Large images use `loading="lazy"`
- [ ] **Images were never hand-resized** — the pre-commit hook handles it; see Images above
- [ ] **No hand-made files in `stories/thumbs/`** — thumbnails are generated from `stories/`
- [ ] Dates are written consistently: `MMM YYYY` (e.g., `Mar 2025`)
- [ ] Paper/thesis links use lowercase labels: `[paper]`, `[thesis]`, `[code]`, `[slides]`

### Code Quality
- [ ] No JavaScript frameworks or build tools — plain HTML/CSS only
- [ ] No unused CSS rules left behind after edits
- [ ] HTML is valid and properly nested
- [ ] No hardcoded absolute URLs for internal pages (use relative paths)

## Design Inspiration & Originality

The professor wants the site to have **uniqueness and originality**. The references below are all personal academic websites — we are a **lab** website, so we do not copy their structure directly. Instead, extract specific UI patterns and adapt them to a multi-person lab context.

### Reference Sites

| Site | Owner | What to borrow |
|---|---|---|
| [arkitus.com/research](https://arkitus.com/research/) | Ali Eslami | Research sections organized **by topic/category** with thumbnail images per paper; anchor-based in-page navigation |
| [alnurali.com/publications](https://www.alnurali.com/publications/index.html) | Alnur Ali | **Representative publications panel** (curated cards with image + abstract excerpt) before the full list; scroll progress indicator; dashed→solid border hover on nav links |
| [theis.io](https://theis.io/) | Lucas Theis | Ultra-minimal aesthetic — no decorative borders or chrome; **content is the interface**; publication entries as clean typographic blocks without explicit card boxes |
| [pluskid.org](https://pluskid.org/) | Chiyuan Zhang | Restrained, accessibility-first layout; understated horizontal nav; personality through simplicity |

### Key Patterns to Adopt (adapted for lab context)

- **Representative publications panel** (`publications.html`): Show 3–5 highlighted papers as visual cards (thumbnail + title + one-line summary) at the top, before the full chronological list. Inspired by alnurali.com.
- **Research organized by topic** (`research.html`): Each research area has a clear category label and an associated paper thumbnail. Already partially done — reinforce with stronger visual separation. Inspired by arkitus.com.
- **Scroll progress indicator**: A thin bar at the top of the page (below the gradient rule) that fills as the user scrolls. Useful on long pages (`publications.html`, `group.html`). Inspired by alnurali.com.
- **Publication entries as typographic blocks**: On the full publication list, avoid heavy box borders. Use whitespace and typographic weight to separate entries instead. Inspired by theis.io.
- **Nav hover treatment**: Consider dashed underline → solid underline on hover for nav links (subtle, distinctive). Inspired by alnurali.com.

### What NOT to import
- Single-column personal bio layout — we need multi-section lab structure
- Profile photo as hero — we use the lab group photo instead
- No-navigation style (theis.io) — our site has 6 distinct pages that need nav
- Heavy animations or JavaScript frameworks — keep plain HTML/CSS

## Commit Style

Follow the existing prefix convention:
- `ADD:` — new content (people, papers, news items, logos)
- `STYLE:` — visual/CSS changes
- `PERF:` — performance improvements
- `FIX:` — bug fixes
- `REFACTOR:` — structural changes with no visual effect

Do **not** add `Co-Authored-By` or any Claude attribution in commit messages.
