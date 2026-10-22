/* Small member faces next to news items and paper authors.

   There is no separate database: group.html is the member list and
   publications.html is the paper list. Both are fetched at runtime, so adding
   a member or a paper there is all it takes — nothing to keep in sync.

   News (news.html, home page) — faces under the date, like the reply faces in
   Slack. Who appears, in this order:
     1. data-people="Hyunji, Hyeondo"   explicit first or full names
     2. data-paper="FRESCO"             a paper, matched by title substring
     3. links in the item that match a paper's links (arXiv id, OpenReview id, URL)
     4. members mentioned by first or full name in the text
   Authors of a matched paper are included when they are current members.
   data-people="none" turns the faces off for that item.

   Publications — a face before each current member's name in the author list.

   Every face links to the member's own site (new tab) when group.html has one,
   otherwise to their card on group.html (#<photo file name>).

   Usage: LOGPeople.decorateNews(container), LOGPeople.decoratePapers(container) */
(function () {
  var membersPromise = null;
  var papersPromise = null;
  var MAX_FACES = 3;

  function supported() {
    return !!(window.fetch && window.DOMParser);
  }

  function fetchDoc(url) {
    return fetch(url, { cache: "no-cache" })
      .then(function (r) { return r.ok ? r.text() : Promise.reject(url); })
      .then(function (html) { return new DOMParser().parseFromString(html, "text/html"); });
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

  /* { list: [person], byFull: {name: person}, byFirst: {name: person} } */
  function loadMembers() {
    if (membersPromise) return membersPromise;
    membersPromise = fetchDoc("group.html").then(function (doc) {
      var db = { list: [], byFull: {}, byFirst: {} };
      Array.prototype.forEach.call(doc.querySelectorAll(".member-item"), function (li) {
        var img = li.querySelector("img");
        var label = li.querySelector("a, span:not(.member-position)");
        if (!img || !label) return;
        var photo = img.getAttribute("src");
        var person = {
          name: clean(label.textContent),
          photo: photo,
          url: label.tagName === "A" ? label.getAttribute("href") : null,
          slug: memberSlug(photo)
        };
        db.list.push(person);
        // The alt text is an alias (it has spelled a name differently before).
        [person.name, clean(img.getAttribute("alt"))].forEach(function (n) {
          if (!n) return;
          db.byFull[n.toLowerCase()] = person;
          db.byFirst[n.split(" ")[0].toLowerCase()] = person;
        });
      });
      return db;
    });
    return membersPromise;
  }

  function loadPapers() {
    if (papersPromise) return papersPromise;
    papersPromise = fetchDoc("publications.html").then(function (doc) {
      return Array.prototype.map.call(doc.querySelectorAll(".paper"), function (el) {
        var title = el.querySelector(".paper-title");
        var authors = el.querySelector(".paper-authors");
        return {
          title: title ? clean(title.textContent).toLowerCase() : "",
          authors: authors ? authors.textContent.split(",").map(clean) : [],
          links: Array.prototype.map.call(el.querySelectorAll("a[href]"), function (a) {
            return linkKey(a.getAttribute("href"));
          })
        };
      });
    });
    return papersPromise;
  }

  /* group_profile/jinseokchung.jpg -> "jinseokchung"; group.html uses the same
     rule to give each member card an id. */
  function memberSlug(photo) {
    return (photo || "").split("/").pop().replace(/\.[^.]*$/, "");
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
      a.href = "group.html#" + person.slug;
    }
    return a;
  }

  function face(person, linked) {
    var wrap = linked ? profileLink(person, "member-face") : document.createElement("span");
    if (!linked) wrap.className = "member-face";
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
      papers.forEach(function (p) { if (p.title.indexOf(paperRef) !== -1) addPaper(p); });
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
    shown.forEach(function (p) { row.appendChild(face(p, true)); });
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
    Promise.all([loadMembers(), loadPapers()])
      .then(function (db) {
        Array.prototype.forEach.call(container.querySelectorAll(".news-item"), function (item) {
          renderNews(item, peopleFor(item, db[0], db[1]));
        });
      })
      .catch(function () { /* faces are decorative; leave the news as is */ });
  }

  /* ---- Publications ---- */

  function renderAuthors(el, members) {
    if (el.querySelector(".member-face")) return;
    var authors = el.textContent.split(",");
    el.textContent = "";
    authors.forEach(function (raw, i) {
      if (i) el.appendChild(document.createTextNode(", "));
      var label = raw.trim();
      var person = members.byFull[clean(label).toLowerCase()];
      if (!person) {
        el.appendChild(document.createTextNode(label));
        return;
      }
      // Face and name together make one link: a bigger target than the face.
      var link = profileLink(person, "paper-member");
      link.appendChild(face(person, false));
      link.appendChild(document.createTextNode(label));
      el.appendChild(link);
    });
  }

  function decoratePapers(container) {
    if (!container || !supported()) return;
    loadMembers()
      .then(function (members) {
        Array.prototype.forEach.call(container.querySelectorAll(".paper-authors"), function (el) {
          renderAuthors(el, members);
        });
      })
      .catch(function () { /* leave the plain author list */ });
  }

  window.LOGPeople = {
    decorateNews: decorateNews,
    decoratePapers: decoratePapers,
    memberSlug: memberSlug
  };
})();
