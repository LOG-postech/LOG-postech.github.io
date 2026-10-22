# Research

`topics.yaml` holds the research areas on the Research page in display order,
and `icons/` holds their pictures.

## Add or edit a topic

```yaml
- key: distributed               # unique id, letters only
  title: Distributed Training
  color: green                   # red | green | blue | orange
  icon: opt-distributed.png      # file in icons/
  icon_class: icon-round         # optional; for round icons, see config.toml
  summary: >-
    The shift toward massive-scale models has made distributed training
    essential ...
  details:                       # shown when "more" is clicked
  - title: Asynchronous Training
    papers: NeurIPS '26, [ICML '26](https://arxiv.org/abs/2602.03515)
    text: >-
      We create algorithms that allow devices to work independently ...
```

| Field | Required | Notes |
|---|---|---|
| `key` | yes | Unique id, letters only. |
| `title` | yes | Coloured heading at the start of the paragraph. |
| `color` | yes | `red`, `green`, `blue` or `orange`. |
| `icon` | yes | Picture in `icons/`. Shown as a square. |
| `icon_class` | no | `icon-round` gives round pictures less padding, so they look as big as square ones. |
| `alt` | no | Icon description, if it should differ from `title`. |
| `hidden` | no | `true` keeps the topic here but off the page. |
| `summary` | yes | The paragraph. `>-` lets it span several lines. |
| `details` | no | Sub-topics. `papers` is optional; it uses Markdown links and is shown in brackets after the title. |

To add a paper to a sub-topic, add it to that sub-topic's `papers` line.

## Presentation settings (`config.toml`)

The icons share one size, worked out in the browser from the shortest
paragraph's height:

| Setting | Meaning |
|---|---|
| `icons.scale` | Icon height as a fraction of the shortest paragraph |
| `icons.min` / `icons.max` | Limits in px |
| `icons.max_fraction` | Limit as a fraction of the column width (narrow screens) |
| `icons.padding` / `icons.round_padding` | Space between picture and frame; less for `icon-round` |
