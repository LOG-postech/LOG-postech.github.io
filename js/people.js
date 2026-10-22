/* Small member faces under the date of each news item (news.html, home page),
   like the reply faces in Slack.

   Data comes from data/db.json, which tools/build-db.py generates from
   data/members.bib and data/papers.bib. (Faces on publications.html are
   generated statically by the same script.)

   Who appears under a news item, in this order:
     1. data-people="Hyunji, Hyeondo"   explicit first or full names
     2. data-paper="lee2026fresco"      a paper by its key in data/papers.bib
                                        (a part of its title also works)
     3. links in the item that match a paper's links (arXiv id, OpenReview id, URL)
     4. members mentioned by first or full name in the text
   Authors of a matched paper are included when they are current members.
   data-people="none" turns the faces off for that item.

   Every face links to the member's own site (new tab) if they have one,
   otherwise to their card on group.html (#<member key>).

   Usage: LOGPeople.decorateNews(container) */
(function () {
  var dbPromise = null;
  var MAX_FACES = 3;

  function supported() {
    return !!window.fetch;
  }

  function clean(s) {
    return (s || "").replace(/[*†‡]/g, "").replace(/\s+/g, " ").trim();
  }

  function linkKey(href) {
    if (!href) return null;
    var m = href.match(/arxiv\.org\/(?:abs|pdf)\/(\d{4}\.\d{4,5})/i);
    if (m) return "arxiv:" + m[1];
    m = href.match(/openreview\.net\/(?:forum|pdf)\?id=([\w-]+)/i);
    if (m) return "openreview:" + m[1];
    return href.toLowerCase().replace(/^https?:\/\/(www\.)?/, "").replace(/[?#].*$/, "").replace(/\/+$/, "");
  }

  /* { members: { list, byFull, byFirst }, papers: [{ key, title, authors, links }] } */
  function loadDB() {
    if (dbPromise) return dbPromise;
    dbPromise = fetch("data/db.json", { cache: "no-cache" })
      .then(function (r) { return r.ok ? r.json() : Promise.reject(); })
      .then(function (data) {
        var members = { list: data.members, byFull: {}, byFirst: {} };
        data.members.forEach(function (person) {
          [person.name].concat(person.aliases || []).forEach(function (n) {
            members.byFull[n.toLowerCase()] = person;
            members.byFirst[n.split(" ")[0].toLowerCase()] = person;
          });
        });
        var papers = data.papers.map(function (p) {
          return {
            key: p.key.toLowerCase(),
            title: p.title.toLowerCase(),
            authors: p.authors,
            links: p.links.map(linkKey)
          };
        });
        return { members: members, papers: papers };
      });
    return dbPromise;
  }

  function profileLink(person, className) {
    var a = document.createElement("a");
    a.className = className;
    a.title = person.name;
    if (person.url) {
      a.href = person.url;
      a.target = "_blank";
      a.rel = "noopener";
    } else {
      a.href = "group.html#" + person.key;
    }
    return a;
  }

  function face(person) {
    var wrap = profileLink(person, "member-face");
    var img = document.createElement("img");
    img.src = person.photo;
    img.alt = "";
    img.loading = "lazy";
    img.decoding = "async";
    wrap.appendChild(img);
    return wrap;
  }

  /* ---- News ---- */

  function escapeRe(s) {
    return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  }

  function peopleFor(item, members, papers) {
    var found = [];
    function add(person) {
      if (person && found.indexOf(person) === -1) found.push(person);
    }
    function addPaper(paper) {
      paper.authors.forEach(function (a) { add(members.byFull[a.toLowerCase()]); });
    }

    var explicit = item.getAttribute("data-people");
    if (explicit && explicit.trim().toLowerCase() === "none") return [];
    if (explicit) {
      explicit.split(",").forEach(function (n) {
        n = clean(n).toLowerCase();
        add(members.byFull[n] || members.byFirst[n]);
      });
    }

    var paperRef = (item.getAttribute("data-paper") || "").trim().toLowerCase();
    if (paperRef) {
      papers.forEach(function (p) {
        if (p.key === paperRef || p.title.indexOf(paperRef) !== -1) addPaper(p);
      });
    }

    var content = item.querySelector(".news-content") || item;
    Array.prototype.forEach.call(content.querySelectorAll("a[href]"), function (a) {
      var key = linkKey(a.getAttribute("href"));
      papers.forEach(function (p) { if (key && p.links.indexOf(key) !== -1) addPaper(p); });
    });

    // Mentions, in the order they appear in the text.
    var text = content.textContent;
    members.list
      .map(function (m) {
        var first = m.name.split(" ")[0];
        var re = new RegExp("\\b(" + escapeRe(m.name) + "|" + escapeRe(first) + ")\\b");
        var hit = re.exec(text);
        return { person: m, at: hit ? hit.index : -1 };
      })
      .filter(function (x) { return x.at !== -1; })
      .sort(function (a, b) { return a.at - b.at; })
      .forEach(function (x) { add(x.person); });

    return found;
  }

  function renderNews(item, people) {
    var old = item.querySelector(".news-people");
    if (old) old.parentNode.removeChild(old);
    if (!people.length) return;

    var names = people.map(function (p) { return p.name; }).join(", ");
    var row = document.createElement("span");
    row.className = "news-people";
    row.setAttribute("aria-label", names);
    row.title = names;

    // Like Slack: a few faces, then "+N" for the rest.
    var shown = people.length > MAX_FACES ? people.slice(0, MAX_FACES - 1) : people;
    shown.forEach(function (p) { row.appendChild(face(p)); });
    if (shown.length < people.length) {
      var more = document.createElement("span");
      more.className = "member-face member-face-more";
      more.textContent = "+" + (people.length - shown.length);
      row.appendChild(more);
    }

    (item.querySelector(".news-date") || item).appendChild(row);
  }

  function decorateNews(container) {
    if (!container || !supported()) return;
    loadDB()
      .then(function (db) {
        Array.prototype.forEach.call(container.querySelectorAll(".news-item"), function (item) {
          renderNews(item, peopleFor(item, db.members, db.papers));
        });
      })
      .catch(function () { /* faces are decorative; leave the news as is */ });
  }

  window.LOGPeople = { decorateNews: decorateNews };
})();
