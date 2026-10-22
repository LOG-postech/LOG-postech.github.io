# LOG-postech.github.io

Website of the Lee Optimization Group at POSTECH: <https://opt.postech.ac.kr>.

Content and design are kept apart. Lists (news, papers, members, photos) are
data in `data/`. Page bodies are in `content/`, design in `layout/`. GitHub Pages
builds the site with Jekyll straight from `main`, and `static/js/site.js` renders
the data in the browser.

```text
data/                  lists — one directory per kind, each with a README
  news/                one .yaml file per year
  publications/        papers.bib (one BibTeX file, all papers)
  members/             members.yaml + photos/  (@tags for people)
  gallery/             gallery.yaml + photos/ + thumbs/ (thumbs are generated)
    */config.toml      presentation settings for that kind of content
content/               the body of every page (front matter: title, address)
  research.html, hiring.html, contact.html    text, plain HTML
  index.html, news.html, ...                  page parts around the lists
layout/                design
  base.html            the frame every page shares: head, header, nav, footer
  partials/            CSS shared by every page (incl. the layout tokens); data.html
  styles/<page>.css    each page's own CSS
  scripts/<page>.js    each page's own script; drawer.js is shared
static/                logos, lab photo, research icons, js/site.js
_config.yml            Jekyll settings, lab name, navigation, footer logos
tools/build.py         checks data/ and makes gallery thumbnails
```

## Which file do I edit?

| I want to… | Edit |
|---|---|
| add news, a paper, a member, a photo | an entry in `data/<kind>/`; its `README.md` explains how |
| change how many items show, date format, … | `data/<kind>/config.toml` |
| change the research topics, hiring or contact text | `content/research.html`, `content/hiring.html`, `content/contact.html` |
| add a new page | a new `content/<page>.html` (front matter like the others) and a `layout/styles/<page>.css`; add it to `nav` in `_config.yml` |
| change the nav, footer or lab name everywhere | `_config.yml` |
| change the design of every page (spacing, fonts, colours) | `layout/partials/chassis.css` (layout tokens) or `layout/base.html` |
| change the design of one page | `layout/styles/<page>.css` |

## Check and preview locally

```bash
tools/setup-hooks.sh                  # once per clone: enables the pre-commit hook
python3 tools/build.py --check        # check data/ (needs: pip install -r requirements.txt)
python3 tools/build.py                # check, and make thumbnails for new photos
bundle install && bundle exec jekyll serve   # preview at http://localhost:4000 (Ruby)
```

`_site/` is preview output: never edit it, and it is not committed.

## Commit hook

`tools/setup-hooks.sh` enables a pre-commit hook that:

- checks `data/` (names, required fields, @tags, paper keys, missing photos),
- shrinks new photos to their display size and strips EXIF/GPS (rules in
  `tools/optimize-images.sh`), and
- makes the thumbnail of each new gallery photo in `data/gallery/thumbs/`.

## Deployment

Push to `main`. GitHub Pages ("Deploy from a branch", `main`, `/`) runs Jekyll
on the repository as it is; no other setup is needed. The custom domain comes
from the `CNAME` file at the root.
