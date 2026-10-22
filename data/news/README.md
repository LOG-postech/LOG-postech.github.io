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
   🎓 Our [paper](https://arxiv.org/abs/2602.03515) on asynchronous pipeline parallelism has been accepted to NeurIPS 2026.
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

3. Check it and preview it (see the repository README):

   ```bash
   python3 tools/build.py --check
   python3 tools/build.py --serve     # http://localhost:8000
   ```

## Member faces (optional)

Small faces of current members appear under the date. They are found
automatically: members named in the text, and the authors of a paper the item
links to. To choose them yourself, start the file with front matter:

```markdown
---
people: Hyunji, Hyeondo, Jinseok   # first or full names, in this order
paper: FRESCO                      # a paper, by part of its title
---
🏆 Hyunji, Hyeondo, and Jinseok have been selected for ...
```

`people: none` turns the faces off for that item. These are the only two fields.

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
