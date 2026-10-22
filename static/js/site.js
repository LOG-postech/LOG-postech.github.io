/* Renders the data/ databases into the page, in the browser.

   GitHub Pages builds this site with plain Jekyll, which cannot read BibTeX or
   TOML or resolve @tags, so that work happens here. layout/partials/data.html
   embeds the data in the page as window.LOG; this script turns it into the
   news, papers, members and gallery lists. The page's own script
   (layout/scripts/<page>.js) runs after it and finds the lists in place.

   The rules are the ones documented in data/<db>/README.md. Data errors are
   reported in the browser console; tools/build.py --check reports them before
   a commit. */
(function () {
    "use strict";
    if (!window.LOG) return;

    var errors = [];
    function fail(msg) { errors.push(msg); }

    // ---------------------------------------------------------------- helpers

    function esc(s) {
        return String(s == null ? "" : s)
            .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
    }

    function external(url) { return /^https?:\/\//.test(url || ""); }

    function collapse(text) { return String(text || "").split(/\s+/).filter(Boolean).join(" "); }

    /* The part of TOML the config.toml files use: [section] / [a.b] headers and
       key = "string" | number | true | false, with # comments. */
    function parseToml(text, where) {
        var root = {}, cur = root;
        String(text || "").split("\n").forEach(function (raw) {
            var line = stripTomlComment(raw).trim();
            if (!line) return;
            var section = line.match(/^\[([A-Za-z0-9_.-]+)\]$/);
            if (section) {
                cur = root;
                section[1].split(".").forEach(function (k) { cur = cur[k] = cur[k] || {}; });
                return;
            }
            var kv = line.match(/^([A-Za-z0-9_-]+)\s*=\s*(.+)$/);
            if (!kv) { fail(where + ": cannot read " + JSON.stringify(raw)); return; }
            var v = kv[2].trim();
            if (/^".*"$/.test(v)) v = JSON.parse(v);
            else if (v === "true" || v === "false") v = v === "true";
            else if (/^[+-]?\d+(\.\d+)?$/.test(v)) v = Number(v);
            cur[kv[1]] = v;
        });
        return root;
    }

    function stripTomlComment(line) {
        var inString = false;
        for (var i = 0; i < line.length; i++) {
            if (line[i] === '"' && line[i - 1] !== "\\") inString = !inString;
            else if (line[i] === "#" && !inString) return line.slice(0, i);
        }
        return line;
    }

    /* One paragraph of Markdown -> inline HTML: [text](url), **strong**, *em*,
       and \-escapes. External links open in a new tab, as everywhere on the site. */
    function renderInline(text) {
        var kept = [];
        var s = String(text).trim().replace(/\\([\\`*_\[\]<>{}()#+\-.!])/g, function (_, c) {
            kept.push(c);
            return "\u0000" + (kept.length - 1) + "\u0000";
        });
        s = esc(s)
            .replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, '<a href="$2">$1</a>')
            .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
            .replace(/\*([^*\s][^*]*)\*/g, "<em>$1</em>")
            .replace(/\u0000(\d+)\u0000/g, function (_, i) { return esc(kept[+i]); });
        return s.replace(/<a href="(https?:\/\/[^"]+)">/g, '<a href="$1" target="_blank" rel="noopener">');
    }

    var MONTHS = ["January", "February", "March", "April", "May", "June", "July",
                  "August", "September", "October", "November", "December"];

    function strftime(fmt, y, m, d) {
        var pad = function (n) { return (n < 10 ? "0" : "") + n; };
        return fmt.replace(/%([bBYymd%])/g, function (_, c) {
            return { b: MONTHS[m - 1].slice(0, 3), B: MONTHS[m - 1], Y: String(y),
                     y: pad(y % 100), m: pad(m), d: pad(d), "%": "%" }[c];
        });
    }

    var config = {};
    Object.keys(LOG.toml).forEach(function (db) {
        config[db] = parseToml(LOG.toml[db], "data/" + db + "/config.toml");
    });

    // ----------------------------------------------------------------- people

    /* @tag -> person, from data/members/members.yaml (members, then alumni).
       Someone in both lists under one tag (MS -> PhD) is the current member.
       Only current members have a face; alumni tags show the name alone. */
    var people = {};
    (function () {
        // Jekyll nests data as folder -> file: data/members/members.yaml is LOG.data.members.members.
        var raw = (LOG.data.members || {}).members || {};
        [["members", true], ["alumni", false]].forEach(function (g) {
            var section = raw[g[0]] || {};
            Object.keys(section).forEach(function (tag) {
                var p = section[tag] || {};
                if (people[tag]) {
                    var other = people[tag];
                    if (!(other.current && !g[1] && other.name === p.name)) {
                        fail("members.yaml: tag @" + tag + " is used for both " + other.name + " and " + p.name);
                    }
                    return;
                }
                var name = p.name || "";
                people[tag] = {
                    tag: tag,
                    name: name,
                    short: p.short || name.split(" ")[0],
                    url: p.url || null,
                    photo: g[1] && p.photo ? "data/members/photos/" + p.photo : null,
                    slug: String(p.photo || "").replace(/\.[^.]*$/, ""),
                    current: g[1],
                    position: p.position || "",
                    alt: p.alt || name,
                    file: p.photo,
                    note: p.note || ""
                };
            });
        });
    })();

    function person(tag, where) {
        var p = people[tag];
        if (!p) fail(where + ": @" + tag + " is not a tag in members/members.yaml");
        return p || null;
    }

    /* Replace each @tag with the person's name; return [text, people in order]. */
    function resolveTags(text, where, form) {
        var found = [];
        var out = text.replace(/(^|[^\w.])@([a-z0-9_]+)/g, function (all, before, tag) {
            var p = person(tag, where);
            if (!p) return all;
            if (found.indexOf(p) === -1) found.push(p);
            return before + p[form];
        });
        return [out, found];
    }

    function profileLink(p) {
        if (p.url && external(p.url)) return ' href="' + esc(p.url) + '" target="_blank" rel="noopener"';
        if (p.url) return ' href="' + esc(p.url) + '"';
        return ' href="group.html#' + esc(p.slug) + '"';
    }

    function faceImg(p) {
        return '<img src="' + esc(p.photo) + '" alt="" loading="lazy" decoding="async">';
    }

    /* Faces under a news item's date: a few, then "+N" (like Slack). */
    function newsFaces(list, max) {
        list = list.filter(function (p) { return p.current; });
        if (!list.length) return "";
        var names = esc(list.map(function (p) { return p.name; }).join(", "));
        var shown = list.length > max ? list.slice(0, max - 1) : list;
        var html = '<span class="news-people" aria-label="' + names + '" title="' + names + '">';
        shown.forEach(function (p) {
            html += '<a class="member-face" title="' + esc(p.name) + '"' + profileLink(p) + ">" + faceImg(p) + "</a>";
        });
        if (shown.length < list.length) {
            html += '<span class="member-face member-face-more">+' + (list.length - shown.length) + "</span>";
        }
        return html + "</span>";
    }

    /* BibTeX author field -> [HTML author list, current members in order].
       "@hyunjijung* and Ziyang Wu": face and name for the member (marks such as
       * kept), plain text for everyone else. */
    function authorList(field, where) {
        var out = [], members = [];
        field.trim().split(/\s+and\s+/).forEach(function (raw) {
            raw = raw.trim();
            var m = raw.match(/^@([a-z0-9_]+)([*†‡]*)$/);
            var p = m ? person(m[1], where) : null;
            if (!p) { out.push(esc(raw)); return; }
            var label = p.name + m[2];
            if (!p.current) { out.push(esc(label)); return; }
            members.push(p);
            out.push('<a class="paper-member" title="' + esc(p.name) + '"' + profileLink(p) +
                     '><span class="member-face">' + faceImg(p) + "</span>" + esc(label) + "</a>");
        });
        return [out.join(", "), members];
    }

    // ----------------------------------------------------------- publications

    /* Entries of papers.bib, in file order: [[key, [[field, value], ...]], ...].
       Covers @type{key, field = {value} or "value" or 2026}. Braces only protect
       capitalisation in BibTeX, so they are dropped; \& is &. Anything outside
       an entry is a comment, and so is a line starting with %. */
    function parseBib(text) {
        var entries = [], pos = 0, m;
        var entry = /@(\w+)\s*\{\s*([^,\s]+)\s*,/g;
        text = String(text || "").replace(/^[ \t]*%.*$/gm, "");
        while (true) {
            entry.lastIndex = pos;
            m = entry.exec(text);
            if (!m) return entries;
            var key = m[2], fields = [], p = entry.lastIndex;
            if (/^(comment|string|preamble)$/i.test(m[1])) { pos = p; continue; }
            while (true) {
                var rest = text.slice(p);
                var close = /^\s*\}/.exec(rest);
                if (close) { p += close[0].length; break; }
                var f = /^\s*([A-Za-z][\w-]*)\s*=\s*/.exec(rest);
                if (!f) { fail("papers.bib: entry " + key + ": cannot read a field"); return entries; }
                var name = f[1], value;
                p += f[0].length;
                if (text[p] === "{" || text[p] === '"') {
                    var opener = text[p], depth = 0, start = p;
                    while (true) {
                        var c = text[p];
                        if (opener === '"' && c === '"' && p > start) break;
                        if (c === "{") depth++;
                        else if (c === "}") { depth--; if (depth === 0 && opener === "{") break; }
                        p++;
                        if (p >= text.length) { fail("papers.bib: entry " + key + ": unclosed " + name); return entries; }
                    }
                    value = text.slice(start + 1, p);
                    p++;
                } else {
                    var bare = /^[^,}\s]+/.exec(text.slice(p));
                    value = bare ? bare[0] : "";
                    p += value.length;
                }
                fields.push([name, collapse(value.replace(/[{}]/g, "").replace(/\\&/g, "&"))]);
                var comma = /^\s*,/.exec(text.slice(p));
                if (comma) p += comma[0].length;
            }
            entries.push([key, fields]);
            pos = p;
        }
    }

    var PAPER_TEXT = ["title", "author", "venue", "year", "also", "award"];
    var PAPER_FLAGS = ["is_preprint", "is_previous", "oral", "spotlight", "spaced_links"];

    function flag(v) { return /^(true|yes|1)$/i.test(String(v || "").trim()); }

    /* venue (Oral); also; award — the award highlighted. */
    function venueLine(p) {
        var line = esc(p.venue);
        if (p.oral || p.spotlight) line += ' <span class="spotlight">(' + (p.oral ? "Oral" : "Spotlight") + ")</span>";
        if (p.also) line += "; " + esc(p.also);
        if (p.award) line += '; <span class="spotlight">' + esc(p.award) + "</span>";
        return line;
    }

    var papers = [], papersByKey = {};
    parseBib(LOG.bib).forEach(function (e) {
        var key = e[0], where = "papers.bib: " + key, lower = {}, links = [];
        e[1].forEach(function (f) {
            var n = f[0].toLowerCase();
            if (PAPER_TEXT.indexOf(n) !== -1 || PAPER_FLAGS.indexOf(n) !== -1) lower[n] = f[1];
            else links.push(f);
        });
        ["title", "author", "venue", "year"].forEach(function (r) { if (!lower[r]) fail(where + ": missing " + r); });
        var p = {};
        PAPER_TEXT.forEach(function (k) { p[k] = lower[k] || ""; });
        PAPER_FLAGS.forEach(function (k) { p[k] = flag(lower[k]); });
        var authors = authorList(p.author, where);
        var sep = p.spaced_links ? " " : config.publications.links.separator;
        var paper = {
            key: key,
            title: p.title,
            authors: authors[0],
            members: authors[1],
            venue: venueLine(p),
            links: links.map(function (l) {
                return external(l[1])
                    ? '<a href="' + esc(l[1]) + '" target="_blank" rel="noopener">' + esc(l[0]) + "</a>"
                    : '<a href="' + esc(l[1]) + '">' + esc(l[0]) + "</a>";
            }).join(sep),
            url: (links.filter(function (l) { return l[0].toLowerCase() === "paper"; })[0] || [])[1] || null,
            group: p.is_preprint ? "preprint" : p.is_previous ? "previous" : p.year
        };
        if (papersByKey[key]) fail("papers.bib: the key " + key + " is used twice");
        papersByKey[key] = paper;
        papers.push(paper);
    });

    function publicationGroups() {
        var years = [];
        papers.forEach(function (p) {
            if (p.group !== "preprint" && p.group !== "previous" && years.indexOf(p.group) === -1) years.push(p.group);
        });
        years.sort().reverse();
        return ["preprint"].concat(years, ["previous"]).map(function (g) {
            return {
                label: config.publications.groups[g] || g,
                papers: papers.filter(function (p) { return p.group === g; })
            };
        }).filter(function (g) { return g.papers.length; });
    }

    // ------------------------------------------------------------------- news

    /* Items from data/news/<year>.yaml, ordered by idx (higher = newer). */
    function loadNews() {
        var cfg = config.news, entries = [];
        var files = LOG.data.news || {};
        Object.keys(files).filter(function (y) { return /^\d{4}$/.test(y); }).forEach(function (year) {
            var items = files[year] || {};
            Object.keys(items).forEach(function (k) {
                var item = items[k] || {}, idx = Number(k), where = "news/" + year + ".yaml idx " + k;
                var m = /^(\d{4})-(\d{2})(?:-(\d{2}))?$/.exec(String(item.date || ""));
                if (!m) { fail(where + ": bad date " + item.date); return; }
                var keys = [];
                var listed = item.paper ? (Array.isArray(item.paper) ? item.paper : [item.paper]) : [];
                listed.forEach(function (key) {
                    key = String(key);
                    if (key.charAt(0) !== "@") fail(where + ': paper keys start with @: "@' + key + '"');
                    keys.push(key.replace(/^@/, ""));
                });
                // [text](@key) links to the paper's own `paper` URL.
                var body = collapse(item.text).replace(/\]\(@([a-z][a-z0-9_]*)\)/g, function (all, key) {
                    var paper = papersByKey[key];
                    if (!paper) { fail(where + ": " + key + " is not a key in papers.bib"); return all; }
                    if (!paper.url) { fail(where + ": " + key + " has no `paper` link"); return all; }
                    if (keys.indexOf(key) === -1) keys.push(key);
                    return "](" + paper.url + ")";
                });
                // Faces: the in-lab authors of those papers, then members @tagged.
                var faces = [];
                keys.forEach(function (key) {
                    var paper = papersByKey[key];
                    if (!paper) { fail(where + ": paper " + key + " is not a key in papers.bib"); return; }
                    paper.members.forEach(function (p) { if (faces.indexOf(p) === -1) faces.push(p); });
                });
                var resolved = resolveTags(body, where, "short");
                resolved[1].forEach(function (p) { if (faces.indexOf(p) === -1) faces.push(p); });
                var y = +m[1], mo = +m[2], d = +(m[3] || 1);
                entries.push({
                    idx: idx,
                    sortDate: y * 10000 + mo * 100 + d,
                    label: strftime(cfg.date_format, y, mo, d),
                    html: renderInline(resolved[0]),
                    faces: newsFaces(faces, cfg.faces.max)
                });
            });
        });
        entries.sort(function (a, b) { return b.idx - a.idx; });
        var since = cfg.page.since;
        if (since) {
            var s = since.split("-");
            var from = (+s[0]) * 10000 + (+s[1]) * 100 + 1;
            entries = entries.filter(function (e) { return e.sortDate >= from; });
        }
        return entries;
    }

    function newsItems(entries, indent) {
        return entries.map(function (n) {
            return indent + '<div class="news-item">\n' +
                indent + '    <span class="news-date">' + n.label + n.faces + "</span>\n" +
                indent + '    <span class="news-content">' + n.html + "</span>\n" +
                indent + "</div>\n";
        }).join("\n");
    }

    // ---------------------------------------------------------------- gallery

    /* Highest idx first: newest photos lead the grid and the Members preview. */
    var galleryPhotos = (function () {
        var items = (LOG.data.gallery || {}).gallery || {};
        return Object.keys(items).map(Number).sort(function (a, b) { return b - a; }).map(function (i) {
            var p = items[i] || {};
            if (!p.file || !p.caption) fail("gallery.yaml " + i + ": needs file and caption");
            return {
                full: "data/gallery/photos/" + p.file,
                thumb: "data/gallery/thumbs/" + String(p.file).replace(/\.[^.]*$/, "") + ".jpg",
                alt: p.alt || p.caption,
                caption: p.caption
            };
        });
    })();

    function galleryTiles(photos, cls) {
        return photos.map(function (p) {
            return '<div class="' + cls + '">\n' +
                '    <a href="photo.html?image=' + esc(p.full) + '">\n' +
                '        <img src="' + esc(p.thumb) + '" alt="' + esc(p.alt) + '" loading="lazy">\n' +
                '        <span class="tooltip">' + esc(p.caption) + "</span>\n" +
                "    </a>\n" +
                "</div>\n";
        }).join("\n");
    }

    // ----------------------------------------------------------------- render

    function $(sel) { return document.querySelector(sel); }

    var render = {
        index: function () {
            var box = $(".news-list");
            box.insertAdjacentHTML("afterbegin", "\n" + newsItems(loadNews().slice(0, config.news.home.count), ""));
        },
        news: function () {
            $("#news-list").innerHTML = "\n" + newsItems(loadNews(), "");
        },
        publications: function () {
            $("main").innerHTML = "\n" + publicationGroups().map(function (g) {
                return '<div class="year-divider">' + esc(g.label) + "</div>\n\n" + g.papers.map(function (p) {
                    return '<div class="paper">\n' +
                        '    <div class="paper-title">' + esc(p.title) + "</div>\n" +
                        '    <div class="paper-authors">' + p.authors + "</div>\n" +
                        '    <div class="paper-venue">' + p.venue + "</div>\n" +
                        (p.links ? '    <div class="paper-links">' + p.links + "</div>\n" : "") +
                        "</div>\n";
                }).join("\n");
            }).join("\n");
        },
        group: function () {
            var members = Object.keys(people).map(function (t) { return people[t]; }).filter(function (p) { return p.current; });
            $(".member-list").innerHTML = "\n" + members.map(function (p) {
                if (!p.file) fail("members.yaml: " + p.tag + " is missing photo");
                return '<li class="member-item">\n' +
                    '    <img src="data/members/photos/' + esc(p.file) + '" alt="' + esc(p.alt) + '">\n' +
                    (p.url ? '    <a href="' + esc(p.url) + '">' + esc(p.name) + "</a>\n"
                           : "    <span>" + esc(p.name) + "</span>\n") +
                    '    <span class="member-position">' + esc(p.position) + "</span>\n" +
                    "</li>\n";
            }).join("\n");

            var count = config.gallery.preview.count;
            $(".gallery-preview").innerHTML = "\n" + galleryTiles(galleryPhotos.slice(0, count), "gallery-preview-item");
            $('[data-gallery-dir="prev"]').setAttribute("aria-label", "Show previous " + count + " gallery photos");
            $('[data-gallery-dir="next"]').setAttribute("aria-label", "Show next " + count + " gallery photos");

            var list = $(".alumni-list"), heading = list.previousElementSibling;
            if (!config.members.alumni.show) {
                heading.remove();
                list.remove();
                return;
            }
            heading.textContent = config.members.alumni.heading;
            var alumni = ((LOG.data.members || {}).members || {}).alumni || {};
            list.innerHTML = "\n" + Object.keys(alumni).map(function (tag) {
                var a = alumni[tag] || {};
                return "<li>" + (a.url ? '<a href="' + esc(a.url) + '">' + esc(a.name) + "</a>" : esc(a.name)) +
                    " " + esc(a.note || "") + "</li>\n";
            }).join("");
        },
        gallery: function () {
            $(".gallery-grid").innerHTML = "\n" + galleryTiles(galleryPhotos, "gallery-item");
        },
        photo: function () { /* layout/scripts/photo.js shows LOG.gallery.photos */ }
    };

    if (render[LOG.page]) render[LOG.page]();

    LOG.config = config;
    LOG.gallery = { photos: galleryPhotos };
    if (errors.length) console.error("Data errors (run tools/build.py --check):\n  " + errors.join("\n  "));
})();
