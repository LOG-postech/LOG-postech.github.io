#!/usr/bin/env python3
"""Build the site: read data/, render templates/, write _site/.

  tools/build.py            build into _site/
  tools/build.py --check    validate data/ only, write nothing (exit 1 on errors)
  tools/build.py --serve    build, then serve _site/ on http://localhost:8000

Content lives in data/<database>/ — one directory per kind of content, each with
its entries, a config.toml for presentation settings, and a README.md on how to
add an entry. Pages are Jinja templates in templates/. Files in static/ are
copied to the site root unchanged.

Images are copied byte-for-byte. The only generated images are gallery
thumbnails, made from the photo itself with ImageMagick (see data/gallery).
"""

import argparse
import datetime as dt
import functools
import http.server
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import markdown
import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from markupsafe import Markup, escape

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
TEMPLATES = ROOT / "templates"
STATIC = ROOT / "static"
OUT = ROOT / "_site"

PAGES = ["index", "news", "research", "publications", "group", "gallery", "photo", "hiring", "contact"]

# Where each database's files are published. These paths are part of the site's
# public URLs (photo.html?image=stories/...), so they stay as they always were.
PUBLISH = {
    DATA / "gallery" / "photos": "stories",
    DATA / "members" / "photos": "group_profile",
    DATA / "research" / "icons": "research_focus",
}
THUMBS = "stories/thumbs"


class DataError(Exception):
    pass


errors = []


def fail(msg):
    errors.append(msg)


# ------------------------------------------------------------------ helpers

def load_config(db):
    path = DATA / db / "config.toml"
    with path.open("rb") as f:
        return tomllib.load(f)


def load_yaml(path):
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


_md = markdown.Markdown()
_EXTERNAL = re.compile(r'<a href="(https?://[^"]+)">')


def render_inline(text):
    """One paragraph of markdown -> inline HTML (no wrapping <p>).

    External links open in a new tab with rel="noopener", as everywhere on the
    site; relative links (news.html, ...) stay in the same tab.
    """
    html = _md.reset().convert(text.strip())
    if html.startswith("<p>") and html.endswith("</p>"):
        html = html[3:-4]
    html = _EXTERNAL.sub(r'<a href="\1" target="_blank" rel="noopener">', html)
    return Markup(html)


_SPOT = re.compile(r"\*\*(.+?)\*\*")


def render_venue(text):
    """Venue line: plain text, with **...** marking a highlight (Oral, awards)."""
    return Markup(_SPOT.sub(r'<span class="spotlight">\1</span>', str(escape(text))))


def external(url):
    return bool(re.match(r"https?://", url or ""))


# --------------------------------------------------------------------- news

NEWS_NAME = re.compile(r"^(\d+)_(\d{4})-(\d{2})(?:-(\d{2}))?_([a-z0-9][a-z0-9-]*)\.md$")
NEWS_KEYS = {"people", "paper"}


def split_front_matter(text, where):
    if not text.startswith("---\n"):
        return {}, text
    try:
        _, head, body = text.split("---\n", 2)
    except ValueError:
        raise DataError("%s: front matter has no closing ---" % where)
    return yaml.safe_load(head) or {}, body


def load_news():
    cfg = load_config("news")
    entries, seen = [], {}
    for path in sorted((DATA / "news").glob("*.md")):
        if path.name == "README.md":
            continue
        m = NEWS_NAME.match(path.name)
        if not m:
            fail("news/%s: name must be {idx}_{YYYY-MM or YYYY-MM-DD}_{simple-title}.md" % path.name)
            continue
        idx = int(m.group(1))
        if idx in seen:
            fail("news/%s: index %d is already used by %s" % (path.name, idx, seen[idx]))
        seen[idx] = path.name
        try:
            date = dt.date(int(m.group(2)), int(m.group(3)), int(m.group(4) or 1))
        except ValueError:
            fail("news/%s: invalid date in file name" % path.name)
            continue
        try:
            front, body = split_front_matter(path.read_text(encoding="utf-8"), "news/" + path.name)
        except DataError as e:
            fail(str(e))
            continue
        unknown = set(front) - NEWS_KEYS
        if unknown:
            fail("news/%s: unknown field(s) %s (allowed: %s)" % (path.name, ", ".join(sorted(unknown)), ", ".join(sorted(NEWS_KEYS))))
        if not body.strip():
            fail("news/%s: empty body" % path.name)
        attrs = ""
        for key in ("people", "paper"):
            if front.get(key):
                attrs += ' data-%s="%s"' % (key, escape(front[key]))
        entries.append({
            "idx": idx,
            "date": date,
            "date_label": date.strftime(cfg["date_format"]),
            "html": render_inline(body),
            "attrs": Markup(attrs),
            "file": path.name,
        })
    entries.sort(key=lambda e: e["idx"], reverse=True)

    since = cfg["page"].get("since")
    if since:
        y, mo = (int(x) for x in since.split("-"))
        listed = [e for e in entries if e["date"] >= dt.date(y, mo, 1)]
    else:
        listed = entries
    return {"config": cfg, "all": entries, "listed": listed, "home": listed[: cfg["home"]["count"]]}


# ------------------------------------------------------------- publications

PAPER_KEYS = {"title", "authors", "venue", "links", "link_separator"}


def load_publications():
    cfg = load_config("publications")
    groups = []
    for key in cfg["groups"]["order"]:
        path = DATA / "publications" / ("%s.yaml" % key)
        if not path.exists():
            fail("publications: groups.order lists %r but %s is missing" % (key, path.name))
            continue
        papers = load_yaml(path) or []
        rendered = []
        for i, p in enumerate(papers, 1):
            where = "publications/%s.yaml paper #%d" % (key, i)
            for req in ("title", "authors", "venue"):
                if not p.get(req):
                    fail("%s: missing %s" % (where, req))
            unknown = set(p) - PAPER_KEYS
            if unknown:
                fail("%s: unknown field(s) %s" % (where, ", ".join(sorted(unknown))))
            sep = p.get("link_separator", cfg["links"]["separator"])
            links = Markup(sep).join(
                Markup('<a href="%s" target="_blank" rel="noopener">%s</a>') % (url, label)
                if external(url) else Markup('<a href="%s">%s</a>') % (url, label)
                for label, url in (p.get("links") or {}).items()
            )
            rendered.append({
                "title": p.get("title", ""),
                "authors": p.get("authors", ""),
                "venue": render_venue(p.get("venue", "")),
                "links": links,
            })
        groups.append({"key": key, "label": cfg["groups"]["labels"].get(key, key), "papers": rendered})
    listed = set(cfg["groups"]["order"])
    for path in (DATA / "publications").glob("*.yaml"):
        if path.stem not in listed:
            fail("publications/%s is not listed in config.toml groups.order, so it would not be shown" % path.name)
    return {"config": cfg, "groups": groups}


# ------------------------------------------------------------------ members

def load_members():
    cfg = load_config("members")
    raw = load_yaml(DATA / "members" / "members.yaml")
    photos = DATA / "members" / "photos"
    members = []
    for m in raw.get("members", []):
        for req in ("name", "photo", "position"):
            if not m.get(req):
                fail("members.yaml: %s is missing %s" % (m.get("name", m), req))
        if m.get("photo") and not (photos / m["photo"]).exists():
            fail("members.yaml: %s's photo %s is not in data/members/photos/" % (m.get("name"), m["photo"]))
        members.append(dict(m, alt=m.get("alt", m.get("name")), url=m.get("url")))
    alumni = [dict(a, url=a.get("url"), note=a.get("note", "")) for a in raw.get("alumni", [])]
    return {"config": cfg, "members": members, "alumni": alumni}


# ------------------------------------------------------------------ gallery

def load_gallery():
    cfg = load_config("gallery")
    photos_dir = DATA / "gallery" / "photos"
    photos, listed = [], set()
    for i, p in enumerate(load_yaml(DATA / "gallery" / "gallery.yaml") or [], 1):
        name = p.get("file")
        if not name or not p.get("caption"):
            fail("gallery.yaml entry #%d: needs file and caption" % i)
            continue
        if not (photos_dir / name).exists():
            fail("gallery.yaml: %s is not in data/gallery/photos/" % name)
        listed.add(name)
        photos.append({
            "file": name,
            "caption": p["caption"],
            "alt": p.get("alt", p["caption"]),
            "full": "stories/" + name,
            "thumb": "%s/%s" % (THUMBS, Path(name).with_suffix(".jpg").name),
        })
    for path in photos_dir.iterdir():
        if path.is_file() and path.name not in listed and not path.name.startswith("."):
            print("note: data/gallery/photos/%s is not in gallery.yaml (published, not shown)" % path.name)
    return {"config": cfg, "photos": photos, "preview": photos[: cfg["preview"]["count"]]}


# ----------------------------------------------------------------- research

def load_research():
    cfg = load_config("research")
    topics = []
    for t in load_yaml(DATA / "research" / "topics.yaml") or []:
        if not (DATA / "research" / "icons" / t["icon"]).exists():
            fail("research/topics.yaml: icon %s is not in data/research/icons/" % t["icon"])
        if t.get("hidden"):
            continue
        topics.append(dict(
            t,
            alt=t.get("alt", t["title"]),
            icon_class=t.get("icon_class", ""),
            summary=Markup(t["summary"]),
            details=[dict(d, papers=render_inline(d["papers"]) if d.get("papers") else None, text=d.get("text", ""))
                     for d in t.get("details", [])],
        ))
    return {"config": cfg, "topics": topics}


# ------------------------------------------------------------------- output

def thumbnail(src, dest, cfg):
    """Square center crop, same command the pre-commit hook used to run."""
    if dest.exists() and dest.stat().st_mtime >= src.stat().st_mtime:
        return
    tool = shutil.which("magick") or shutil.which("convert")
    if not tool:
        raise SystemExit("ImageMagick is required to make gallery thumbnails "
                         "(brew install imagemagick / apt install imagemagick)")
    size = cfg["size"]
    subprocess.run([
        tool, str(src), "-auto-orient",
        "-resize", "%dx%d^" % (size, size), "-gravity", "center", "-extent", "%dx%d" % (size, size),
        "-strip", "-interlace", "Plane", "-sampling-factor", "4:2:0",
        "-quality", str(cfg["quality"]), str(dest),
    ], check=True)


def copy_tree(src, dest):
    for path in src.rglob("*"):
        if path.is_file() and path.name != ".DS_Store":
            target = dest / path.relative_to(src)
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists() or target.stat().st_mtime < path.stat().st_mtime:
                shutil.copy2(path, target)


def build(check_only=False):
    with (DATA / "site.toml").open("rb") as f:
        site_cfg = tomllib.load(f)
    site = {
        "site": site_cfg,
        "news": load_news(),
        "publications": load_publications(),
        "members": load_members(),
        "gallery": load_gallery(),
        "research": load_research(),
    }
    if errors:
        print("Data errors:", file=sys.stderr)
        for e in errors:
            print("  - " + e, file=sys.stderr)
        return 1
    if check_only:
        print("data/ is valid.")
        return 0

    env = Environment(
        loader=FileSystemLoader(TEMPLATES),
        autoescape=True,
        undefined=StrictUndefined,
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    OUT.mkdir(exist_ok=True)
    for page in PAGES:
        html = env.get_template(page + ".html").render(page=page, **site)
        (OUT / (page + ".html")).write_text(html, encoding="utf-8")

    copy_tree(STATIC, OUT)
    for src, dest in PUBLISH.items():
        copy_tree(src, OUT / dest)
    thumbs = OUT / THUMBS
    thumbs.mkdir(parents=True, exist_ok=True)
    for p in site["gallery"]["photos"]:
        thumbnail(DATA / "gallery" / "photos" / p["file"], OUT / p["thumb"], site["gallery"]["config"]["thumbnail"])
    print("Built %d pages into %s" % (len(PAGES), OUT.relative_to(ROOT)))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true", help="validate data/ only")
    ap.add_argument("--serve", action="store_true", help="serve _site/ after building")
    ap.add_argument("--port", type=int, default=8000)
    args = ap.parse_args()
    status = build(check_only=args.check)
    if status or not args.serve:
        return status
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(OUT))
    print("Serving http://localhost:%d (Ctrl-C to stop)" % args.port)
    http.server.ThreadingHTTPServer(("", args.port), handler).serve_forever()


if __name__ == "__main__":
    sys.exit(main())
