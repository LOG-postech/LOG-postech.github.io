# Members

`members.yaml` lists the people on the Members page, and `photos/` holds their
headshots.

## Add a member

1. Put their photo in `photos/`, named after them without spaces:
   `photos/hyeondojang.jpg`. Any size is fine; the pre-commit hook shrinks
   it to 512px (see the repository README).
2. Add them to `members:` in `members.yaml`, at the position they should appear:

   ```yaml
   - tag: hyeondojang
     name: Hyeondo Jang
     photo: hyeondojang.jpg
     position: MS Student
     url: https://hyeondo-jang.github.io/   # optional: name links here
   ```

| Field | Required | Notes |
|---|---|---|
| `tag` | yes | How news and papers refer to them: `@hyeondojang`. Lowercase, no spaces; use the photo's name. Never reuse a tag. |
| `name` | yes | As shown under the photo and in author lists. |
| `short` | no | Name used for `@tag` in news. Defaults to the first word of `name`. |
| `photo` | yes | File name in `photos/`. Also the anchor of their card: `group.html#hyeondojang`. |
| `position` | yes | `Principal Investigator`, `PhD Student`, `MS/PhD Student`, `MS Student`, … |
| `url` | no | Personal site. Without it the name is plain text. |
| `alt` | no | Photo description, if it should differ from `name`. |

## When someone graduates

Remove them from `members:`, and add them to `alumni:`:

```yaml
- tag: jaehyeonjeong        # keep the same tag, so old news and papers still work
  name: Jaehyeon Jeong
  url: https://...          # optional
  note: (MS 2026 → ETRI)
```

Their `@tag` keeps working in news and papers, showing the name without a face.
Keep their photo in `photos/`, since old pages may still link to it. Someone who
stays on (MS → PhD) can be in both lists under one tag.

## Presentation settings (`config.toml`)

| Setting | Meaning |
|---|---|
| `alumni.show` | Show the Alumni list |
| `alumni.heading` | Its heading |

The gallery preview on the Members page is configured in `data/gallery/`.
