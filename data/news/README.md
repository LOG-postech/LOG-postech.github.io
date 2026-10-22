# News

Each news item is one Markdown file in this directory. The News page lists them
newest first, and the home page's **Recent News** shows the newest few, both
generated from these files. Nothing is copied by hand.

## Add a news item

1. Create a file named `{idx}_{date}_{simple-title}.md`:

   | Part | Rule | Example |
   |---|---|---|
   | `idx` | Next number: the highest existing index + 1, zero-padded to 3 digits. Sets the order: higher is newer. | `039` |
   | `date` | `YYYY-MM`, or `YYYY-MM-DD` if you know the day. Shown as `Oct 2026`. | `2026-10` |
   | `simple-title` | A few lowercase words joined with `-`. Only for finding the file. | `fresco-neurips-oral` |

   → `039_2026-10_fresco-neurips-oral.md`

2. Write the item as one paragraph, starting with the emoji for its kind:

   ```markdown
   🏆 @kwanheelee received the IITP President's Award at [AI Connect Korea 2026](https://www.aiconnectkorea.kr/).
   ```

   | Emoji | Kind |
   |---|---|
   | 🎓 | paper accepted / released |
   | 🏆 | award, fellowship, scholarship |
   | 🤝 | grant or program the lab was selected for |
   | 🧑‍💻 | internship, joining a company |
   | ✈️ | visit, research stay |
   | 🏛 | workshop or event we organize |

   Links use Markdown: `[text](https://...)`. External links open in a new tab
   automatically. Use `*italic*` and `**bold**` if needed.

   Mention lab members as `@tag` and name papers by key (see below).

3. Check it and preview it (see the repository README):

   ```bash
   python3 tools/build.py --check
   python3 tools/build.py --serve     # http://localhost:8000
   ```

## People and papers: `@tags` and paper keys

Refer to lab members by their **tag** from `data/members/members.yaml`. The page
shows their first name (or their `short` name), with their face under the date:

```markdown
🏆 @hyunjijung, @hyeondojang, and @jinseokchung have been selected for the NRF Research Grant.
```

→ "Hyunji, Hyeondo, and Jinseok have been selected for …"

For news about a paper, name the paper by its key in
`data/publications/papers.bib`. Its in-lab authors get faces too:

```markdown
---
paper: lee26fresco                    # or a list: [seong25memeic, park25analysis]
---
🎓 Our paper on asynchronous pipeline parallelism has been accepted to NeurIPS 2026.
```

Faces appear only for these two: the authors of `paper`, then people `@tagged` in
the text, in that order, and only for current members. Alumni tags show the name
without a face. Nothing is guessed from plain names or links. An unknown tag or
paper key stops the build with an error.

## Edit or remove an item

Edit the file. To remove an item, delete the file. Gaps in the numbering are
fine. To reorder two items, swap their `idx`.

## Presentation settings (`config.toml`)

| Setting | Meaning |
|---|---|
| `date_format` | How the date is written (`"%b %Y"` → `Oct 2026`) |
| `home.count` | Items in Recent News on the home page |
| `page.since` | Oldest month listed on the News page. Older items stay here as the archive but are not shown |
| `page.initial` / `page.step` | Items shown when the News page opens / added per **Show more** click |
| `faces.max` | Faces under a date before the rest collapse into "+N" |
