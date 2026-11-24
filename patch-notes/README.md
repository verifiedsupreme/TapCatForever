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

Post each part as its own message, in order, and don't post the break lines.

## Pictures

Some messages end with one or more lines like:

```
<!-- image: media/1.7.0_new_sets.png -->
```

Attach each named picture (its path is from this folder, so `patch-notes/media/...`) to the message it's in, and remove the line from the text. `index.json` lists the same pictures for every version, each with its file, a caption and the message number it goes with (1 = the first message).

For 1.7.0:
- `media/1.7.0_new_sets.png`: a promo of all 11 new legendary sets. It goes with the first message.
- `media/1.7.0_sets_tailoring.png`, `media/1.7.0_sets_smithing_leather.png` and `media/1.7.0_sets_gathering.png`: the sets by profession, with their names and titles. They go with the message about the legendary profession sets.

The pictures are made by `tools/make_set_showcase.py`. The first message starts with a `# TapCatForever <version>` heading and the one-line headline. The rest is Discord markdown: **bold** section titles and `-` bullets.

## Raw links

On the `main` branch:

- https://raw.githubusercontent.com/verifiedsupreme/TapCatForever/main/patch-notes/latest.md
- https://raw.githubusercontent.com/verifiedsupreme/TapCatForever/main/patch-notes/index.json
- https://raw.githubusercontent.com/verifiedsupreme/TapCatForever/main/patch-notes/media/1.7.0_new_sets.png (and the other pictures the same way)

Roadmap pictures for posts are in `media/roadmap_*.png` (see ROADMAP.md).
