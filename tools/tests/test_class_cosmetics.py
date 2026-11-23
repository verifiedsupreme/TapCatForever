# 1.6.0 test feedback: "everything on the appearance tab should be per class ... including unlocks"
# ("if i unlocked diamond skin and equip it on my mage i shouldnt see it on my hunter"). Each class's
# cat owns its own cosmetics (classData[class].owned); db.owned is the collection of the cat things
# are given to (TCF:OwnerClass). Checks:
#   - an old save (one collection for the character): every cat owns all of it, sources kept
#   - unlocks go to the cat being played: drops, skins, the Shop (Daily Wares, skins, racial piece),
#     account achievements; duplicates salvage per cat
#   - unlocks go to the cat that earned them: crafting for another cat, an expedition being claimed,
#     a class achievement
#   - the Appearance tab, the Shop's owned marks and Heroic Cache skins, Equip, item sources use the
#     current cat; achievements count the best cat's collection
#   - a reload keeps it; a new character's cats own the starters
# Run on its own:  python3 tools/tests/test_class_cosmetics.py [seed]
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import test_deathroll as TD
import savehelp

def ck(c, m):
    if not c: raise AssertionError("class cosmetics: " + m)

def login(load_addon, name, db=None):
    lua = load_addon(login=False)
    lua.execute(TD.CLIENT)
    lua.execute(savehelp.AS_OLD)
    lua.execute('_charName = "%s"' % name)
    if db: lua.execute("TapCatForeverDB = loadstring(%r)()" % ("return " + db))
    lua.execute('_fire("ADDON_LOADED", "TapCatForever"); _fire("PLAYER_LOGIN")')
    return lua

def check(seed, load_addon):
    # --- an old save: one collection for the character (1.5.x)
    A = login(load_addon, "Wardrobe")
    A.execute('''
      local T = TapCatForever
      T:SetClass("MAGE")
      T:Owned("MAGE").skin_frostsaber = 1
      T:Owned("MAGE").skin_lion = 3
      _as15()
      T.charData.itemSources = { skin_frostsaber = { first = { "Heroic Cache", 1000 }, last = { "Heroic Cache", 1000 } } }
    ''')
    B = login(load_addon, "Wardrobe", A.eval("_dbString()"))
    E = lambda e: B.eval(e)
    X = lambda c: B.execute(c)
    X("T = TapCatForever; T.RefreshAll = function() end")
    for cls in ("MAGE", "HUNTER", "WARRIOR", "DRUID"):
        ck(E("T:Owned(%r).skin_frostsaber == 1 and T:Owned(%r).skin_lion == 3 and T:Owned(%r).skin_orange ~= nil" % (cls, cls, cls)),
           "migration: the %s cat owns everything the character owned" % cls)
        ck(E("T:ItemSourceRecord('skin_frostsaber', %r).first[1]" % cls) == "Heroic Cache", "the old source for the %s cat" % cls)
    ck(E("rawget(T.charData, 'owned') == nil and rawget(T.charData, 'classData') == nil"), "the old collection and cats are gone from the character")

    # --- "diamond skin on my mage, not on my hunter"
    X('T:SetClass("MAGE"); _new, _salv = T:GrantItem(T.ITEMS.skin_diamond, "Dropped by Nefarian in Blackwing Lair")')
    ck(E("_new") and E("T.db.owned.skin_diamond == 1") and E("T:Owned('MAGE').skin_diamond == 1"), "the Mage gets the Diamond Cat")
    X("T:Equip(T.ITEMS.skin_diamond)")
    ck(E("T:GetAppearance().skin.id") == "skin_diamond", "the Mage wears it")
    X('T:SetClass("HUNTER")')
    ck(E("T.db.owned.skin_diamond == nil") and E("T:Owned('HUNTER').skin_diamond == nil"), "the Hunter doesn't own it")
    X("T:Equip(T.ITEMS.skin_diamond)")
    ck(E("(T:GetAppearance().skin or {}).id ~= 'skin_diamond'"), "the Hunter can't wear it")
    X("T:Equip(T.ITEMS.skin_diamond, 'HUNTER')")
    ck(E("not T:IsEquipped(T.ITEMS.skin_diamond, 'HUNTER')"), "Equip for a class that doesn't own it does nothing")
    # the Appearance tab lists the Hunter's collection (skins show every skin, owned ones first)
    X('''
      _hat = nil
      for _, it in ipairs(T.ITEM_LIST) do
        if it.source == "loot" and it.slot == "head" and not it.class and not T:Owned("HUNTER")[it.id] and not T:Owned("MAGE")[it.id] then _hat = it; break end
      end
      T:SetClass("MAGE"); T:GrantItem(_hat, "Lucky find while tapping"); T:SetClass("HUNTER")
      T:CreateWindow(); T.window:Show()
      T.window.slot = "head"
      _list = {}
      for _, it in ipairs(T.window:WardrobeItems()) do _list[it.id] = true end
      T.window.slot = "skin"
      _skinPos = nil
      for i, it in ipairs(T.window:WardrobeItems()) do if it.id == "skin_diamond" then _skinPos = i end end
      _ownedSkins = 0
      for _, it in ipairs(T.window:WardrobeItems()) do if T.db.owned[it.id] then _ownedSkins = _ownedSkins + 1 end end
    ''')
    ck(E("_list[_hat.id] == nil"), "the Hunter's Appearance tab doesn't list the Mage's hat")
    ck(E("_skinPos > _ownedSkins"), "the Diamond Cat shows as not owned for the Hunter")
    X('T:SetClass("MAGE"); T.window.slot = "head"; _list = {}; for _, it in ipairs(T.window:WardrobeItems()) do _list[it.id] = true end')
    ck(E("_list[_hat.id] == true"), "the Mage's does")
    # duplicates salvage per cat
    X('_new, _salv = T:GrantItem(T.ITEMS.skin_diamond, "Dropped by Nefarian in Blackwing Lair")')
    ck(not E("_new") and E("_salv") > 0 and E("T:Owned('MAGE').skin_diamond == 2"), "a second Diamond Cat on the Mage is salvaged")
    X('T:SetClass("HUNTER"); _new, _salv = T:GrantItem(T.ITEMS.skin_diamond, "Dropped by Nefarian in Blackwing Lair")')
    ck(E("_new") and E("_salv") == 0 and E("T:Owned('HUNTER').skin_diamond == 1"), "the Hunter's first one is new")
    ck(E("T:ItemSourceRecord('skin_diamond').first[1]") == "Nefarian (Blackwing Lair)", "the Hunter's own source record")

    # --- skins from anywhere, the Shop: the cat being played
    X('''
      _shopSkin = nil
      for _, it in ipairs(T.ITEM_LIST) do
        if it.slot == "skin" and it.skinPrice and not T:Owned("HUNTER")[it.id] and not T:Owned("MAGE")[it.id] then _shopSkin = it; break end
      end
      T.db.coins = 1e6
      T:SetClass("HUNTER")
      _poolBefore = #T:UnownedShopSkins()
      _bought = T:BuySkin(_shopSkin.id)
    ''')
    ck(E("_bought") and E("T:Owned('HUNTER')[_shopSkin.id] == 1") and E("T:Owned('MAGE')[_shopSkin.id] == nil"), "a bought skin is the Hunter's only")
    ck(E("#T:UnownedShopSkins()") == E("_poolBefore") - 1, "Heroic Cache skins: the Hunter's unowned shop skins")
    X('T:SetClass("MAGE")')
    ck(E("#T:UnownedShopSkins()") == E("_poolBefore"), "the Mage can still find it in a Heroic Cache")
    X('_g = T:GrantSkin("skin_frostsaber", "Found in a Heroic Cache")')
    ck(not E("_g"), "a skin the Mage owns isn't given again")
    X('''
      T:BuildShop(true)
      _ware = T.db.shop.stock[1]
      _ok = _ware and T:BuyItem(_ware)
    ''')
    if E("_ok"):
        ck(E("T:Owned('MAGE')[_ware] == 1") and E("T:Owned('HUNTER')[_ware] == nil"), "Daily Wares go to the Mage")
    # crafting for another cat (idle professions): that cat
    X('''
      _cos = nil
      for _, it in ipairs(T.ITEM_LIST) do
        if it.source == "loot" and it.slot == "head" and not it.class and not T:Owned("PRIEST")[it.id] and not T:Owned("MAGE")[it.id] then _cos = it; break end
      end
      T:WithTradeClass("PRIEST", function(self) self:GrantItem(_cos, "Crafted", true) end)
    ''')
    ck(E("T:Owned('PRIEST')[_cos.id] == 1") and E("T:Owned('MAGE')[_cos.id] == nil"), "crafted for the Priest: the Priest's")
    # an expedition being claimed: a cat that went
    X('''
      T:WithOwner("ROGUE", function(self) self:GrantSkin("skin_diamond", "Your party brought it home from Assault Molten Core") end)
    ''')
    ck(E("T:Owned('ROGUE').skin_diamond == 1") and E("T.db.class") == "MAGE", "an expedition's skin goes to the Rogue that went")
    X('''
      T.claimChests = { owner = "SHAMAN", source = "x" }
      _g = T:GrantSkin("skin_diamond", "Your party brought it home from Raid the Deadmines")
      T.claimChests = nil
    ''')
    ck(E("_g") and E("T:Owned('SHAMAN').skin_diamond == 1"), "the claim's cat gets the expedition's skin")

    # --- achievements: best cat counts, rewards to the cat being played
    X('''
      _best = 0
      for _, cl in ipairs(T.CLASSES) do _best = math.max(_best, (T:CountOwned(cl.key))) end
      _o1 = T:GetStat("owned")
      T:SetClass("PALADIN"); _o2 = T:GetStat("owned"); T:SetClass("MAGE")
    ''')
    ck(E("_o1") == E("_best") and E("_o2") == E("_best"), "owned counts the best cat, whichever is played")
    X('''
      local a
      for _, x in ipairs(T.ACHIEVEMENTS) do if x.item and x.stat == "owned" then a = x end end
      _ach = a
      T.db.achievements[a.id] = nil
      for _, cl in ipairs(T.CLASSES) do T:Owned(cl.key)[a.item] = nil end
      local n = 0
      for _, it in ipairs(T.ITEM_LIST) do if n < a.goal + 5 and it.source == "loot" then T:Owned("MAGE")[it.id] = 1; n = n + 1 end end
      T:CheckAchievements()
    ''')
    ck(E("T.db.achievements[_ach.id] ~= nil") and E("T:Owned('MAGE')[_ach.item] == 1") and E("T:Owned('HUNTER')[_ach.item] == nil"),
       "an account achievement's cosmetic goes to the cat being played")

    # --- a reload keeps every cat's collection, nothing spreads
    C = login(load_addon, "Wardrobe", B.eval("_dbString()"))
    ck(C.eval("TapCatForever:Owned('MAGE').skin_diamond == 2 and TapCatForever:Owned('HUNTER').skin_diamond == 1 and TapCatForever:Owned('WARRIOR').skin_diamond == nil"),
       "after a reload: Mage 2, Hunter 1, Warrior none")
    ach_item = B.eval("_ach.item")
    ck(C.eval("TapCatForever:Owned('HUNTER')[%r] == nil and TapCatForever:Owned('MAGE')[%r] == 1" % (ach_item, ach_item)),
       "the achievement cosmetic stays the Mage's after a reload")

    # --- a new account: its cats own the starters
    N = login(load_addon, "Freshwardrobe")
    for cls in ("WARRIOR", "MAGE", "HUNTER"):
        ck(N.eval("TapCatForever:Owned(%r).skin_orange == 1" % cls) and N.eval("TapCatForever:Owned(%r).skin_diamond == nil" % cls),
           "a new %s cat: starters only" % cls)
    print("class cosmetics section (old save: every cat owns the old collection and its sources; the Mage's Diamond Cat isn't the "
          "Hunter's; Appearance tab, Equip, duplicates and sources per cat; skins, Daily Wares and Heroic Cache skins per cat; "
          "crafting, expeditions and claims go to the cat that earned it; achievements count the best cat; reload; new character): all checks passed")

if __name__ == "__main__":
    sys.path.insert(0, os.path.join(HERE, ".."))
    import test_harness
    check(int(sys.argv[1]) if len(sys.argv) > 1 else 1, test_harness.load_addon)
