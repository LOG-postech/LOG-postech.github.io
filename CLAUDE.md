# CLAUDE.md — Lee Optimization Group Homepage

This is a static HTML/CSS academic lab website for the **Lee Optimization Group (LOG)** at POSTECH.

## Pages

| File | Purpose |
|---|---|
| `index.html` | Home — lab intro, news, acknowledgements |
| `research.html` | Research areas |
| `publications.html` | Paper list |
| `group.html` | Lab members |
| `hiring.html` | Open positions |
| `contact.html` | Contact info |
| `gallery.html` | Lab photos |

## Design Conventions (must be preserved)

- **Background**: `#FAF8F5` (warm off-white)
- **Primary color**: `#1B3A8A` (deep blue); hover/accent: `#3B6FD4`
- **Top rule**: 3px gradient `#1B3A8A → #3B6FD4 → #93A8D8`
- **Heading font**: EB Garamond (serif), weight 500
- **Body font**: Inter (sans-serif), weights 300/400/500/600
- **Max content width**: 800px, centered via `.inner`
- **Padding**: `clamp()` for responsive spacing
- **Text color**: `#111` (headings), `#374151` (body), `#6b7280` (muted)
- **Links**: `#1B3A8A`, underline on hover only

## Should-Be-Satisfied Checklist

When adding or modifying any page, verify all of the following:

### Consistency
- [ ] Top gradient rule (`<div class="top-rule">`) is present on every page
- [ ] Navigation links are identical across all pages, with the correct `active` class on the current page
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
- [ ] **Lab name font size is fixed at `2.3em`** — do not use `clamp()` with a viewport unit for `.lab-name`, and do not override it in media queries
- [ ] **Body text is unified at `0.93em`** across all pages — `p`, `.intro`, and equivalent paragraph elements must use `0.93em`, matching `index.html`
- [ ] **Logo card containers use `flex-wrap: wrap`** so logos reflow to multiple rows on narrow screens instead of shrinking — do not set `flex-wrap: nowrap` or force images to scale down inside logo cards (`.sponsor-logos`, `.collab-logos`)

### Content
- [ ] External links open in a new tab (`target="_blank"`) and have `rel="noopener"`
- [ ] Images have descriptive `alt` text
- [ ] Large images use `loading="lazy"`
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
