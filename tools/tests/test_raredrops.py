# 1.7.1 rare drops list: every profession with rare drops says where they come from (Help guide and the
# guild view's rare finds line).

def check(seed, load_addon):
    lua = load_addon()
    r = lua.execute(r'''
      local T = TapCatForever
      local fails = {}
      local function ck(c, m) if not c then fails[#fails + 1] = m end end
      for _, f in ipairs({ "mining", "skinning", "cloth" }) do
        local t = T:RareDropText(f) or ""
        for _, rf in ipairs(T.RARE_FINDS[f]) do ck(t:find(rf.name, 1, true), f .. " names " .. rf.name) end
        ck(t:find(T.FAMILIES[f].ops[2][1], 1, true), f .. ": where (spot 2) " .. t)
        ck(t:find("1 in 250", 1, true), f .. ": how often")
      end
      local h = T:RareDropText("herbalism") or ""
      for _, rh in ipairs(T.RARE_HERBS) do ck(h:find(rh.name, 1, true) and h:find(T.RareSources(rh.key), 1, true), "herbalism: " .. rh.name .. " and its seeds") end
      local fi = T:RareDropText("fishing") or ""
      ck(fi:find("Mr. Pinchy", 1, true) and fi:find("Treasure", 1, true), "fishing: Mr. Pinchy and treasure")
      ck(T:RareDropText("cooking") == nil and T:RareDropText("firstaid") == nil, "no list where there are no rare drops")
      for _, s in ipairs({ T:RareDropText("cloth"), h, fi }) do ck(not s:find("!", 1, true), "no exclamation marks") end
      return table.concat(fails, "; ")
    ''')
    assert r == "", "rare drops: " + r
    print("rare drops section (gathering rare finds with their spots and odds, rare herbs with their seeds, Mr. Pinchy and treasure): all checks passed")
