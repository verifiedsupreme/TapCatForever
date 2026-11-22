"""Writes OUT_DIR/index.html showing every art preview in the folder (animated GIFs, sheets, the
skin ranking and proposal). Run it after the preview tools:
  python3 tools/set_preview.py tools/sets/<set>.py OUT     (sets_<key>.gif/.png/_pieces.png)
  python3 tools/fx_preview.py OUT                          (skin and cosmetic effects, racial slot, shoulders)
  python3 tools/skin_ranking.py OUT                        (skins_ranked.png, skins_proposal.md)
  python3 tools/preview_index.py OUT
"""
import glob, html, os, re, sys


def md_to_html(text):
    out, table, para = [], [], []
    def flush_para():
        if para: out.append("<p>%s</p>" % inline(" ".join(para))); para.clear()
    def flush_table():
        if table:
            rows = [r for r in table if not re.match(r"^\|[-| ]+\|$", r)]
            h = "".join("<th>%s</th>" % inline(c.strip()) for c in rows[0].strip("|").split("|"))
            b = "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % inline(c.strip()) for c in r.strip("|").split("|")) for r in rows[1:])
            out.append("<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>" % (h, b)); table.clear()
    for line in text.splitlines():
        if line.startswith("|"): flush_para(); table.append(line); continue
        flush_table()
        m = re.match(r"^(#+) (.*)", line)
        if m: flush_para(); n = len(m.group(1)) + 1; out.append("<h%d>%s</h%d>" % (n, inline(m.group(2)), n))
        elif line.startswith("- "): flush_para(); out.append("<ul><li>%s</li></ul>" % inline(line[2:]))
        elif not line.strip(): flush_para()
        else: para.append(line)
    flush_para(); flush_table()
    return "\n".join(out).replace("</ul>\n<ul>", "")


def inline(s):
    s = html.escape(s)
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", s))


def figure(src, caption, wide=False):
    return '<figure class="%s"><img src="%s" loading="lazy" alt="%s"><figcaption>%s</figcaption></figure>' % (
        "wide" if wide else "", html.escape(src), html.escape(caption), html.escape(caption))


def set_info():
    """key -> (name, [(piece name, word, boss)]) from the generated Sets/*.lua files"""
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
    info = {}
    toc = open(os.path.join(root, "TapCatForever.toc"), encoding="utf-8").read()
    files = [os.path.join(root, "Sets", m) for m in re.findall(r"^Sets\\(\S+\.lua)", toc, re.M)]   # game order
    for f in files + [f for f in sorted(glob.glob(os.path.join(root, "Sets", "*.lua"))) if f not in files]:
        src = open(f, encoding="utf-8").read()
        key, name = re.search(r'key = "([^"]+)"', src).group(1), re.search(r'\n  name = "([^"]+)"', src).group(1)
        pieces = re.findall(r'\n      name = "([^"]+)",.*?boss = "([^"]+)",\n      word = "([^"]+)"', src, re.S)
        info[key] = (name, [(n, w, b) for n, b, w in pieces])
    return info


def main(out):
    have = lambda f: os.path.exists(os.path.join(out, f))
    parts = []
    info = set_info()
    sets = sorted(glob.glob(os.path.join(out, "sets_*.gif")))
    sets = [g for g in sets if os.path.basename(g) != "sets_overview.gif"]
    order = list(info)
    sets.sort(key=lambda g: order.index(os.path.basename(g)[5:-4]) if os.path.basename(g)[5:-4] in order else 99)
    if have("sets_overview.gif"):
        parts.append("<h2>All cosmetic sets</h2><p>%d sets, 6 pieces each (helm, shoulders, chest, cape, weapon, aura). Each piece is guaranteed from one Adventure boss of its dungeon until you own it. Cosmetic only.</p><div class='grid'>%s</div>"
                     % (len(info), figure("sets_overview.gif", "Every set worn in full, as the game draws it", True)))
    if sets:
        parts.append("<h2>Cosmetic sets</h2><p>Each piece is guaranteed from one Adventure boss until you own it. Cosmetic only. Drawn with the game's own cat code; the paws tap now and then.</p>")
        for g in sets:
            key = os.path.basename(g)[5:-4]
            name, pieces = info.get(key, (key, []))
            parts.append("<h3>%s set</h3>" % html.escape(name))
            if pieces:
                parts.append("<table><thead><tr><th>Piece</th><th>Slot</th><th>Boss</th></tr></thead><tbody>%s</tbody></table>" % "".join(
                    "<tr><td>%s</td><td>%s</td><td>%s</td></tr>" % (html.escape(n), html.escape(w), html.escape(b)) for n, w, b in pieces))
            parts.append("<div class='grid'>")
            parts.append(figure(os.path.basename(g), "%s set, animated" % name))
            if have("sets_%s_pieces.png" % key): parts.append(figure("sets_%s_pieces.png" % key, "%s set: each piece and its boss" % name, True))
            parts.append("</div>")
    if have("skins_fx.gif") or glob.glob(os.path.join(out, "fx_*.gif")):
        parts.append("<h2>Effects on the expensive skins</h2><div class='grid'>")
        for g in sorted(glob.glob(os.path.join(out, "fx_*.gif"))):
            parts.append(figure(os.path.basename(g), os.path.basename(g)[3:-4].replace("skin_", "").replace("_", " ").title()))
        if have("skins_fx.gif"): parts.append(figure("skins_fx.gif", "Every skin with an effect", True))
        if have("cosmetics_fx.gif"): parts.append(figure("cosmetics_fx.gif", "Legendary cosmetics: their own sparkles, and a shine on the rest. Epic helms, chest pieces and shoulders: two small glints now and then", True))
        parts.append("</div>")
    if have("shoulders_sheet.png") or have("shoulders_layer.png"):
        parts.append("<h2>Shoulders</h2><div class='grid'>")
        for f, c in (("shoulders_sheet.png", "Every real gear shoulder drawing on the cat (43 icons, 960 items), each with a helm, chest and cape, and full outfits at the bottom"), ("shoulders_layer.png", "The shoulder layer with capes, chest pieces, hoods and big helms (tinted fallbacks by armour type, now only for an icon without its own drawing)")):
            if have(f): parts.append(figure(f, c, True))
        parts.append("</div>")
    if have("racial_slot.png"):
        parts.append("<h2>Racial accessory in its own slot</h2><div class='grid'>%s</div>" % figure("racial_slot.png", "Each racial accessory worn with another accessory", True))
    if have("skins_ranked.png"):
        parts.append("<h2>Skin ranking (proposal, not applied)</h2><div class='grid'>%s</div>" % figure("skins_ranked.png", "Every skin ranked by looks, with the proposed moves and prices", True))
    if have("skins_proposal.md"):
        parts.append("<section class='md'>%s</section>" % md_to_html(open(os.path.join(out, "skins_proposal.md")).read()))
    page = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>TapCatForever art previews</title><style>
:root { --bg: #1d1926; --panel: #27212f; --ink: #efe8f6; --muted: #b9adc8; --accent: #ffcf6e; }
body { margin: 0; padding: 16px; background: var(--bg); color: var(--ink); font: 15px/1.5 system-ui, sans-serif; }
h1 { color: var(--accent); margin: 4px 0 2px; } h2 { color: var(--accent); margin-top: 32px; border-bottom: 1px solid #3a3146; padding-bottom: 4px; }
.grid { display: flex; flex-wrap: wrap; gap: 14px; } figure { margin: 0; background: var(--panel); padding: 8px; border-radius: 8px; max-width: 100%; }
figure.wide { flex-basis: 100%; } figure img { max-width: 100%; height: auto; display: block; border-radius: 4px; }
figcaption { color: var(--muted); font-size: 13px; padding-top: 6px; }
table { border-collapse: collapse; margin: 10px 0; font-size: 14px; display: block; overflow-x: auto; }
th, td { border: 1px solid #3a3146; padding: 4px 8px; text-align: left; } th { background: #2f2839; } code { color: var(--accent); }
</style></head><body><h1>TapCatForever 1.6 art previews</h1><p style="color:var(--muted)">For approval before shipping. Drawn with the addon's own cartoon cat code outside the game.</p>
@@BODY@@</body></html>""".replace("@@BODY@@", "\n".join(parts))
    open(os.path.join(out, "index.html"), "w").write(page)
    print("wrote", os.path.join(out, "index.html"))


if __name__ == "__main__":
    main(sys.argv[1])
