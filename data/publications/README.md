# Publications

All papers are in one BibTeX file, `papers.bib`. The Publications page groups
them under **Preprint**, then each year (newest first), then **Previous**. Within a
group, papers appear in the order they are written in the file.

## Add a paper

Add an entry where it should appear:

```bibtex
@inproceedings{jang26hidden,
  title  = {Hidden in Plain Sight: The Overlooked Significance of Canonical Elements for Extreme LLM Sparsity},
  author = {@hyeondojang and @kwanheelee and @dongyeoplee and @namhoonlee},
  venue  = {EMNLP 2026},
  year   = {2026},
  award  = {CKAIA 2026 Best Paper Award},
  paper  = {https://arxiv.org/abs/2609.06557},
}
```

The key (`jang26hidden`) is first author's last name + 2-digit year + first title
word. News items refer to the paper by it as `@jang26hidden`, so keep it once
chosen.

| Field | Kind | Meaning |
|---|---|---|
| `title` | text | Required. Write `\&` for &. |
| `author` | text | Required. Names joined by `and`. Lab members and alumni by **tag**: `@hyunjijung`; current members get their face. Others by name: `Dan Alistarh`. Mark equal contribution with `*`: `@hyunjijung*`. |
| `venue` | text | Required. As printed: `NeurIPS 2026`, `ICML 2026 Workshop on ...`, `arXiv 2026`. |
| `year` | text | Required. Decides the year heading. |
| `oral` / `spotlight` | true/false | Adds a highlighted `(Oral)` / `(Spotlight)` after the venue. |
| `also` | text | Another venue of the same paper: `ICLR 2023 Workshop on ...`. |
| `award` | text | Shown highlighted at the end: `CKAIA 2026 Best Paper Award`. |
| `is_preprint` | true/false | Listed under **Preprint**, above the years. |
| `is_previous` | true/false | Listed under **Previous**, below the years (work before the lab). |
| `spaced_links` | true/false | Space between this paper's links (see note below). |
| *anything else* | URL | A link, labelled with the field name, in the order written. In use: `paper`, `code`, `code-torch`, `code-jax`, `model`, `OpenReview`. A new name (e.g. `slides`) just works. |

Fields left out are false or empty. When a preprint is accepted, remove
`is_preprint` and update `venue` and `year`.

## Presentation settings (`config.toml`)

| Setting | Meaning |
|---|---|
| `groups.preprint` / `groups.previous` | The two special headings |
| `links.separator` | Text between a paper's links |

> `spaced_links = {true}` reproduces the page as it was: until now, some papers
> had a space between `paper` and `code` and most did not. Delete those lines to
> make every paper the same.
