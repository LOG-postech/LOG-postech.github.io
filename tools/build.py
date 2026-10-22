#!/usr/bin/env python3
"""Build the site: read data/, render pages/, write _site/.

  tools/build.py            build into _site/
  tools/build.py --check    validate data/ only, write nothing (exit 1 on errors)
  tools/build.py --serve    build, then serve _site/ on http://localhost:8000

Content lives in data/<database>/ — one directory per kind of content, each with
its entries, a config.toml for presentation settings, and a README.md on how to
add an entry. Pages are Jinja templates in pages/. Files in static/ are
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
PAGES_DIR = ROOT / "pages"
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


class _UniqueKeyLoader(yaml.SafeLoader):
    """yaml.safe_load, except a key given twice in one mapping is an error
    (plain YAML silently keeps the last one, which would drop an entry)."""

    def construct_mapping(self, node, deep=False):
        seen = set()
        for key_node, _ in node.value:
            key = self.construct_object(key_node, deep=deep)
            if key in seen:
                raise DataError("line %d: %r is given twice" % (key_node.start_mark.line + 1, key))
            seen.add(key)
        return super().construct_mapping(node, deep=deep)


def load_yaml(path):
    with path.open(encoding="utf-8") as f:
        return yaml.load(f, Loader=_UniqueKeyLoader)


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


# ------------------------------------------------------------------- people

TAG = re.compile(r"(?<![\w.])@([a-z0-9_]+)")


class People:
    """@tag -> person, from data/members/members.yaml (members, then alumni).

    A person can be in both lists (an MS graduate continuing as a PhD student)
    under one tag; the current-member entry wins. Only current members have a
    face: alumni tags show the name alone.
    """

    def __init__(self, raw):
        self.by_tag = {}
        for group, current in (("members", True), ("alumni", False)):
            for p in raw.get(group, []) or []:
                tag = p.get("tag", "")
                if not re.fullmatch(r"[a-z0-9_]+", tag or ""):
                    fail("members.yaml: %s needs a tag of lowercase letters/digits (e.g. hyunjijung)" % p.get("name", p))
                    continue
                if tag in self.by_tag:
                    other = self.by_tag[tag]
                    if not (other["current"] and not current and other["name"] == p.get("name")):
                        fail("members.yaml: tag @%s is used for both %s and %s" % (tag, other["name"], p.get("name")))
                    continue
                name = p.get("name", "")
                self.by_tag[tag] = {
                    "tag": tag,
                    "name": name,
                    "short": p.get("short") or name.split(" ")[0],
                    "url": p.get("url"),
                    "photo": "group_profile/" + p["photo"] if current and p.get("photo") else None,
                    "slug": Path(p.get("photo", "")).stem,
                    "current": current,
                }

    def get(self, tag, where):
        person = self.by_tag.get(tag)
        if person is None:
            fail("%s: @%s is not a tag in members/members.yaml" % (where, tag))
        return person

    def resolve(self, text, where, form):
        """Replace each @tag with the person's name; return (text, people in order)."""
        found = []

        def sub(m):
            person = self.get(m.group(1), where)
            if person is None:
                return m.group(0)
            if person not in found:
                found.append(person)
            return person[form]

        return TAG.sub(sub, text), found


def _profile_link(person):
    """Where a face links: the member's own site, else their card on group.html."""
    if person["url"] and external(person["url"]):
        return Markup(' href="%s" target="_blank" rel="noopener"') % person["url"]
    if person["url"]:
        return Markup(' href="%s"') % person["url"]
    return Markup(' href="group.html#%s"') % person["slug"]


def _face_img(person):
    return Markup('<img src="%s" alt="" loading="lazy" decoding="async">') % person["photo"]


def news_faces(people, max_faces):
    """Faces under a news item's date: a few, then "+N" (like Slack)."""
    people = [p for p in people if p["current"]]
    if not people:
        return Markup("")
    names = ", ".join(p["name"] for p in people)
    shown = people[: max_faces - 1] if len(people) > max_faces else people
    html = Markup('<span class="news-people" aria-label="%s" title="%s">') % (names, names)
    for p in shown:
        html += Markup('<a class="member-face" title="%s"%s>%s</a>') % (p["name"], _profile_link(p), _face_img(p))
    if len(shown) < len(people):
        html += Markup('<span class="member-face member-face-more">+%d</span>') % (len(people) - len(shown))
    return html + Markup("</span>")


def author_list(field, people, where):
    """BibTeX author field -> (HTML author list, current members in order).

    "@hyunjijung* and Ziyang Wu" -> a face and name for the member (marks such
    as * kept), plain text for everyone else.
    """
    out, members = [], []
    for raw in re.split(r"\s+and\s+", field.strip()):
        raw = raw.strip()
        m = re.fullmatch(r"@([a-z0-9_]+)([*†‡]*)", raw)
        person = people.get(m.group(1), where) if m else None
        if person is None:
            out.append(escape(raw))
            continue
        label = person["name"] + m.group(2)
        if not person["current"]:
            out.append(escape(label))
            continue
        members.append(person)
        out.append(Markup('<a class="paper-member" title="%s"%s><span class="member-face">%s</span>%s</a>')
                   % (person["name"], _profile_link(person), _face_img(person), label))
    return Markup(", ").join(out), members


# --------------------------------------------------------------------- news

NEWS_KEYS = {"date", "paper", "text"}
NEWS_DATE = re.compile(r"^(\d{4})-(\d{2})(?:-(\d{2}))?$")
# A Markdown link to a paper by its papers.bib key: [paper](@shin23closer).
PAPER_LINK = re.compile(r"\]\(@([a-z][a-z0-9_]*)\)")
# A link target that is a bare word is a key missing its @.
BARE_LINK = re.compile(r"\]\(([a-z][a-z0-9_]*)\)")


def load_news(papers_by_key, people):
    """News items from data/news/<year>.yaml, ordered by idx (higher = newer)."""
    cfg = load_config("news")
    entries, seen = [], {}
    for path in sorted((DATA / "news").glob("*.yaml")):
        if not re.fullmatch(r"\d{4}", path.stem):
            fail("news/%s: news files are named by year, like 2026.yaml" % path.name)
            continue
        try:
            items = load_yaml(path) or {}
        except DataError as e:
            fail("news/%s %s" % (path.name, e))
            continue
        if not isinstance(items, dict):
            fail("news/%s: items are keyed by idx (39:, 38:, ...)" % path.name)
            continue
        for idx, item in items.items():
            if not isinstance(idx, int):
                fail("news/%s: %r is not an idx; each item starts with its number, like 39:" % (path.name, idx))
                continue
            where = "news/%s idx %d" % (path.name, idx)
            if not isinstance(item, dict):
                fail("%s: needs date and text" % where)
                continue
            unknown = set(item) - NEWS_KEYS
            if unknown:
                fail("%s: unknown field(s) %s (allowed: %s)" % (where, ", ".join(sorted(unknown)), ", ".join(sorted(NEWS_KEYS))))
            if idx in seen:
                fail("%s: idx %d is already used in %s" % (where, idx, seen[idx]))
            seen[idx] = path.name
            raw_date = item.get("date")
            m = NEWS_DATE.match(str(raw_date or ""))
            if not m:
                fail('%s: date must be "YYYY-MM" or "YYYY-MM-DD", not %r' % (where, raw_date))
                continue
            try:
                date = dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3) or 1))
            except ValueError:
                fail("%s: %r is not a real date" % (where, raw_date))
                continue
            if m.group(1) != path.stem:
                fail("%s: dated %s but filed in %s" % (where, raw_date, path.name))
            body = " ".join(str(item.get("text") or "").split())
            if not body:
                fail("%s: text is empty" % where)
                continue
            front = item
            # Papers: named in front matter (paper: key), or linked in the text as
            # [paper](key), which links to the paper's own `paper` URL.
            keys = []
            listed = front.get("paper") or []
            for k in [listed] if isinstance(listed, str) else listed:
                if not str(k).startswith("@"):
                    fail('%s: paper keys start with @, in quotes: paper: "@%s"' % (where, k))
                keys.append(str(k).lstrip("@"))
            for m in BARE_LINK.finditer(body):
                fail("%s: link target %r: write a paper key as (@%s)" % (where, m.group(1), m.group(1)))

            def link_paper(m):
                key = m.group(1)
                paper = papers_by_key.get(key)
                if paper is None:
                    fail("%s: link target %r is not a key in publications/papers.bib" % (where, key))
                    return m.group(0)
                if not paper["url"]:
                    fail("%s: %s has no `paper` link in papers.bib to link to" % (where, key))
                    return m.group(0)
                if key not in keys:
                    keys.append(key)
                return "](%s)" % paper["url"]

            body = PAPER_LINK.sub(link_paper, body)

            # Faces: the in-lab authors of those papers, then the members @tagged in
            # the text, in that order.
            faces = []
            for key in keys:
                paper = papers_by_key.get(str(key))
                if paper is None:
                    fail("%s: paper %r is not a key in publications/papers.bib" % (where, key))
                    continue
                faces += [p for p in paper["members"] if p not in faces]
            body, tagged = people.resolve(body, where, "short")
            faces += [p for p in tagged if p not in faces]
            entries.append({
                "idx": idx,
                "date": date,
                "date_label": date.strftime(cfg["date_format"]),
                "html": render_inline(body),
                "faces": news_faces(faces, cfg["faces"]["max"]),
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

BIB_ENTRY = re.compile(r"@(\w+)\s*\{\s*([^,\s]+)\s*,")
BIB_FIELD = re.compile(r"\s*([A-Za-z][\w-]*)\s*=\s*")


def parse_bibtex(text, where):
    """Entries of a .bib file, in file order: [(key, {field: value})].

    Covers what papers.bib uses: @type{key, field = {value} or "value" or 2026}.
    Field order and name case are kept (link fields are shown in that order, with
    that label). Braces only protect capitalisation in BibTeX, so they are
    dropped; \\& is &. Anything outside an entry is a comment, and so is a
    line starting with % inside one.
    """
    entries, pos = [], 0
    text = re.sub(r"(?m)^[ \t]*%.*$", "", text)
    while True:
        m = BIB_ENTRY.search(text, pos)
        if not m:
            return entries
        key, fields, pos = m.group(2), {}, m.end()
        if m.group(1).lower() in ("comment", "string", "preamble"):
            continue
        while True:
            close = re.match(r"\s*\}", text[pos:])
            if close:
                pos += close.end()
                break
            f = BIB_FIELD.match(text, pos)
            if not f:
                raise DataError("%s: entry %s: cannot read field near %r" % (where, key, text[pos:pos + 40]))
            name, pos = f.group(1), f.end()
            if text[pos] in "{\"":
                opener, depth, start = text[pos], 0, pos
                while True:
                    c = text[pos]
                    if opener == '"' and c == '"' and pos > start:
                        break
                    if c == "{":
                        depth += 1
                    elif c == "}":
                        depth -= 1
                        if depth == 0 and opener == "{":
                            break
                    pos += 1
                    if pos >= len(text):
                        raise DataError("%s: entry %s: unclosed value of %s" % (where, key, name))
                value, pos = text[start + 1:pos], pos + 1
            else:
                v = re.match(r"[^,}\s]+", text[pos:])
                value, pos = v.group(0), pos + v.end()
            if name.lower() in (n.lower() for n in fields):
                raise DataError("%s: entry %s: %s is given twice" % (where, key, name))
            fields[name] = " ".join(value.replace("{", "").replace("}", "").replace("\\&", "&").split())
            comma = re.match(r"\s*,", text[pos:])
            if comma:
                pos += comma.end()
        entries.append((key, fields))


# Fields of a papers.bib entry. Any other field is a link: its name is the label
# shown on the page ([paper], [code], ...), its value the URL.
PAPER_TEXT = {"title", "author", "venue", "year", "also", "award"}
PAPER_FLAGS = {"is_preprint", "is_previous", "oral", "spotlight", "spaced_links"}


def flag(value, where, name):
    v = value.strip().lower()
    if v in ("true", "yes", "1"):
        return True
    if v in ("false", "no", "0", ""):
        return False
    fail("%s: %s must be true or false, not %r" % (where, name, value))
    return False


def venue_line(p):
    """venue (Oral); also; award  — the award highlighted, as on the page."""
    line = str(escape(p["venue"]))
    if p["oral"] or p["spotlight"]:
        line += ' <span class="spotlight">(%s)</span>' % ("Oral" if p["oral"] else "Spotlight")
    if p.get("also"):
        line += "; " + str(escape(p["also"]))
    if p.get("award"):
        line += '; <span class="spotlight">%s</span>' % escape(p["award"])
    return Markup(line)


def load_publications(people):
    cfg = load_config("publications")
    where = "publications/papers.bib"
    try:
        entries = parse_bibtex((DATA / "publications" / "papers.bib").read_text(encoding="utf-8"), where)
    except DataError as e:
        fail(str(e))
        entries = []

    papers, keys = [], set()
    for key, f in entries:
        here = "%s: %s" % (where, key)
        if key in keys:
            fail("%s: the key %s is used twice" % (where, key))
        keys.add(key)
        lower = {k.lower(): v for k, v in f.items()}
        for req in ("title", "author", "venue", "year"):
            if not lower.get(req):
                fail("%s: missing %s" % (here, req))
        if lower.get("year") and not re.fullmatch(r"\d{4}", lower["year"]):
            fail("%s: year must be four digits, not %r" % (here, lower["year"]))
        p = {k: lower.get(k, "") for k in PAPER_TEXT}
        for k in PAPER_FLAGS:
            p[k] = flag(lower.get(k, ""), here, k)
        if p["is_preprint"] and p["is_previous"]:
            fail("%s: is_preprint and is_previous cannot both be true" % here)
        if p["oral"] and p["spotlight"]:
            fail("%s: oral and spotlight cannot both be true" % here)
        links = []
        for name, url in f.items():
            if name.lower() in PAPER_TEXT | PAPER_FLAGS:
                continue
            if not re.match(r"(https?://|[\w./-]+$)", url):
                fail("%s: %s is not a known field, so it is read as a link, but %r is not a URL" % (here, name, url))
            links.append((name, url))
        sep = " " if p["spaced_links"] else cfg["links"]["separator"]
        authors, members = author_list(p["author"], people, here)
        papers.append({
            "title": p["title"],
            "authors": authors,
            "members": members,
            "url": next((u for n, u in links if n.lower() == "paper"), None),
            "venue": venue_line(p),
            "links": Markup(sep).join(
                Markup('<a href="%s" target="_blank" rel="noopener">%s</a>') % (url, label)
                if external(url) else Markup('<a href="%s">%s</a>') % (url, label)
                for label, url in links
            ),
            "key": key,
            "group": "preprint" if p["is_preprint"] else "previous" if p["is_previous"] else p["year"],
        })

    # Preprints first, then years newest first, then earlier work. Within a group,
    # papers keep their order in the file.
    years = sorted({p["group"] for p in papers if p["group"] not in ("preprint", "previous")}, reverse=True)
    order = ["preprint"] + years + ["previous"]
    labels = cfg["groups"]
    groups = [
        {"key": g, "label": labels.get(g, g), "papers": [p for p in papers if p["group"] == g]}
        for g in order
    ]
    return {"config": cfg, "groups": [g for g in groups if g["papers"]], "by_key": {p["key"]: p for p in papers}}


# ------------------------------------------------------------------ members

def load_members():
    cfg = load_config("members")
    try:
        data = load_yaml(DATA / "members" / "members.yaml") or {}
    except DataError as e:
        fail("members.yaml %s" % e)
        data = {}
    # Each section maps tag -> person, in display order; flatten to lists.
    raw = {}
    for group in ("members", "alumni"):
        section = data.get(group) or {}
        if not isinstance(section, dict):
            fail("members.yaml: %s is keyed by tag (hyunjijung:, ...)" % group)
            section = {}
        raw[group] = []
        for tag, person in section.items():
            if not isinstance(person, dict):
                fail("members.yaml: %s: %s needs name and the other fields below it" % (group, tag))
                continue
            if "tag" in person:
                fail("members.yaml: %s: the tag is the key, so remove the tag field" % tag)
            raw[group].append(dict(person, tag=str(tag)))
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
    return {"config": cfg, "members": members, "alumni": alumni, "people": People(raw)}


# ------------------------------------------------------------------ gallery

def load_gallery():
    cfg = load_config("gallery")
    photos_dir = DATA / "gallery" / "photos"
    photos, listed = [], set()
    try:
        items = load_yaml(DATA / "gallery" / "gallery.yaml") or {}
    except DataError as e:
        fail("gallery.yaml %s" % e)
        items = {}
    if not isinstance(items, dict):
        fail("gallery.yaml: photos are keyed by idx (46:, 45:, ...)")
        items = {}
    # Highest idx first: newest photos lead the grid and the Members preview.
    for k in items:
        if not isinstance(k, int):
            fail("gallery.yaml: %r is not an idx; each photo starts with its number, like 46:" % (k,))
    for i in sorted((k for k in items if isinstance(k, int)), reverse=True):
        p = items[i]
        if not isinstance(p, dict) or not p.get("file") or not p.get("caption"):
            fail("gallery.yaml %d: needs file and caption" % i)
            continue
        unknown = set(p) - {"file", "caption", "alt"}
        if unknown:
            fail("gallery.yaml %d: unknown field(s) %s (allowed: alt, caption, file)" % (i, ", ".join(sorted(unknown))))
        name = p["file"]
        if name in listed:
            fail("gallery.yaml %d: %s is already listed under another number" % (i, name))
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
    members = load_members()
    publications = load_publications(members["people"])
    site = {
        "site": site_cfg,
        "news": load_news(publications["by_key"], members["people"]),
        "publications": publications,
        "members": members,
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
        loader=FileSystemLoader(PAGES_DIR),
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
