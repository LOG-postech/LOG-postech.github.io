# News

News items are kept in one YAML file per year: `2026.yaml`, `2025.yaml`, … The
News page lists them newest first, and the home page's **Recent News** shows the
newest few, both generated from these files. Nothing is copied by hand.

## Add a news item

Add it at the top of its year's file (create `2027.yaml` for a new year), with a
blank line between items:

```yaml
- idx: 39
  date: "2026-10"
  text: >-
    🏆 @kwanheelee received the IITP President's Award at
    [AI Connect Korea 2026](https://www.aiconnectkorea.kr/).
```

| Field | Required | Rule |
|---|---|---|
| `idx` | yes | The highest `idx` in any year + 1. Sets the order: higher is newer. Never reuse one. |
| `date` | yes | `"YYYY-MM"`, or `"YYYY-MM-DD"` if you know the day, in quotes. Shown as `Oct 2026`. Must be in the file's year. |
| `text` | yes | One paragraph of Markdown, after `>-` on the next lines, indented. Line breaks inside it are just spaces. |
| `paper` | no | Key(s) of papers the item is about but does not link (see below). |

Start `text` with the emoji for the item's kind:

| Emoji | Kind |
|---|---|
| 🎓 | paper accepted / released |
| 🏆 | award, fellowship, scholarship |
| 🤝 | grant or program the lab was selected for |
| 🧑‍💻 | internship, joining a company |
| ✈️ | visit, research stay |
| 🏛 | workshop or event we organize |

Links use Markdown: `[text](https://...)`, or `[text](paperkey)` for a paper.
External links open in a new tab automatically. Use `*italic*` and `**bold**` if
needed. The top of each year file lists every field as a template.

Then check it and preview it (see the repository README):

```bash
python3 tools/build.py --check
python3 tools/build.py --serve     # http://localhost:8000
```

## People and papers: `@tags` and paper keys

Refer to lab members by their **tag** from `data/members/members.yaml`. The page
shows their first name (or their `short` name), with their face under the date:

```yaml
  text: >-
    🏆 @hyunjijung, @hyeondojang, and @jinseokchung have been selected for the NRF Research Grant.
```

→ "Hyunji, Hyeondo, and Jinseok have been selected for …"

For news about a paper, refer to it by its key in `data/publications/papers.bib`.
Its in-lab authors get faces too. To link to it, use the key as the link target;
the build fills in the paper's `paper` URL from papers.bib:

```yaml
  text: >-
    🎓 Our [paper](shin23closer) on concept bottleneck models has been accepted to ICML 2023.
```

For a paper mentioned without a link (no `paper` URL yet), name it in `paper`:

```yaml
- idx: 34
  date: "2026-09"
  paper: lee26fresco                  # or a list: [lee26fresco, jang26hidden]
  text: >-
    🎓 Our paper on asynchronous pipeline parallelism has been accepted to NeurIPS 2026.
```

Faces appear only from these: the authors of the papers (`paper` first, then
linked ones in text order), then people `@tagged` in the text, and only for
current members. Alumni tags show the name
without a face. Nothing is guessed from plain names or links. An unknown tag or
paper key stops the build with an error.

## Edit or remove an item

Edit it in place. To remove an item, delete its entry. Gaps in `idx` are fine.
To reorder two items, swap their `idx`.

## Presentation settings (`config.toml`)

| Setting | Meaning |
|---|---|
| `date_format` | How the date is written (`"%b %Y"` → `Oct 2026`) |
| `home.count` | Items in Recent News on the home page |
| `page.since` | Oldest month listed on the News page. Older items stay in their year files as the archive but are not shown |
| `page.initial` / `page.step` | Items shown when the News page opens / added per **Show more** click |
| `faces.max` | Faces under a date before the rest collapse into "+N" |
