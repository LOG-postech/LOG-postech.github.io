#!/usr/bin/env python3
"""Build the member and paper lists from the lab database in data/.

  data/members.bib   @member, @intern and @alumnus entries
  data/papers.bib    one entry per paper, in display order (newest first)

are the single source of truth. This script regenerates

  group.html         member grid, interns, alumni   (between <!-- db:... --> markers)
  publications.html  the full paper list            (between <!-- db:papers --> markers)
  data/db.json       members and papers for js/people.js (news faces)

  tools/build-db.py           rebuild in place
  tools/build-db.py --check   report stale files only, change nothing (exit 1)

Runs from the pre-commit hook and from .github/workflows/build-db.yml, so an
edit made in the GitHub web editor is rebuilt too. Standard library only.
"""

import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEMBERS_BIB = 'data/members.bib'
PAPERS_BIB = 'data/papers.bib'
DB_JSON = 'data/db.json'

# Papers from before the lab started are listed together under "Previous".
FIRST_LAB_YEAR = 2023
PREPRINT_TYPES = {'misc', 'unpublished'}

# Fields of a paper entry that are not links. Any other field holding a URL is
# shown as a link labelled with the field name (url is shown as "paper").
PAPER_META = {'title', 'author', 'year', 'venue', 'presentation', 'also', 'award',
              'equal', 'booktitle', 'journal', 'eprint', 'archiveprefix',
              'primaryclass', 'note', 'abstract', 'keywords', 'pages', 'volume',
              'number', 'publisher', 'doi', 'month', 'organization'}


# ---------------------------------------------------------------- BibTeX ----

class BibError(Exception):
    pass


def parse_bib(text, path):
    """[(type, key, {field: value}, line)] in file order. Field order is kept."""
    # Blank out % comment lines (keeping line numbers), so examples in them are
    # not read as entries.
    text = re.sub(r'(?m)^[ \t]*%.*$', '', text)
    entries = []
    i = 0
    n = len(text)
    while True:
        at = text.find('@', i)
        if at == -1:
            return entries
        m = re.compile(r'@\s*(\w+)\s*\{\s*([^,\s]+)\s*,').match(text, at)
        if not m:
            # A stray @ (e.g. in a comment line) – skip it.
            i = at + 1
            continue
        etype, key = m.group(1).lower(), m.group(2)
        line = text.count('\n', 0, at) + 1
        if etype in ('comment', 'preamble', 'string'):
            i = m.end()
            continue
        i = m.end()
        fields = {}
        while True:
            fm = re.compile(r'\s*([\w-]+)\s*=\s*').match(text, i)
            if not fm:
                end = re.compile(r'\s*,?\s*\}').match(text, i)
                if not end:
                    raise BibError('%s:%d: cannot parse entry %r near %r'
                                   % (path, line, key, text[i:i + 40]))
                i = end.end()
                break
            name = fm.group(1).lower()
            i = fm.end()
            if i < n and text[i] == '{':
                depth, j = 0, i
                while j < n:
                    if text[j] == '{':
                        depth += 1
                    elif text[j] == '}':
                        depth -= 1
                        if depth == 0:
                            break
                    j += 1
                if depth:
                    raise BibError('%s:%d: unbalanced braces in %r' % (path, line, key))
                value = text[i + 1:j]
                i = j + 1
            elif i < n and text[i] == '"':
                j = text.find('"', i + 1)
                value = text[i + 1:j]
                i = j + 1
            else:
                vm = re.compile(r'[^,}\s]+').match(text, i)
                value = vm.group(0)
                i = vm.end()
            if name in fields:
                raise BibError('%s:%d: field %r repeated in %r' % (path, line, name, key))
            fields[name] = clean(value)
            cm = re.compile(r'\s*,').match(text, i)
            if cm:
                i = cm.end()
        entries.append((etype, key, fields, line))


def clean(value):
    """Collapse whitespace and drop the braces BibTeX uses to protect case."""
    value = value.replace('{', '').replace('}', '').replace('\\&', '&')
    return ' '.join(value.split())


def split_list(value, sep):
    return [v.strip() for v in value.split(sep) if v.strip()] if value else []


def person_name(raw):
    """'Lee, Namhoon' or 'Namhoon Lee' -> 'Namhoon Lee'."""
    if ',' in raw:
        last, first = [p.strip() for p in raw.split(',', 1)]
        return '%s %s' % (first, last)
    return raw.strip()


def authors_of(fields):
    return [person_name(a) for a in re.split(r'\s+and\s+', fields.get('author', '')) if a.strip()]


# ------------------------------------------------------------------ data ----

def load_members(path):
    db = {'member': [], 'intern': [], 'alumnus': []}
    keys = set()
    for etype, key, f, line in parse_bib(read(path), path):
        if etype not in db:
            raise BibError('%s:%d: unknown entry type @%s (use @member, @intern or @alumnus)'
                           % (path, line, etype))
        if key in keys:
            raise BibError('%s:%d: duplicate key %r' % (path, line, key))
        keys.add(key)
        if 'name' not in f:
            raise BibError('%s:%d: @%s{%s} has no name' % (path, line, etype, key))
        if etype == 'member':
            for req in ('position', 'photo'):
                if req not in f:
                    raise BibError('%s:%d: @member{%s} has no %s' % (path, line, key, req))
            if not os.path.exists(f['photo']):
                raise BibError('%s:%d: @member{%s}: photo %s does not exist'
                               % (path, line, key, f['photo']))
        f = dict(f, key=key, aliases=split_list(f.get('aliases'), ';'))
        db[etype].append(f)
    return db


def load_papers(path):
    papers = []
    keys = set()
    for etype, key, f, line in parse_bib(read(path), path):
        if key in keys:
            raise BibError('%s:%d: duplicate key %r' % (path, line, key))
        keys.add(key)
        for req in ('title', 'author', 'venue', 'year'):
            if req not in f:
                raise BibError('%s:%d: @%s{%s} has no %s' % (path, line, etype, key, req))
        authors = authors_of(f)
        equal = set(person_name(a) for a in re.split(r'\s+and\s+', f.get('equal', '')) if a.strip())
        missing = equal - set(authors)
        if missing:
            raise BibError('%s:%d: equal names not among authors of %r: %s'
                           % (path, line, key, ', '.join(sorted(missing))))
        links = []
        for name, value in f.items():
            if name in PAPER_META or not re.match(r'https?://', value):
                continue
            links.append(('paper' if name == 'url' else name, value))
        if etype in PREPRINT_TYPES:
            section = 'Preprint'
        elif int(f['year']) >= FIRST_LAB_YEAR:
            section = f['year']
        else:
            section = 'Previous'
        papers.append({
            'key': key,
            'section': section,
            'title': f['title'],
            'authors': authors,
            'equal': equal,
            'venue': f['venue'],
            'presentation': f.get('presentation'),
            'also': split_list(f.get('also'), ';'),
            'awards': split_list(f.get('award'), ';'),
            'links': links,
        })
    return papers


# ----------------------------------------------------------------- render ----

def esc(s):
    return html.escape(s, quote=True)


def member_href(m):
    return m.get('url') or 'group.html#' + m['key']


def ext_attrs(href):
    return ' target="_blank" rel="noopener"' if re.match(r'https?://', href) else ''


def render_members(members):
    out = []
    for m in members['member']:
        name = esc(m['name'])
        label = ('<a href="%s">%s</a>' % (esc(m['url']), name)) if m.get('url') else '<span>%s</span>' % name
        out.append(
            '            <li class="member-item" id="%s">\n'
            '                <img src="%s" alt="%s">\n'
            '                %s\n'
            '                <span class="member-position">%s</span>\n'
            '            </li>\n' % (esc(m['key']), esc(m['photo']), name, label, esc(m['position'])))
    return '\n' + '\n'.join(out) + '\n'


def render_interns(members):
    items = []
    for m in members['intern']:
        aff = ' (%s)' % esc(m['affiliation']) if m.get('affiliation') else ''
        items.append('            <li>%s%s</li>\n' % (esc(m['name']), aff))
    return '\n' + ''.join(items) + '        '


def render_alumni(members):
    items = []
    for m in members['alumnus']:
        name = ('<a href="%s">%s</a>' % (esc(m['url']), esc(m['name']))) if m.get('url') else esc(m['name'])
        note = ' (%s)' % esc(m['note']) if m.get('note') else ''
        items.append('            <li>%s%s</li>\n' % (name, note))
    return '\n' + ''.join(items) + '        '


def name_index(members):
    index = {}
    for m in members['member']:
        for n in [m['name']] + m['aliases']:
            index[n.lower()] = m
    return index


def render_author(name, paper, index):
    label = esc(name) + ('*' if name in paper['equal'] else '')
    m = index.get(name.lower())
    if not m:
        return label
    href = member_href(m)
    return ('<a class="paper-member" href="%s"%s title="%s">'
            '<span class="member-face"><img src="%s" alt="" loading="lazy"></span>%s</a>'
            % (esc(href), ext_attrs(href), esc(m['name']), esc(m['photo']), label))


def render_venue(p):
    first = esc(p['venue'])
    if p['presentation']:
        first += ' <span class="spotlight">(%s)</span>' % esc(p['presentation'])
    parts = [first] + [esc(a) for a in p['also']]
    parts += ['<span class="spotlight">%s</span>' % esc(a) for a in p['awards']]
    return '; '.join(parts)


def render_papers(papers, members):
    index = name_index(members)
    out = []
    section = None
    for p in papers:
        if p['section'] != section:
            section = p['section']
            out.append('        <div class="year-divider">%s</div>\n' % section)
        lines = [
            '        <div class="paper">',
            '            <div class="paper-title">%s</div>' % esc(p['title']),
            '            <div class="paper-authors">%s</div>'
            % ', '.join(render_author(a, p, index) for a in p['authors']),
            '            <div class="paper-venue">%s</div>' % render_venue(p),
        ]
        if p['links']:
            lines.append('            <div class="paper-links">%s</div>' % ' '.join(
                '<a href="%s" target="_blank" rel="noopener">%s</a>' % (esc(url), esc(label))
                for label, url in p['links']))
        lines.append('        </div>\n')
        out.append('\n'.join(lines))
    return '\n' + '\n'.join(out) + '\n        '


def render_json(papers, members):
    data = {
        'members': [{'key': m['key'], 'name': m['name'], 'aliases': m['aliases'],
                     'photo': m['photo'], 'url': m.get('url')} for m in members['member']],
        'papers': [{'key': p['key'], 'title': p['title'], 'authors': p['authors'],
                    'links': [url for _, url in p['links']]} for p in papers],
    }
    return json.dumps(data, ensure_ascii=False, indent=1) + '\n'


# ------------------------------------------------------------------- io ----

GENERATED_NOTE = ('<!-- Generated from %s by tools/build-db.py. '
                  'Edit that file, not this list. -->')


def replace_block(page, name, content, source):
    """Replace what sits between <!-- db:name --> and <!-- /db:name -->."""
    m = re.search(r'(<!-- db:%s -->)(.*?)(<!-- /db:%s -->)' % (name, name), page, re.S)
    if not m:
        raise BibError('markers <!-- db:%s --> ... <!-- /db:%s --> not found' % (name, name))
    inner = '\n        ' + GENERATED_NOTE % source + content
    return page[:m.end(1)] + inner + page[m.start(3):]


def read(path):
    with open(path, encoding='utf-8') as f:
        return f.read()


def main():
    check = '--check' in sys.argv[1:]
    os.chdir(ROOT)
    try:
        members = load_members(MEMBERS_BIB)
        papers = load_papers(PAPERS_BIB)
        group = read('group.html')
        group = replace_block(group, 'members', render_members(members), MEMBERS_BIB)
        group = replace_block(group, 'interns', render_interns(members), MEMBERS_BIB)
        group = replace_block(group, 'alumni', render_alumni(members), MEMBERS_BIB)
        pubs = replace_block(read('publications.html'), 'papers',
                             render_papers(papers, members), PAPERS_BIB)
        outputs = {'group.html': group, 'publications.html': pubs,
                   DB_JSON: render_json(papers, members)}
    except BibError as e:
        print('build-db: %s' % e, file=sys.stderr)
        return 2

    stale = [p for p, text in outputs.items()
             if not os.path.exists(p) or read(p) != text]
    if not stale:
        print('build-db: pages are up to date with data/.')
        return 0
    if check:
        print('build-db: out of date: %s. Run tools/build-db.py.' % ', '.join(stale))
        return 1
    for p in stale:
        with open(p, 'w', encoding='utf-8') as f:
            f.write(outputs[p])
    print('build-db: rebuilt %s.' % ', '.join(stale))
    return 0


if __name__ == '__main__':
    sys.exit(main())
