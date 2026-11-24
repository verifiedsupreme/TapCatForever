# Patch notes for Discord

Made from CHANGELOG.md by `python3 tools/make_patch_notes.py` (run with every release). Don't edit these files by hand.

- `latest.md`: the newest version's notes.
- `<version>.md`: one file per version, for example `1.7.0.md`.
- `index.json`: every version, newest first, with its file, a one-line headline and how many messages it takes.

## Posting them

Each file is already split into Discord messages, every one under Discord's 2000-character limit. The messages are separated by a line that says exactly:

```
<!-- message break -->
```

Post each part as its own message, in order, and don't post the break lines. The first message starts with a `# TapCatForever <version>` heading and the one-line headline. The rest is Discord markdown: **bold** section titles and `-` bullets.

## Raw links

On the `main` branch:

- https://raw.githubusercontent.com/verifiedsupreme/TapCatForever/main/patch-notes/latest.md
- https://raw.githubusercontent.com/verifiedsupreme/TapCatForever/main/patch-notes/index.json

Roadmap pictures for posts are in `media/roadmap_*.png` (see ROADMAP.md).
