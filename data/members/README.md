# Members

`members.yaml` lists the people on the Members page, and `photos/` holds their
headshots.

## Add a member

1. Put their photo in `photos/`, named after them without spaces:
   `photos/hyeondojang.jpg`. Any size is fine; the pre-commit hook shrinks
   it to 512px (see the repository README).
2. Add them to `members:` in `members.yaml`, at the position they should appear:

   ```yaml
   - name: Hyeondo Jang
     photo: hyeondojang.jpg
     position: MS Student
     url: https://hyeondo-jang.github.io/   # optional: name links here
   ```

| Field | Required | Notes |
|---|---|---|
| `name` | yes | As shown under the photo. Also how news and papers find this person's face. |
| `photo` | yes | File name in `photos/`. Also the anchor of their card: `group.html#hyeondojang`. |
| `position` | yes | `Principal Investigator`, `PhD Student`, `MS/PhD Student`, `MS Student`, … |
| `url` | no | Personal site. Without it the name is plain text. |
| `alt` | no | Photo description, if it should differ from `name`. |

## When someone graduates

Remove them from `members:`, and add them to `alumni:`:

```yaml
- name: Jaehyeon Jeong
  url: https://...          # optional
  note: (MS 2026 → ETRI)
```

Keep their photo in `photos/`, since old pages may still link to it.

## Presentation settings (`config.toml`)

| Setting | Meaning |
|---|---|
| `alumni.show` | Show the Alumni list |
| `alumni.heading` | Its heading |

The gallery preview on the Members page is configured in `data/gallery/`.
