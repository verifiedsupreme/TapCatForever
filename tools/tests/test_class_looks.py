# 1.6.0 test feedback: "the cats skins should be PER class". Each class's cat wears its own fur,
# pattern, skin and tap effect (cosmetic slots were already per class); since the next 1.6.0 change
# the cosmetics are owned per class cat too (tools/tests/test_class_cosmetics.py). Checks:
#   - an old save (one shared look): after the update every class's cat wears that look
#   - a new skin on the Mage stays on the Mage; the Warrior keeps its own; back and forth; reload
#   - fur and tap effect per class, IsEquipped / Equip / Unequip for another class
#   - the party message and the previews (Shop try on, Gear page, Casino) use the current class's look
#   - set pieces and the racial slot follow the class too (loadouts), a racial piece goes on the cat that bought it
#   - a new character's cats start in their own class fur
# Run on its own:  python3 tools/tests/test_class_looks.py [seed]
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import test_deathroll as TD

def ck(c, m):
    if not c: raise AssertionError("class looks: " + m)

def login(load_addon, name, db=None):
    lua = load_addon(login=False)
    lua.execute(TD.CLIENT)
    lua.execute('_charName = "%s"' % name)
    if db: lua.execute("TapCatForeverDB = loadstring(%r)()" % ("return " + db))
    lua.execute('_fire("ADDON_LOADED", "TapCatForever"); _fire("PLAYER_LOGIN")')
    return lua

def check(seed, load_addon):
    # --- an old save: one look shared by every cat (no db.looks)
    A = login(load_addon, "Lookcat")
    A.execute('''
      local T = TapCatForever
      T:SetClass("MAGE")
      for _, id in ipairs({ "skin_frostsaber", "skin_lion", "fur_snow", "tap_puff" }) do T.db.owned[id] = 1 end
      T:Equip(T.ITEMS.skin_frostsaber); T:Equip(T.ITEMS.fur_snow)
      -- as a 1.5.x save looked: no per-class looks yet, one collection for the character
      TapCatForever.charData.looks = nil
      local all = {}
      for _, cd in pairs(T.db.classData) do for id, n in pairs(cd.owned or {}) do all[id] = n end; cd.owned = nil end
      TapCatForever.charData.owned = all
    ''')
    old = A.eval("_dbString()")
    B = login(load_addon, "Lookcat", old)
    E = lambda e: B.eval(e)
    X = lambda c: B.execute(c)
    for cls in ("MAGE", "WARRIOR", "PRIEST", "DRUID"):
        X('TapCatForever:SetClass("%s")' % cls)
        ck(E("TapCatForever:GetAppearance().skin.id") == "skin_frostsaber" and E("TapCatForever:GetAppearance().fur.id") == "fur_snow",
           "migration: the %s cat wears the look worn before" % cls)

    # --- a new skin on the Mage stays on the Mage
    X('TapCatForever:SetClass("MAGE"); TapCatForever:Equip(TapCatForever.ITEMS.skin_lion)')
    ck(E("TapCatForever:GetAppearance().skin.id") == "skin_lion", "the Mage wears the lion skin")
    X('TapCatForever:SetClass("WARRIOR")')
    ck(E("TapCatForever:GetAppearance().skin.id") == "skin_frostsaber", "the Warrior keeps its own skin")
    ck(E("TapCatForever:GetAppearance('MAGE').skin.id") == "skin_lion", "the Mage's look read while playing the Warrior")
    ck(E("TapCatForever:IsEquipped(TapCatForever.ITEMS.skin_lion, 'MAGE')") and not E("TapCatForever:IsEquipped(TapCatForever.ITEMS.skin_lion)"),
       "IsEquipped per class")
    # (1.6.0: every cat of an old save owns what the character owned) the Warrior can wear the lion skin too
    X("TapCatForever:Equip(TapCatForever.ITEMS.skin_lion); TapCatForever:Unequip('skin')")
    ck(E("TapCatForever:GetAppearance().skin == nil") and E("TapCatForever:GetAppearance('MAGE').skin.id") == "skin_lion", "Unequip on the Warrior only")
    X("TapCatForever:Equip(TapCatForever.ITEMS.skin_frostsaber)")
    # fur and tap effect per class
    X("TapCatForever:Equip(TapCatForever.ITEMS.fur_ginger)")
    ck(E("TapCatForever:GetAppearance().fur.id") == "fur_ginger" and E("TapCatForever:GetAppearance('MAGE').fur.id") == "fur_snow", "fur per class")
    X("TapCatForever:Unequip('tap', 'MAGE')")
    ck(E("TapCatForever:GetAppearance('MAGE').tap == nil") and E("TapCatForever:GetAppearance().tap ~= nil"), "tap effect per class (Unequip for another class)")
    X("TapCatForever:Equip(TapCatForever.ITEMS.tap_puff, 'MAGE')")
    ck(E("TapCatForever:IsEquipped(TapCatForever.ITEMS.tap_puff, 'MAGE')"), "Equip for another class")
    # back and forth
    for _ in range(3):
        X('TapCatForever:SetClass("MAGE")'); ck(E("TapCatForever:GetAppearance().skin.id") == "skin_lion", "Mage again: lion")
        X('TapCatForever:SetClass("WARRIOR")'); ck(E("TapCatForever:GetAppearance().skin.id") == "skin_frostsaber", "Warrior again: frostsaber")

    # --- the party message is the current cat's look
    pw = E("TapCatForever:PartyPayload()")
    ck(pw.startswith("WARRIOR;") and ";skin_frostsaber;" in pw and ";fur_ginger;" in pw, "party message for the Warrior: %s" % pw)
    pm = E("TapCatForever:PartyPayload('MAGE')")
    ck(pm.startswith("MAGE;") and ";skin_lion;" in pm and ";fur_snow;" in pm, "party message for the Mage: %s" % pm)

    # --- previews follow the current class: Shop try on, Gear page, the screen cat, Casino
    ck(E("TapCatForever:GetAppearance(nil, TapCatForever.ITEMS.skin_lion).skin.id") == "skin_lion"
       and E("TapCatForever:GetAppearance(nil, TapCatForever.ITEMS.skin_lion).fur.id") == "fur_ginger", "try on: the Warrior's fur under the tried skin")
    X('''
      local T = TapCatForever
      T:CreateWindow(); T.window:Show(); T.window:Refresh()
      _skins = {}
      local orig = T.cat.ApplyAppearance
      T.cat.ApplyAppearance = function(self, look) _skins.hud = look.skin and look.skin.id; return orig(self, look) end
      if T.window.preview then
        local o2 = T.window.preview.ApplyAppearance
        T.window.preview.ApplyAppearance = function(self, look) _skins.preview = look.skin and look.skin.id; return o2(self, look) end
      end
      T:SetClass("MAGE"); T:RefreshAll(); T.window:Refresh()
    ''')
    ck(E("_skins.hud") == "skin_lion", "the screen cat puts on the Mage's skin: %s" % E("_skins.hud"))
    ck(E("_skins.preview") in (None, "skin_lion"), "the character pane cat follows: %s" % E("_skins.preview"))
    # the Casino's death roll scene draws your cat with the current class's look
    X('''
      _drRefresh = TapCatForever.UI.CasinoDeathRoll(CreateFrame("Frame", nil, UIParent), nil)
      local v = TapCatForever.DR.views[#TapCatForever.DR.views]
      _skins.casino = nil
      local o3 = v.L.cat.ApplyAppearance
      v.L.cat.ApplyAppearance = function(self, look) _skins.casino = look.skin and look.skin.id; return o3(self, look) end
      TapCatForever:SetClass("WARRIOR"); v.L.lookKey = nil; v:Refresh(true)
    ''')
    ck(E("_skins.casino") == "skin_frostsaber", "the Casino cat wears the Warrior's skin: %s" % E("_skins.casino"))

    # --- set pieces and the racial slot follow the class (cosmetic slots: loadouts)
    X('''
      local T = TapCatForever
      local set = T.COSMETIC_SETS[1]
      _piece = set and set.items[1]
      if _piece then T:SetClass("MAGE"); T.db.owned[_piece.id] = 1; T:Equip(_piece) end
    ''')
    if E("_piece ~= nil"):
        slot = E("_piece.slot")
        ck(E("TapCatForever:GetAppearance()[%r].id == _piece.id" % slot), "the Mage wears the set piece")
        X('TapCatForever:SetClass("WARRIOR")')
        ck(E("(TapCatForever:GetAppearance()[%r] or {}).id ~= _piece.id" % slot), "the Warrior doesn't")
    X('''
      local T = TapCatForever
      T.db.coins = 10000
      for _, cl in ipairs(T.CLASSES) do T:GetLoadout(cl.key).race = nil end
      _raceOk = T:BuyRaceAccessory()
    ''')
    if E("_raceOk"):
        # (1.6.0) bought for the cat being played (the Warrior): only it owns and wears it
        ck(E("TapCatForever:GetAppearance('WARRIOR').race ~= nil"), "the racial piece goes on the Warrior cat")
        for cls in ("MAGE", "ROGUE"):
            ck(E("TapCatForever:GetAppearance(%r).race == nil" % cls), "the %s cat doesn't get it" % cls)
        X("TapCatForever:Unequip('race', 'WARRIOR')")
        ck(E("TapCatForever:GetAppearance('WARRIOR').race == nil"), "the racial slot per class")

    # --- a reload keeps every cat's look
    X('TapCatForever:SetClass("WARRIOR")')
    C = login(load_addon, "Lookcat", B.eval("_dbString()"))
    ck(C.eval("TapCatForever:GetAppearance().skin.id") == "skin_frostsaber" and C.eval("TapCatForever:GetAppearance('MAGE').skin.id") == "skin_lion",
       "after a reload: Warrior frostsaber, Mage lion")
    C.execute('TapCatForever:SetClass("MAGE")')
    ck(C.eval("TapCatForever:GetAppearance().skin.id") == "skin_lion" and C.eval("TapCatForever:GetAppearance().fur.id") == "fur_snow", "the Mage after a reload")

    # --- a new character: each cat in its own class fur
    N = login(load_addon, "Freshcat")
    furs = {}
    for cls in ("WARRIOR", "MAGE", "ROGUE", "DRUID"):
        N.execute('TapCatForever:SetClass("%s")' % cls)
        furs[cls] = N.eval("TapCatForever:GetAppearance().fur.id")
        ck(furs[cls] == N.eval("TapCatForever.CLASS_BY_KEY[%r].fur" % cls), "a new %s cat in its class fur: %s" % (cls, furs[cls]))
    print("class looks section (old save: every cat keeps the worn look; skin, fur and tap effect per class; Equip and Unequip "
          "for another class; party message, try on, screen cat and Casino follow the class; set pieces and the racial slot; "
          "reload; new cats in their class fur): all checks passed")

if __name__ == "__main__":
    sys.path.insert(0, os.path.join(HERE, ".."))
    import test_harness
    check(int(sys.argv[1]) if len(sys.argv) > 1 else 1, test_harness.load_addon)
