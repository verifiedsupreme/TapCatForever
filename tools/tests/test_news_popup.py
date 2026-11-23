# 1.6.0: the What's new pop-up. The first time the main window opens on 1.6.0, a small box over the
# middle of the window (not over the screen cat) shows six pictures of what is new with a few words
# each, one line saying multiplayer is still in the works, "Read the full patch notes" and Close.
# Once per account; brand-new players get the welcome tour instead; later versions keep the strip.
# Run on its own:  python3 tools/tests/test_news_popup.py [seed]
import os, sys, importlib.util
_here = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("test_winpane", os.path.join(_here, "test_winpane.py"))
_pane = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_pane)
RECORDER = _pane.RECORDER + r'''
  -- and their parent
  local cf = CreateFrame
  CreateFrame = function(kind, name, parent, ...)
    local f = cf(kind, name, parent, ...)
    f._parent = parent
    return f
  end
'''
ROOT = os.path.join(_here, "..", "..")
NOTE = "Multiplayer is still in the works: party death roll, rock paper scissors and the leaderboard may not work yet."
LABELS = ["Cat Casino", "Resize your window", "Animated dungeon sets", "Professions level like WoW", "Farm your favourite bosses", "Party expeditions"]

def ck(c, m):
    if not c: raise AssertionError("what's new pop-up: " + m)

def check(seed, load_addon):
    lua = load_addon()
    r = lua.execute(RECORDER + r'''
      local T = TapCatForever
      local out = { fails = {} }
      local function ckl(c, m) if not c then out.fails[#out.fails + 1] = m end end
      T.version = "1.6.0"
      local n = T:CurrentNews()
      ckl(n and n.version == "1.6.0" and T.NEWS_POPUPS["1.6.0"], "1.6.0 has a pop-up")
      T.db.newsSeen, T.db.newsShows = nil, nil
      T:CreateWindow()
      local win = T.window
      win:Show(); T:CheckNews()
      local p = TapCatForeverWhatsNew
      ckl(p and p:IsShown(), "it shows the first time the window opens")
      ckl(not (T.newsStrip and T.newsStrip:IsShown()), "no strip for 1.6.0")
      ckl(p and p._parent == win and _pt(p, "CENTER") and _pt(p, "CENTER")[2] == win and _pt(p, "CENTER")[3] == "CENTER", "centred over the window, a part of it")
      ckl(p.title:GetText() == "What's new in 1.6", "title: " .. tostring(p.title:GetText()))
      out.labels, out.pics = {}, {}
      for i, t in ipairs(p.tiles) do out.labels[i] = t.label:GetText(); out.pics[i] = t.pic.tex end
      out.note = p.note:GetText()
      out.more, out.done = p.more:GetText(), p.done:GetText()
      -- every word in it: no exclamation marks
      local all = {}
      for _, f in ipairs(_frames) do if f.kind == "FontString" and type(f.text) == "string" then all[#all + 1] = f.text end end
      out.bang = table.concat(all, " "):find("!", 1, true) ~= nil
      -- sized for the window: a little bigger in the wide windows, fits the compact one
      out.scaleFull = p:GetScale()
      win:SetCompact(true)
      out.scaleCompact, out.w = p:GetScale(), p._w
      win:SetCompact(false)
      -- seen once per account: remembered at once
      ckl(T.db.newsSeen == "1.6.0" and not T:NewsPending(), "remembered as seen")
      p.done.scripts.OnClick(p.done)
      ckl(not p:IsShown(), "Close closes it")
      win:Hide(); win:Show(); T:CheckNews()
      ckl(not p:IsShown(), "it doesn't come back")
      -- Read the full patch notes
      T:ShowNewsPopup(n)
      ckl(p:IsShown(), "shown again by hand for the next check")
      p.more.scripts.OnClick(p.more)
      ckl(not p:IsShown() and TapCatForeverPatchNotes and TapCatForeverPatchNotes:IsShown(), "Read the full patch notes opens them")
      local body = TapCatForeverPatchNotes.body:GetText()
      ckl(body:find("Version 1.6.0", 1, true) and body:find("Multiplayer is still in the works", 1, true), "the 1.6.0 notes, with the multiplayer line")
      TapCatForeverPatchNotes:Hide()
      -- a later version with a highlight keeps the strip
      table.insert(T.NEWS, 1, { version = "1.7.0", highlight = "Something new.", text = "- Something new." })
      T.version = "1.7.0"
      win:Hide(); win:Show(); T:CheckNews()
      ckl(T.newsStrip and T.newsStrip:IsShown() and not p:IsShown(), "1.7.0 shows the strip, not the pop-up")
      table.remove(T.NEWS, 1)
      T:MarkNewsSeen()
      return out
    ''')
    fails = [r.fails[k] for k in range(1, len(r.fails) + 1)]
    ck(not fails, "; ".join(fails))
    labels = [r.labels[k] for k in range(1, len(r.labels) + 1)]
    ck(labels == LABELS, "the six labels: %r" % labels)
    ck(all(2 <= len(l.split()) <= 5 for l in labels), "2 to 5 words each")
    pics = [r.pics[k] for k in range(1, len(r.pics) + 1)]
    for p in pics:
        rel = p.replace("Interface\\AddOns\\TapCatForever\\", "").replace("\\", "/") + ".tga"
        path = os.path.join(ROOT, rel)
        ck(rel.startswith("Art/news/") and os.path.exists(path), "picture %s" % rel)
        size = os.path.getsize(path)
        ck(size <= 110 * 1024, "%s is small: %d bytes" % (rel, size))
        from PIL import Image
        im = Image.open(path)
        ck(im.size == (256, 128), "%s is 256x128: %r" % (rel, im.size))
    ck(r.note == NOTE, "the multiplayer line: %s" % r.note)
    ck(r.more == "Read the full patch notes" and r.done == "Close", "the buttons: %s, %s" % (r.more, r.done))
    ck(not r.bang, "no exclamation marks")
    ck(r.scaleFull > 1 and r.scaleCompact == 1 and r.w * r.scaleCompact <= 420 - 8, "sized for the window: %s full, %s x %s compact" % (r.scaleFull, r.w, r.scaleCompact))
    # brand-new players: the welcome tour, no pop-up
    lua = load_addon(login=False)
    r = lua.execute(r'''
      local T = TapCatForever
      T.version = "1.6.0"
      _fire("ADDON_LOADED", "TapCatForever"); _fire("PLAYER_LOGIN")
      local new = not T.db.welcomed and (T.db.taps or 0) == 0
      T:CreateWindow(); T.window:Show(); T:CheckNews()
      return { new = new, shown = TapCatForeverWhatsNew ~= nil and TapCatForeverWhatsNew:IsShown() or false, pending = T:NewsPending() }
    ''')
    ck(r.new and not r.shown and not r.pending, "a brand-new player gets no pop-up (new %s, shown %s)" % (r.new, r.shown))
    print("what's new pop-up section (1.6.0: over the window, six pictures with 2-5 words, the multiplayer line, patch notes and Close, once per account, "
          "not for brand-new players, later versions keep the strip, %d tiles under 110 KB): all checks passed" % len(pics))

if __name__ == "__main__":
    sys.path.insert(0, os.path.join(_here, ".."))
    import test_harness
    check(int(sys.argv[1]) if len(sys.argv) > 1 else 1, test_harness.load_addon)
