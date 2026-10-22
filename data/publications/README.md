# Publications

Papers are grouped into one YAML file per heading on the Publications page:
`preprint.yaml`, `2026.yaml`, `2025.yaml`, …, `previous.yaml`. Each file is a list
of papers **in display order**, top to bottom.

## Add a paper

Add an entry to the right file, at the position it should appear:

```yaml
- title: 'FRESCO: A Novel Consistency Control for Asynchronous Pipeline Parallel Training'
  authors: Dongyeop Lee, Namhoon Lee
  venue: NeurIPS 2026 **(Oral)**
  links:
    paper: https://arxiv.org/abs/2602.03515
    code: https://github.com/LOG-postech/fresco
```

| Field | Required | Notes |
|---|---|---|
| `title` | yes | Quote it with `'...'` if it contains a colon (`:`). |
| `authors` | yes | Comma-separated, as printed. Mark equal contribution with `*`. Current members get their face automatically. |
| `venue` | yes | Wrap highlights in `**...**`: `ACL 2026 **(Oral)**; **KCC 2026 Outstanding Paper Award**`. |
| `links` | no | `label: url`, in display order. Use lowercase labels: `paper`, `code`, `slides`, `model`, `thesis`. |
| `link_separator` | no | Overrides `links.separator` in `config.toml` for this paper. |

When a preprint is accepted, move its entry from `preprint.yaml` to the year's
file and update `venue`.

## Start a new year

Create `2027.yaml`, then add `"2027"` to `groups.order` in `config.toml`. The
build refuses to run if a file is not listed there, so a year cannot go missing.

## Presentation settings (`config.toml`)

| Setting | Meaning |
|---|---|
| `groups.order` | Which files are shown, top to bottom |
| `groups.labels` | Heading for a file (`preprint = "Preprint"`); others use the file name |
| `links.separator` | Text between a paper's links |

> Some papers have `link_separator: " "`. Until now, link spacing was set paper
> by paper: some had a space between `paper` and `code`, most did not. This
> keeps the page exactly as it was. Delete those lines to make every paper
> consistent.
