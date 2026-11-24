#!/usr/bin/env python3
"""Patch notes ready to post on Discord, made from CHANGELOG.md (run it after writing a version's
CHANGELOG section, with make_news.py):

  patch-notes/<version>.md   one file per version, already split into Discord messages
  patch-notes/latest.md      the newest version
  patch-notes/index.json     every version, newest first, with its file, headline and message count

Each file is one or more messages separated by a line that says only MESSAGE_BREAK (below), every
message under Discord's 2000-character limit. Headings and bullets are Discord markdown."""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "patch-notes")
MESSAGE_BREAK = "<!-- message break -->"
IMAGE_LINE = "<!-- image: %s -->"     # attach this picture (path from patch-notes/) to the message it's in

# pictures for a version (tools/make_set_showcase.py): file in patch-notes/, caption, and text of the
# section it goes with (None: the first message)
IMAGES = {
    "1.7.0": [
        ("media/1.7.0_new_sets.png", "11 new legendary sets", None),
        ("media/1.7.0_sets_tailoring.png", "Tailoring sets", "Legendary profession sets"),
        ("media/1.7.0_sets_smithing_leather.png", "Blacksmithing and Leatherworking sets", "Legendary profession sets"),
        ("media/1.7.0_sets_gathering.png", "Herbalism, Fishing, Cooking and First Aid sets", "Legendary profession sets"),
    ],
}
LIMIT = 1900          # a little room under Discord's 2000


def sections():
    md = open(os.path.join(ROOT, "CHANGELOG.md"), encoding="utf-8").read()
    parts = re.split(r"^## (\S+)\s*$", md, flags=re.M)
    for i in range(1, len(parts), 2):
        ver, body = parts[i], parts[i + 1].strip()
        if re.match(r"^\d+\.\d+\.\d+(\.\d+)?$", ver):
            yield ver, body


def blocks(body):
    """the body's paragraphs, each heading kept with what follows it"""
    out, cur = [], []
    for line in body.splitlines():
        if re.match(r"^\*\*.+\*\*$", line.strip()) and cur:
            out.append("\n".join(cur).strip()); cur = []
        cur.append(line)
    if cur: out.append("\n".join(cur).strip())
    return [b for b in out if b]


def split_long(text):
    """a block longer than one message, cut between lines (or sentences, for one very long line)"""
    msgs, cur = [], ""
    for line in text.splitlines():
        # a very long line goes in sentence by sentence (each piece keeps its trailing space)
        pieces = re.split(r"(?<=\. )", line) if len(line) > LIMIT else [line]
        for k, p in enumerate(pieces):
            sep = "" if k > 0 or not cur else "\n"
            if cur and len(cur) + len(sep) + len(p) > LIMIT:
                msgs.append(cur.rstrip()); cur, sep = "", ""
            cur += sep + p
    if cur.strip(): msgs.append(cur.rstrip())
    return msgs


def messages(ver, body, headline):
    head = "# TapCatForever %s" % ver
    if headline: head += "\n" + headline
    msgs, cur = [], head
    for b in blocks(body):
        add = "\n\n" + b
        if len(cur) + len(add) <= LIMIT:
            cur += add
        else:
            msgs.append(cur)
            if len(b) <= LIMIT: cur = b
            else:
                parts = split_long(b)
                msgs.extend(parts[:-1]); cur = parts[-1]
    msgs.append(cur)
    return msgs


def main():
    import importlib.util
    spec = importlib.util.spec_from_file_location("make_news", os.path.join(HERE, "make_news.py"))
    news = importlib.util.module_from_spec(spec); spec.loader.exec_module(news)
    os.makedirs(OUT, exist_ok=True)
    index = []
    for n, (ver, body) in enumerate(sections()):
        hl = news.HIGHLIGHTS.get(ver)
        msgs = messages(ver, body, hl)
        assert all(len(m) <= 2000 for m in msgs), ver
        imgs = []
        for f, cap, anchor in IMAGES.get(ver, []):
            assert os.path.exists(os.path.join(OUT, f)), f
            k = 0
            if anchor:
                k = next((i for i, m in enumerate(msgs) if anchor in m), 0)
            msgs[k] += "\n" + IMAGE_LINE % f
            imgs.append({"file": f, "caption": cap, "message": k + 1})
        text = ("\n\n" + MESSAGE_BREAK + "\n\n").join(msgs) + "\n"
        open(os.path.join(OUT, ver + ".md"), "w", encoding="utf-8").write(text)
        if n == 0:
            open(os.path.join(OUT, "latest.md"), "w", encoding="utf-8").write(text)
        index.append({"version": ver, "file": ver + ".md", "headline": hl, "messages": len(msgs), "images": imgs})
    json.dump({"latest": index[0]["version"], "message_break": MESSAGE_BREAK, "image_line": IMAGE_LINE % "<file>", "versions": index},
              open(os.path.join(OUT, "index.json"), "w", encoding="utf-8"), indent=2)
    print("patch-notes: %d versions, latest %s (%d messages)" % (len(index), index[0]["version"], index[0]["messages"]))


if __name__ == "__main__":
    main()
