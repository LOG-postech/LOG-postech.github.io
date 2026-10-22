# LOG-postech.github.io

Website of the Lee Optimization Group at POSTECH: <https://opt.postech.ac.kr>.

Content and design are kept apart. Content is data in `data/`. Design is
templates in `templates/`. `tools/build.py` combines them into the site, and a
GitHub Action publishes it on every push to `main`.

```text
data/                  content — one directory per kind, each with a README
  news/                one .yaml file per year
  publications/        papers.bib (one BibTeX file, all papers)
  members/             members.yaml + photos/  (@tags for people)
  gallery/             gallery.yaml + photos/  (thumbnails are generated)
  research/            topics.yaml + icons/
  site.toml            lab name, navigation, footer logos
    */config.toml      presentation settings for that kind of content
templates/             page design (Jinja + HTML/CSS)
  base.html            the frame every page shares: head, header, nav, footer
  partials/*.css       CSS shared by every page, incl. the layout tokens
  <page>.html          one per page: its own CSS, layout and scripts
static/                copied to the site as is (logos, lab photo, js/)
tools/build.py         renders data + templates into _site/
```

## Which file do I edit?

| I want to… | Edit |
|---|---|
| add news, a paper, a member, a photo, a research topic | an entry in `data/<kind>/`; its `README.md` explains how |
| change how many items show, date format, thumbnail size, … | `data/<kind>/config.toml` |
| change the nav, footer or lab name everywhere | `data/site.toml` |
| change the design of every page (spacing, fonts, colours) | `templates/partials/chassis.css` (layout tokens) or `templates/base.html` |
| change the design of one page | `templates/<page>.html` |

## Build and preview locally

```bash
pip install -r requirements.txt       # once; needs Python 3.11+
brew install imagemagick              # once (Ubuntu: apt install imagemagick)
tools/setup-hooks.sh                  # once per clone: enables the pre-commit hook

python3 tools/build.py --serve        # build, then open http://localhost:8000
python3 tools/build.py --check        # only validate data/
```

`_site/` is build output: never edit it, and it is not committed.

## Commit hook

`tools/setup-hooks.sh` enables a pre-commit hook that does two things:

- validates `data/` (file names, required fields, missing photos), and
- shrinks new photos to their display size and strips EXIF/GPS before they enter
  git history. Rules are in `tools/optimize-images.sh`.

## Deployment

`.github/workflows/deploy.yml` builds and publishes the site on every push to
`main`. Pull requests are built as a check but not published. This needs
**Settings → Pages → Build and deployment → Source: GitHub Actions**.
