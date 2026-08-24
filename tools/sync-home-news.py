#!/usr/bin/env python3
"""Rewrite the Recent News list on index.html from news.html.

news.html is the single source of truth for news. The home page shows only the
newest few items, and used to be edited by hand — which meant a link added on the
News page silently went missing on the home page. This keeps the two in step.

  tools/sync-home-news.py           update index.html in place
  tools/sync-home-news.py --check   report drift only, change nothing (exit 1)

Commented-out blocks further down the home page's news list are left untouched;
only the run of live items above them is regenerated.
"""

import os
import re
import sys

HOME = 'index.html'
ARCHIVE = 'news.html'
COUNT = 5

ITEM = re.compile(
    r'<div class="news-item">\s*'
    r'<span class="news-date">([^<]+)</span>\s*'
    r'<span class="news-content"\s*>(.*?)</span\s*>\s*'
    r'</div>',
    re.S,
)


def newest_items(archive_html):
    """The first COUNT news items in document order (news.html is newest-first)."""
    out = []
    for m in ITEM.finditer(archive_html):
        out.append((m.group(1).strip(), ' '.join(m.group(2).split())))
        if len(out) == COUNT:
            break
    return out


def render(items):
    blocks = []
    for date, content in items:
        blocks.append(
            '        <div class="news-item">\n'
            '          <span class="news-date">%s</span>\n'
            '          <span class="news-content">%s</span>\n'
            '        </div>' % (date, content)
        )
    return '\n\n'.join(blocks)


def news_list_span(home_html):
    """(start, end) of the .news-list element's inner content."""
    open_tag = '<div class="news-list">'
    i = home_html.index(open_tag) + len(open_tag)
    anchor = home_html.index('<p class="news-note">')
    j = home_html.rindex('</div>', i, anchor)
    return i, j


def rebuild(home_html, items):
    i, j = news_list_span(home_html)
    inner = home_html[i:j]

    # Keep everything from the first comment onward (disabled entries).
    cut = inner.find('<!--')
    tail = inner[cut:] if cut != -1 else ''

    new_inner = '\n\n' + render(items) + '\n\n'
    if tail:
        new_inner += '          ' + tail.lstrip()
    return home_html[:i] + new_inner + home_html[j:]


def main():
    check = '--check' in sys.argv[1:]
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(root)

    home = open(HOME, encoding='utf-8').read()
    archive = open(ARCHIVE, encoding='utf-8').read()

    items = newest_items(archive)
    if len(items) < COUNT:
        print('sync-home-news: only %d item(s) found in %s' % (len(items), ARCHIVE),
              file=sys.stderr)
        return 1

    updated = rebuild(home, items)
    if updated == home:
        print('Recent News on %s is in sync with %s.' % (HOME, ARCHIVE))
        return 0

    if check:
        print('Recent News on %s is out of sync with %s:' % (HOME, ARCHIVE))
        for date, content in items:
            text = re.sub(r'<[^>]+>', '', content)
            print('  %-9s %s' % (date, ' '.join(text.split())[:64]))
        print('Run tools/sync-home-news.py to update.')
        return 1

    open(HOME, 'w', encoding='utf-8').write(updated)
    print('Updated Recent News on %s (%d items from %s).' % (HOME, len(items), ARCHIVE))
    return 0


if __name__ == '__main__':
    sys.exit(main())
