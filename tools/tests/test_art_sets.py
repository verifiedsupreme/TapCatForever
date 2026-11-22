# 1.6 art, wiring: every cosmetic set in the TOC (Molten Core and the ten later dungeons), their
# bosses in TCF.BOSS_COSMETICS (exact Adventure boss names), the set lines in the Compendium, the
# animation budget with a whole set worn, and real gear shoulders (one drawing per shoulder icon)
# on the cat and on the Gear page's cat.
import glob, os, re

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")

# set key -> dungeon (Adventure tier key) and the boss that gives the helm (its final boss)
SETS = {
    "mc": "Ragnaros", "sm": "High Inquisitor Whitemane", "uld": "Archaedas", "zf": "Chief Ukorz Sandscalp",
    "mara": "Princess Theradras", "st": "Shade of Eranikus", "brd": "Emperor Dagran Thaurissan",
    "brs": "General Drakkisath", "dim": "Immol'thar", "scholo": "Darkmaster Gandling", "strat": "Baron Rivendare",
}


def check(seed, load_addon):
    # every generated set file is loaded by the TOC
    toc = open(os.path.join(ROOT, "TapCatForever.toc"), encoding="utf-8").read()
    listed = set(re.findall(r"^Sets\\(\S+\.lua)", toc, re.M))
    files = set(os.path.basename(f) for f in glob.glob(os.path.join(ROOT, "Sets", "*.lua")))
    assert files and files == listed, "art sets section: TOC lists %s, Sets/ has %s" % (sorted(listed), sorted(files))
    srcs = set(os.path.basename(f)[:-3] for f in glob.glob(os.path.join(ROOT, "tools", "sets", "*.py")))
    assert len(srcs) == len(files), "art sets section: one tools/sets/*.py per Sets/*.lua (%d, %d)" % (len(srcs), len(files))

    lua = load_addon()
    lua.execute("math.randomseed(%d)" % seed)
    want = "{" + ",".join('["%s"]="%s"' % (k, v.replace('"', '\\"')) for k, v in SETS.items()) + "}"
    r = lua.execute(r'''
      local T = TapCatForever
      local WANT = ''' + want + r'''
      local fails = {}
      local function ck(ok, msg) if not ok then fails[#fails + 1] = msg end end
      local db, cat = T.db, T.cat
      for _, f in ipairs(cat.vframes) do
        f.CreateMaskTexture = function(self, ...) local m = self:CreateTexture(...); m.isMask = true; return m end
      end
      local function shownAnimTex(c)
        local n = 0
        for _, list in pairs(c.anim and c.anim.tex or {}) do for _, t in ipairs(list) do if t:IsShown() then n = n + 1 end end end
        return n
      end
      local tiers = {}
      for _, t in ipairs(T.TIERS) do tiers[t.key] = t end

      -- 1. every set: 11 of them, 6 pieces in 6 slots from 6 different bosses of its own dungeon
      local nSets, ids, names, bossesSeen = 0, {}, {}, {}
      for key, finalBoss in pairs(WANT) do
        local def = T.COSMETIC_SET_BY_KEY[key]
        ck(def, "set loaded: " .. key)
        if def then
          nSets = nSets + 1
          local t = tiers[def.zone]
          ck(t and def.zone == key, key .. ": its dungeon is the Adventure zone " .. key)
          ck(t and t.bosses[#t.bosses][1] == finalBoss, key .. ": final boss is " .. finalBoss)
          ck(#def.items == 6, key .. ": 6 pieces")
          local slots = {}
          for _, it in ipairs(def.items) do
            slots[it.slot] = true
            ck(not ids[it.id], "unique item id " .. it.id); ids[it.id] = true
            ck(not names[it.name], "unique item name " .. it.name); names[it.name] = true
            ck(it.source == "set" and it.set == key, key .. ": " .. it.id .. " is a set piece")
            ck(not bossesSeen[it.boss], "a boss gives one set piece: " .. tostring(it.boss)); bossesSeen[it.boss or "?"] = true
            if it.slot == "head" then ck(it.boss == finalBoss, key .. ": the helm comes from the final boss") end
            -- the hook Adventure reads: the exact boss display name lists this piece
            local hit = false
            for _, id in ipairs(T.BOSS_COSMETICS[it.boss] or {}) do if id == it.id then hit = true end end
            ck(hit, key .. ": TCF.BOSS_COSMETICS[" .. tostring(it.boss) .. "] lists " .. it.id)
            local inZone = false
            for _, b in ipairs(t and t.bosses or {}) do if b[1] == it.boss then inZone = true end end
            ck(inZone, key .. ": " .. tostring(it.boss) .. " is a boss of " .. key)
            -- Compendium and tooltips: where it drops, set progress, cosmetic only, plain English
            local how = table.concat(T:HowToGet(it), " | ")
            ck(how:find("Adventure: " .. it.boss .. " in " .. t.name .. " always drops it until you own it", 1, true), "how to get " .. it.id .. ": " .. how)
            ck(how:find(def.name .. " set (", 1, true) and how:find("cosmetic only", 1, true), "set line for " .. it.id .. ": " .. how)
            ck(not how:find("!", 1, true) and not it.name:find("!", 1, true), "no exclamation marks: " .. it.id)
            ck(T.SLOT_BY_KEY[it.slot], key .. ": real slot " .. it.slot)
            ck(T.Icon and T.Icon(it.icon), key .. ": icon for " .. it.id)
          end
          for _, s in ipairs({ "head", "shoulder", "chest", "back", "main", "effect" }) do ck(slots[s], key .. " has a " .. s .. " piece") end
        end
      end
      ck(nSets == 11 and #T.COSMETIC_SETS == 11, "11 sets: " .. nSets .. " / " .. #T.COSMETIC_SETS)
      local nBoss = 0
      for b, list in pairs(T.BOSS_COSMETICS) do nBoss = nBoss + 1; ck(#list >= 1, "boss list not empty: " .. b) end
      ck(nBoss == 66, "66 bosses give a set piece: " .. nBoss)

      -- 2. progress counts owned pieces, and the line marks them
      local mc = T.COSMETIC_SET_BY_KEY.mc
      local have, total = T:CosmeticSetProgress("dim")
      ck(have == 0 and total == 6, "Dire Maul set starts at 0/6")
      local dim = T.COSMETIC_SET_BY_KEY.dim
      db.owned[dim.items[1].id] = 1; db.owned[dim.items[2].id] = 1
      have = T:CosmeticSetProgress("dim")
      ck(have == 2, "two owned pieces count: " .. have)
      local line = T:HowToGet(dim.items[3])[2] or ""
      ck(line:find("Dire Maul set (2/6)", 1, true), "progress in the set line: " .. line)

      -- 3. wearing each whole set: every layer runs, the paws lift, and it stays cheap
      local worst, worstKey = 0, ""
      for key in pairs(WANT) do
        local def = T.COSMETIC_SET_BY_KEY[key]
        for _, it in ipairs(def and def.items or {}) do db.owned[it.id] = 1; T:Equip(it) end
        local look = T:GetAppearance()
        ck(look.head and look.head.set == key and look.effect and look.effect.set == key, key .. ": whole set worn")
        local ok, err = pcall(function()
          cat:ApplyAppearance(look)
          for i = 1, 30 do _update(0.05) end
          cat:SetPaw("R", false); _update(0.05); cat:SetPaw("R", true); _update(0.05)
        end)
        ck(ok, key .. ": draws without errors: " .. tostring(err))
        local n = shownAnimTex(cat)
        if n > worst then worst, worstKey = n, key end
        ck(n <= 60, key .. ": a whole set shows at most 60 animated textures: " .. n)
        ck(cat.anim and #cat.anim.layers <= 24, key .. ": at most 24 layers: " .. (cat.anim and #cat.anim.layers or 0))
      end
      for _, s in ipairs({ "head", "shoulder", "chest", "back", "main", "effect" }) do T:Unequip(s) end

      -- 4. real gear shoulders: every shoulder icon has its own drawing, worn on the cat
      local icons, nItems, noArt = {}, 0, {}
      for _, g in ipairs(T.GEAR_LIST) do
        if g.slot == "SHOULDER" and g.icon then
          nItems = nItems + 1
          local k = g.icon:lower()
          if not icons[k] then
            icons[k] = g
            local e = T.VEC[k]
            if not (e and e[8] == "shoulder") then noArt[#noArt + 1] = k end
          end
        end
      end
      local nIcons = 0
      for _ in pairs(icons) do nIcons = nIcons + 1 end
      ck(#noArt == 0, "every shoulder icon has a drawing, missing: " .. table.concat(noArt, ", "))
      ck(nIcons >= 40, "shoulder icons: " .. nIcons)
      local sh
      for _, g in ipairs(T.GEAR_LIST) do
        if g.slot == "SHOULDER" and (T:GearTargetSlots(g, db.class) or {})[1] == "SHOULDER" and T.VEC[g.icon:lower()] then sh = g; break end
      end
      ck(sh, "a wearable shoulder item")
      if sh then
        local eq = T:GearEquipped()
        local old = eq.SHOULDER
        eq.SHOULDER = sh.id
        cat:ApplyAppearance(T:GetAppearance())
        ck(cat.vt.shoulder_f:IsShown() and cat.vt.shoulder_f.tex and cat.vt.shoulder_f.tex:find(T.VEC[sh.icon:lower()][1], 1, true),
          "the cat wears the icon's own pauldrons: " .. tostring(cat.vt.shoulder_f.tex))
        ck(not cat.vt.shoulder_a:IsShown(), "no tinted fallback under the drawing")
        -- the Gear page's cat (the paperdoll) shows them, also as a hover preview
        eq.SHOULDER = old
        if not T.window then T:ToggleWindow() end
        local win = T.window
        ck(win and win.preview, "the window's cat")
        if win and win.preview then
          T.UI.ShowTryOn(win, sh)
          ck(win.preview.vt.shoulder_f:IsShown(), "hovering a shoulder item shows it on the Gear page's cat")
          T.UI.HideTryOn(win)
          ck(old ~= nil or not win.preview.vt.shoulder_f:IsShown(), "and takes it off again")
        end
        local doll = false
        for _, s in ipairs(T.GEAR_SLOTS or {}) do if s.key == "SHOULDER" then doll = true end end
        ck(doll, "the paperdoll has a shoulder slot")
      end
      _G.__nShoulderIcons, _G.__nShoulderItems, _G.__worst = nIcons, nItems, worstKey .. " " .. worst
      return table.concat(fails, "\n")
    ''')
    if r:
        raise AssertionError("art sets section:\n" + r)
    g = lua.globals()
    print("art sets section (11 sets x 6 pieces, 66 bosses in BOSS_COSMETICS, Compendium set lines, budget, most textures: %s; %d shoulder icons with drawings for %d items, Gear page cat): all checks passed"
          % (g.__worst, g.__nShoulderIcons, g.__nShoulderItems))
